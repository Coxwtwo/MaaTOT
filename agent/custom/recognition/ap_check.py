import re
import json
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context
from maa.pipeline import JRecognitionType, JOCR
from utils import logger

@AgentServer.custom_recognition("APCheck")
class APCheck(CustomRecognition):
    """
    APCheck 自定义识别类
    用于识别当前体力值并判断是否低于设定阈值。
    """
    def analyze(
        self, context: Context, argv: CustomRecognition.AnalyzeArg
    ) -> CustomRecognition.AnalyzeResult:
        """
        核心识别逻辑：
        通过 OCR 读取指定区域的体力数值，并与参数中的阈值进行比较。
        
        :param context: Maa 任务上下文，用于调用底层 OCR 接口
        :param argv: 包含当前截图 (argv.image) 和 Pipeline 定义的 ROI (argv.roi)
        :return: AnalyzeResult (若体力不足返回成功标记，否则返回 None)
        """
        
        logger.info("APCheck: 正在检查当前体力数值...")
        
        try:
            # 1. 坐标适配：确保 roi 格式为 [x, y, w, h] 列表，以兼容 run_recognition_direct 接口
            roi_list = [argv.roi.x, argv.roi.y, argv.roi.w, argv.roi.h] if hasattr(argv.roi, 'x') else list(argv.roi)
            
            # 2. 执行 OCR 识别：
            # 使用 run_recognition_direct 直接驱动 OCR 算法，规避对 Pipeline 命名节点的依赖，提高自定义脚本的稳健性
            res = context.run_recognition_direct(
                JRecognitionType.OCR,
                JOCR(roi=roi_list),
                argv.image
            )
            
            # 检查 OCR 是否成功返回了文本块
            if not res or not res.all_results:
                logger.warning(f"APCheck: 在区域 {roi_list} 内未识别到任何文本")
                return None
            
            # 3. 结果处理：将所有识别到的文本块拼接（应对不同字号导致的文本切分问题，如 "10" 和 "/160"）
            full_text = "".join([item.text for item in res.all_results])
            logger.info(f"APCheck: OCR 识别结果为 '{full_text}'")
            
            # 4. 数值解析：使用正则表达式提取第一个数字序列
            match = re.search(r"(\d+)", full_text)
            if not match:
                logger.warning(f"APCheck: 无法从文本 '{full_text}' 中解析出有效的体力数字")
                return None
                
            current_ap = int(match.group(1))
            
            # 5. 阈值读取：从节点参数 custom_recognition_param 中解析 target 阈值
            try:
                param_dict = json.loads(argv.custom_recognition_param)
            except (json.JSONDecodeError, TypeError):
                param_dict = {}
            ap_threshold = param_dict.get("ap_threshold", 0)
            
            # 6. 逻辑判定：
            # 如果当前体力小于设定值，则判定为“匹配成功” (Hit)
            if current_ap < ap_threshold:
                logger.info(f"APCheck: 体力不足 ({current_ap} < {ap_threshold}) -> 触发补给流程")
                # 返回一个有效的虚拟坐标盒，告知 Pipeline 该节点已“匹配成功”，从而触发后续的 next 链路
                return CustomRecognition.AnalyzeResult(box=[0, 0, 1, 1], detail={"ap": current_ap})
                
            # 如果体力充足，则判定为“匹配失败” (No Hit)
            # 这将促使 Pipeline 尝试 next 列表中的低优先级项（如 Click_取消 逻辑）
            logger.info(f"APCheck: 体力充足 ({current_ap} >= {ap_threshold})，跳过能量饮料补给动作")
            return None
            
        except Exception as e:
            logger.exception(f"APCheck: 运行过程中发生未知异常: {e}")
            return None

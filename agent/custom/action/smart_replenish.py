import json
import re
import time
import numpy as np
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.pipeline import JRecognitionType, JOCR, JTemplateMatch
from utils import logger

@AgentServer.custom_action("SmartReplenish")
class SmartReplenish(CustomAction):
    """
    SmartReplenish 智能补给决策动作。
    负责在补给弹窗内根据当前体力缺口和能量饮料库存，选择并饮用一瓶最合适的饮料。
    注意：该动作被设计为“单次执行模式”，即每次运行仅决策并饮用一瓶饮料。
    """
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        """
        核心决策逻辑：
        1. 识别当前数值；
        2. 寻找最优能量饮料；
        3. 执行单次饮用。
        
        :param context: Maa 任务上下文
        :param argv: 包含动作参数 (argv.custom_action_param)
        :return: RunResult (success=True 表示饮用成功，触发 Pipeline 的递归流转)
        """
        # ==================== 内置配置参数 ====================
        # 当前体力数值的 OCR 识别区域
        ACTIONPOINT_VALUE_ROI = [380, 339, 180, 80] 
        # 补给界面中饮料图标的整体搜索区域（锁定前两栏）
        DRINK_SEARCH_ROI = [54, 562, 444, 224] 
        
        # 能量饮料各组件相对于图标左上角的坐标偏移与尺寸 [dx, dy, w, h]
        # c_off: 库存数字区域, e_off: 保质期文字区域
        DRINK_CONFIGS = [
            {
                "id": "60",
                "name": "60能量饮料",
                "template": "Button/60体力饮料.png",
                "node": "Click_60体力饮料",
                "value": 60,
                "c_off": (101, 56, 16, 21),
                "e_off": (-4, -36, 91, 32)
            },
            {
                "id": "30",
                "name": "30能量饮料",
                "template": "Button/30体力饮料.png",
                "node": "Click_30体力饮料",
                "value": 30,
                "c_off": (59, 27, 69, 62),
                "e_off": (-16, -41, 79, 35)
            }
        ]
        # =====================================================

        try:
            # 1. 参数解析：获取由外部注入的体力目标阈值
            param_dict = json.loads(argv.custom_action_param)
            ap_threshold = param_dict.get("ap_threshold", 0)
        except (json.JSONDecodeError, TypeError):
            ap_threshold = 0
        
        logger.info(f"SmartReplenish: 正在执行补给决策 (目标: {ap_threshold})...")

        # 2. 图像捕获：显式等待并获取当前最新截图，确保感知的是最新 UI 状态
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        if img is None:
            logger.error("SmartReplenish: 无法获取截图，动作中断")
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

        # 3. 状态读数：OCR 识别当前体力数值
        res_ap = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(roi=ACTIONPOINT_VALUE_ROI),
            img
        )
        
        current_ap = 0
        if res_ap and res_ap.all_results:
            full_text = "".join([item.text for item in res_ap.all_results])
            match = re.search(r"(\d+)", full_text)
            if match:
                current_ap = int(match.group(1))

        # 计算当前体力缺口
        gap = ap_threshold - current_ap
        if gap <= 0:
            logger.info(f"SmartReplenish: 当前体力 {current_ap} 已达标，无需补给")
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

        logger.info(f"SmartReplenish: 当前体力 {current_ap}，缺口为 {gap}")

        # 4. 资源动态搜索：收集所有在界面上可见（有库存）的饮料及其保质期信息
        available_drinks = {}
        
        for cfg in DRINK_CONFIGS:
            # 使用模板匹配实时定位图标位置
            match_res = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=cfg["template"], threshold=0.7, roi=DRINK_SEARCH_ROI),
                img
            )
            
            # 若图标不存在，根据游戏机制判定为该饮料已耗尽 (0库存不显示)
            if not match_res or not match_res.hit:
                continue
            
            # 找到图标坐标
            box = match_res.best_result.box
            abs_x, abs_y, abs_w, abs_h = (box.x, box.y, box.w, box.h) if hasattr(box, 'x') else box
            
            # A. 识别保质期并计算权重 (小时级优先级高于天级)
            exp_roi = [abs_x + cfg["e_off"][0], abs_y + cfg["e_off"][1], cfg["e_off"][2], cfg["e_off"][3]]
            res_exp = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=exp_roi), img)
            exp_weight = 9999
            if res_exp and res_exp.all_results:
                exp_text = "".join([it.text for it in res_exp.all_results])
                m_hour = re.search(r"(\d+)\s*小时", exp_text)
                m_day = re.search(r"(\d+)\s*天", exp_text)
                if m_hour:
                    exp_weight = int(m_hour.group(1))
                elif m_day:
                    exp_weight = int(m_day.group(1)) * 24 + 100
            
            # B. 识别库存瓶数
            count_roi = [abs_x + cfg["c_off"][0], abs_y + cfg["c_off"][1], cfg["c_off"][2], cfg["c_off"][3]]
            res_count = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=count_roi), img)
            
            inventory = 1 # 默认有库存
            if res_count and res_count.all_results:
                m = re.search(r"(\d+)", "".join([it.text for it in res_count.all_results]))
                if m:
                    inventory = int(m.group(1))
                    logger.info(f"SmartReplenish: {cfg['name']} 识别库存为 {inventory}")
            
            if inventory > 0:
                # 记录位置信息以供后续动态 ROI 覆盖
                available_drinks[cfg["id"]] = {
                    **cfg, 
                    "exp": exp_weight, 
                    "pos": (abs_x, abs_y, abs_w, abs_h)
                }

        # 5. 最终补给决策逻辑：基于保质期绝对优先原则
        target = None
        s60 = available_drinks.get("60")
        s30 = available_drinks.get("30")
        
        if s60 and s30:
            if s60["exp"] < s30["exp"]:
                target = s60
            elif s60["exp"] > s30["exp"]:
                target = s30
            else:
                if gap >= 60: target = s60
                else: target = s30
        elif s60:
            target = s60
        elif s30:
            target = s30

        # 6. 执行动作或安全回退
        if target:
            logger.info(f"SmartReplenish: 选定 {target['name']} (保质期权重: {target['exp']})")
            
            # 关键优化：应用动态 ROI 覆盖，确保精准命中选定的图标
            ax, ay, aw, ah = target["pos"]
            dynamic_roi = [ax - 50, ay - 50, aw + 100, ah + 100]
            
            context.override_pipeline({
                target["node"]: {
                    "roi": dynamic_roi
                }
            })
            
            context.run_task(target["node"])
            time.sleep(2.0)
            return CustomAction.RunResult(success=True)
        else:
            logger.warning("SmartReplenish: 未找到任何可用能量饮料，执行自我禁用逻辑")
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

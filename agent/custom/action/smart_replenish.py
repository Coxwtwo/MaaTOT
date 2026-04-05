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
        try:
            # 1. 参数解析：获取由外部注入的体力目标阈值
            param_dict = json.loads(argv.custom_action_param)
            threshold = param_dict.get("threshold", 0)
        except (json.JSONDecodeError, TypeError):
            threshold = 0
        
        logger.info(f"SmartReplenish: 正在执行补给决策 (目标: {threshold})...")

        # 2. 图像捕获：显式等待并获取当前最新截图，确保感知的是最新 UI 状态
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        if img is None:
            logger.error("SmartReplenish: 无法获取截图，动作中断")
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

        # 3. 状态读数：OCR 识别当前体力数值
        STAMINA_VALUE_ROI = [380, 339, 180, 80] 
        res_stamina = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(roi=STAMINA_VALUE_ROI),
            img
        )
        
        current_stamina = 0
        if res_stamina and res_stamina.all_results:
            full_text = "".join([item.text for item in res_stamina.all_results])
            match = re.search(r"(\d+)", full_text)
            if match:
                current_stamina = int(match.group(1))

        # 计算当前体力缺口
        gap = threshold - current_stamina
        if gap <= 0:
            logger.info(f"SmartReplenish: 当前体力 {current_stamina} 已达标，无需补给")
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

        logger.info(f"SmartReplenish: 当前体力 {current_stamina}，缺口为 {gap}")

        # 4. 资源动态搜索：定义饮料配置与搜索区域
        DRINK_SEARCH_ROI = [54, 562, 444, 224] # 锁定前两栏区域
        
        # 配置药水的基础属性及库存数字相对于图标的相对偏移量
        drink_configs = [
            {
                "id": "60",
                "name": "60能量饮料",
                "template": "Button/60体力饮料.png",
                "node": "Click_60体力饮料",
                "value": 60,
                "count_offset_x": 101, "count_offset_y": 56, "count_w": 16, "count_h": 21
            },
            {
                "id": "30",
                "name": "30能量饮料",
                "template": "Button/30体力饮料.png",
                "node": "Click_30体力饮料",
                "value": 30,
                "count_offset_x": 59, "count_offset_y": 27, "count_w": 69, "count_h": 62
            }
        ]

        # 收集所有在界面上可见（有库存）的饮料
        available_drinks = {}
        
        for cfg in drink_configs:
            # 使用模板匹配实时定位图标位置
            match_res = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=cfg["template"], threshold=0.7, roi=DRINK_SEARCH_ROI),
                img
            )
            
            # 若图标不存在，根据游戏逻辑判定为该饮料已耗尽 (0库存不显示)
            if not match_res or not match_res.hit:
                continue
            
            # 基础库存假设：图标存在即至少有 1 瓶
            inventory = 1 
            
            # 尝试通过 OCR 获取精确的剩余瓶数
            box = match_res.best_result.box
            abs_x = (box.x if hasattr(box, 'x') else box[0])
            abs_y = (box.y if hasattr(box, 'y') else box[1])
            count_roi = [abs_x + cfg["count_offset_x"], abs_y + cfg["count_offset_y"], cfg["count_w"], cfg["count_h"]]
            
            res_count = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=count_roi), img)
            
            if res_count and res_count.all_results:
                m = re.search(r"(\d+)", "".join([it.text for it in res_count.all_results]))
                if m:
                    inventory = int(m.group(1))
                    logger.info(f"SmartReplenish: {cfg['name']} 识别库存为 {inventory}")
            
            if inventory > 0:
                available_drinks[cfg["id"]] = cfg

        # 5. 补给决策逻辑
        best_drink = None
        has_60 = "60" in available_drinks
        has_30 = "30" in available_drinks
        
        if has_60 and has_30:
            if gap >= 60:
                best_drink = available_drinks["60"]
            else:
                best_drink = available_drinks["30"]
        elif has_60:
            best_drink = available_drinks["60"]
        elif has_30:
            best_drink = available_drinks["30"]

        # 6. 执行动作或安全回退
        if best_drink:
            logger.info(f"SmartReplenish: 决定饮用一瓶 {best_drink['name']}")
            context.run_task(best_drink["node"])
            time.sleep(2.0)
            return CustomAction.RunResult(success=True)
        else:
            logger.warning("SmartReplenish: 未找到任何可用能量饮料，执行自我禁用回退逻辑")
            # 库存枯竭时，主动触发禁用节点，防止主任务重复进入检查循环
            context.run_task("Action_禁用体力检查")
            return CustomAction.RunResult(success=False)

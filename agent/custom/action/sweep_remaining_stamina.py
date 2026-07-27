import json
import re
import time
from pathlib import Path
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.pipeline import JRecognitionType, JOCR, JTemplateMatch
from utils import logger

# ─── 从 JSON 数据文件加载关卡列表（运行时加载，避免解析器栈溢出）───
_STAGE_DATA_PATH = Path(__file__).parent / "stage_list_data.json"
with open(_STAGE_DATA_PATH, "r", encoding="utf-8") as _f:
    STAGE_LIST = json.load(_f)

logger.debug(f"SweepRemainingStamina: 已加载 {len(STAGE_LIST)} 个异常关卡")

# 体力弹窗内数值 OCR 区域
AP_POPUP_ROI = [380, 339, 180, 80]
# 主界面体力图标模板匹配区域
STAMINA_ICON_ROI = [655, 1055, 40, 40]
# 取消按钮大致区域（关闭弹窗）
CANCEL_CLICK = (420, 1080)


@AgentServer.custom_action("SweepRemainingStamina")
class SweepRemainingStamina(CustomAction):
    """
    消耗剩余体力：从最新章到最旧章遍历所有异常副本关卡，
    跳过已刷取（0剩余次数）的关卡，优先3次回退到1次，
    直到体力低于配置的最低阈值。

    custom_action_param:
    {
        "stage_index": 当前关卡索引（初始0）,
        "min_ap": 最低体力阈值（默认15）
    }
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        try:
            params = json.loads(argv.custom_action_param)
        except (json.JSONDecodeError, TypeError):
            params = {}

        stage_index = params.get("stage_index", 0)
        min_ap = params.get("min_ap", 15)
        total = len(STAGE_LIST)

        # 首次调用
        if stage_index == 0:
            logger.info(f"Sweep: 开始扫荡（共 {total} 关，阈值 {min_ap}AP）")

        # 全部完成
        if stage_index >= total:
            logger.info(f"Sweep: 全部 {total} 关遍历完毕")
            self._finish(context)
            return CustomAction.RunResult(success=True)

        # 检查体力
        ap = self._read_stamina_direct(context)
        if ap > 0 and ap < min_ap:
            logger.info(f"Sweep: 体力 {ap} < {min_ap}，停止")
            self._finish(context)
            return CustomAction.RunResult(success=True)

        # 处理当前关卡
        stage = STAGE_LIST[stage_index]
        logger.info(f"Sweep [{stage_index + 1}/{total}]: {stage['chapter']} {stage['stage']} (AP:{ap})")
        self._override_stage(context, stage, min_ap)
        context.run_task("异常副本")

        # 前进到下一关
        stage_index += 1
        context.override_pipeline({
            "Action_SweepRemainingStamina": {
                "custom_action_param": {
                    "stage_index": stage_index,
                    "min_ap": min_ap,
                },
                "enabled": True,
            }
        })

        return CustomAction.RunResult(success=True)

    def _finish(self, context):
        context.override_pipeline({
            "Action_SweepRemainingStamina": {"enabled": False}
        })
        context.run_task("返回主界面")

    def _read_stamina_direct(self, context):
        """
        直接通过模板匹配 + 点击 + OCR 读取体力值。
        不依赖 pipeline 节点，避免触发副作用链。
        """
        # 截图当前画面
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        if img is None:
            logger.warning("Sweep: 无法获取截图")
            return 0

        # 模板匹配找到体力图标
        match_res = context.run_recognition_direct(
            JRecognitionType.TemplateMatch,
            JTemplateMatch(
                template="Button/主界面体力.png",
                threshold=0.6,
                roi=STAMINA_ICON_ROI,
            ),
            img,
        )

        if match_res and match_res.hit:
            # 点击体力图标打开弹窗
            box = match_res.best_result.box
            if hasattr(box, "x"):
                cx = box.x + box.w // 2
                cy = box.y + box.h // 2
            else:
                cx = box[0] + box[2] // 2
                cy = box[1] + box[3] // 2
            context.tasker.controller.post_click(cx, cy).wait()
            time.sleep(1.5)

        # 截取弹窗画面
        context.tasker.controller.post_screencap().wait()
        img_popup = context.tasker.controller.cached_image
        if img_popup is None:
            return 0

        # OCR 读取体力数值
        res = context.run_recognition_direct(
            JRecognitionType.OCR,
            JOCR(roi=AP_POPUP_ROI),
            img_popup,
        )

        # 关闭弹窗
        context.tasker.controller.post_click(
            CANCEL_CLICK[0], CANCEL_CLICK[1]
        ).wait()
        time.sleep(0.5)

        if res and res.all_results:
            full_text = "".join([item.text for item in res.all_results])
            match = re.search(r"(\d+)", full_text)
            if match:
                ap = int(match.group(1))
                logger.debug(f"Sweep: OCR 读取体力 = {ap}")
                return ap

        logger.debug("Sweep: OCR 未能读取体力数值")
        return 0

    def _override_stage(self, context, stage, min_ap):
        """动态设置导航参数并确保体力检查不被永久禁用。"""
        override = {
            # 恢复体力检查（前一次异常副本运行可能禁用了它）
            "体力检查": {"enabled": True},
            # 关卡导航
            "Click_选择主线篇章": {"expected": stage["chapter"]},
            "Click_进入异常关卡": {"expected": stage["stage"]},
            # 优先游戏默认 max (3次)，回退到1次
            "Flag_复盘确认弹窗": {
                "next": [
                    "Click_复盘3次确定",
                    "Click_复盘1次确定",
                    "Flag_复盘次数最小",
                    "[JumpBack]Click_复盘次数减号亮",
                ]
            },
            # 体力不足时跳过能量饮料，直接取消
            "Flag_体力判断": {
                "custom_recognition_param": {"ap_threshold": min_ap},
                "next": ["Action_禁用体力检查"],
            },
        }

        # 关卡定位：OCR 或 TemplateMatch
        ep = stage["ep_override"]
        if "expected" in ep:
            override["Click_进入异常副本"] = {"expected": ep["expected"]}
        else:
            override["Click_进入异常副本"] = {
                "recognition": "TemplateMatch",
                "template": ep["template"],
                "threshold": ep.get("threshold", 0.93),
            }

        # 可选的列表边界标记
        if "list_bottom" in stage:
            override["Flag_异常关卡列表最下端"] = {
                "expected": stage["list_bottom"]
            }
        if "list_top" in stage:
            override["Flag_异常关卡列表最上端"] = {
                "expected": stage["list_top"]
            }

        context.override_pipeline(override)

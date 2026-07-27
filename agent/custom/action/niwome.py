"""
你我之间（Niwome）日常任务清理 - 自定义动作。

顺序: 进入 → ①记录心情 → ②准备物品 → ③回应动态 → ④完成打卡 → 退出
配置: config/niwome_config.json
所有操作 OCR 优先 + 坐标兜底。
"""

import json
import time
from pathlib import Path
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from maa.pipeline import JRecognitionType, JOCR, JTemplateMatch
from utils import logger

# ─── 等待时间 ───
W_SHORT = 1.0
W_CLICK = 2.0
W_PAGE = 3.0

# ─── 坐标常量（兜底用）───
POS_TOPRIGHT = (660, 55)   # 右上角按钮
# ─── ROI 常量 ───
ROI_TABS = [0, 100, 720, 200]
ROI_MID = [0, 200, 720, 600]
ROI_BOTTOM = [0, 600, 720, 600]
ROI_FULL = [0, 0, 720, 1280]

@AgentServer.custom_action("Niwome")
class Niwome(CustomAction):

    def _load_config(self):
        cfg_path = Path("config/niwome_config.json")
        defaults = {
            "character": "夏彦",
            "task_mood": True,
            "task_item": True,
            "task_checkin": True,
            "task_respond": True,
        }
        if cfg_path.exists():
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
            except Exception:
                logger.warning("Niwome: 读取配置失败")
        return defaults

    def _set_step(self, context, step):
        """存储下一步，保持节点启用让 pipeline 循环回来。"""
        context.override_pipeline({
            "Action_Niwome": {
                "custom_action_param": {"step": step},
                "enabled": True,
            }
        })

    def _finish(self, context):
        """禁用节点，pipeline 走到停止任务。"""
        context.override_pipeline({
            "Action_Niwome": {"enabled": False}
        })

    def run(self, context, argv):
        cfg = self._load_config()
        character = cfg["character"]

        try:
            params = json.loads(argv.custom_action_param)
        except (json.JSONDecodeError, TypeError):
            params = {}
        step = params.get("step", "init")

        tasks = [
            ("mood", cfg["task_mood"]),
            ("item", cfg["task_item"]),
            ("respond", cfg["task_respond"]),
            ("checkin", cfg["task_checkin"]),
        ]

        try:
            if step == "init":
                n = sum(v for _, v in tasks)
                logger.info(f"===== 你我之间 {n}/4 =====")
                self._click_phone_icon(context)
                if not self._enter_niwome(context):
                    self._exit_to_main(context)
                    self._finish(context)
                    return CustomAction.RunResult(success=False)
                self._skip_signin(context)
                # 找第一个启用的任务
                for name, enabled in tasks:
                    if enabled:
                        self._set_step(context, name)
                        return CustomAction.RunResult(success=True)
                self._set_step(context, "exit")
                return CustomAction.RunResult(success=True)

            elif step == "mood":
                self._task_mood(context)
                self._wait_homepage(context)

            elif step == "item":
                self._task_item(context, character)
                self._wait_homepage(context)

            elif step == "respond":
                self._task_respond(context)
                self._wait_homepage(context)

            elif step == "checkin":
                self._task_checkin(context)
                time.sleep(W_CLICK)

            elif step == "exit":
                self._exit_to_main(context)
                self._finish(context)
                logger.info("===== 你我之间完成 =====")
                return CustomAction.RunResult(success=True)

            # 找下一个启用的任务
            found_current = False
            for name, enabled in tasks:
                if found_current and enabled:
                    self._set_step(context, name)
                    return CustomAction.RunResult(success=True)
                if name == step:
                    found_current = True
            # 没有更多 → 退出
            self._set_step(context, "exit")
            return CustomAction.RunResult(success=True)

        except Exception as e:
            logger.exception(f"Niwome [{step}]: {e}")
            self._exit_to_main(context)
            self._finish(context)
            return CustomAction.RunResult(success=False)

    # ═══════ 工具方法 ═══════

    def _click(self, context, xy):
        context.tasker.controller.post_click(xy[0], xy[1]).wait()

    def _ocr_find(self, context, keywords, roi=None):
        """OCR 找关键词，返回命中的 box 或 None。"""
        r = roi or ROI_FULL
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        res = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=r), img)
        if res and res.all_results:
            for item in res.all_results:
                text = item.text.replace(" ", "")
                for kw in keywords:
                    if kw in text:
                        box = item.box
                        return (
                            (box.x, box.y, box.w, box.h)
                            if hasattr(box, "x")
                            else (box[0], box[1], box[2], box[3])
                        ), text
        return None, ""

    def _ocr_click(self, context, keywords, roi=None, label=""):
        """OCR 找关键词并点击。"""
        box, text = self._ocr_find(context, keywords, roi)
        if box:
            cx, cy = box[0] + box[2] // 2, box[1] + box[3] // 2
            self._click(context, (cx, cy))
            time.sleep(W_CLICK)
            return True
        return False

    def _ocr_click_exact(self, context, keywords, label=""):
        """OCR 精确匹配（text == kw）。"""
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        res = context.run_recognition_direct(JRecognitionType.OCR, JOCR(roi=ROI_FULL), img)
        if res and res.all_results:
            for item in res.all_results:
                text = item.text.replace(" ", "")
                for kw in keywords:
                    if text == kw:
                        box = item.box
                        x, y, w, h = (box.x, box.y, box.w, box.h) if hasattr(box, "x") else box
                        self._click(context, (x + w // 2, y + h // 2))
                        time.sleep(W_CLICK)
                        return True
        return False

    def _ocr_click_above(self, context, keywords, offset_y=-40, roi=None, label=""):
        """OCR 找关键词，点击文字上方 offset_y 处。"""
        box, text = self._ocr_find(context, keywords, roi)
        if box:
            cx, cy = box[0] + box[2] // 2, box[1] + offset_y
            self._click(context, (cx, cy))
            time.sleep(W_CLICK)
            return True
        return False

    def _go_back(self, context):
        """模拟器返回键（Shell pipeline）。"""
        context.run_task("Click_AndroidBack")
        time.sleep(W_CLICK)

    def _wait_homepage(self, context, max_retry=5):
        """确认回到你我之间首页。"""
        for _ in range(max_retry):
            if self._ocr_find(context, ["此刻", "此时", "最新动态", "本次外出", "下次外出"], roi=[0, 0, 720, 800])[0]:
                return
            self._go_back(context)

    def _exit_to_main(self, context):
        self._go_back(context)

    # ═══════ 进入 ═══════

    def _click_phone_icon(self, context):
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        for tmpl in [
            "好感/手机.png",
            "好感/手机_你我之间夏彦.png",
            "好感/手机_你我之间左然.png",
            "好感/手机_你我之间莫弈.png",
            "好感/手机_你我之间陆景和.png",
        ]:
            match = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=tmpl, threshold=0.7, roi=[45, 1005, 50, 50]),
                img,
            )
            if match and match.hit:
                box = match.best_result.box
                cx = (box.x + box.w // 2) if hasattr(box, "x") else (box[0] + box[2] // 2)
                cy = (box.y + box.h // 2) if hasattr(box, "y") else (box[1] + box[3] // 2)
                self._click(context, (cx, cy))
                time.sleep(W_CLICK)
                return
        self._click(context, (70, 1030))
        time.sleep(W_CLICK)

    def _enter_niwome(self, context):
        time.sleep(W_CLICK)
        LEFT_MID = [50, 200, 350, 600]
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image

        for tmpl in ["niwome/爱心图标.png"]:
            match = context.run_recognition_direct(
                JRecognitionType.TemplateMatch,
                JTemplateMatch(template=tmpl, threshold=0.6, roi=LEFT_MID),
                img,
            )
            if match and match.hit:
                box = match.best_result.box
                cx = (box.x + box.w // 2) if hasattr(box, "x") else (box[0] + box[2] // 2)
                cy = (box.y + box.h // 2) if hasattr(box, "y") else (box[1] + box[3] // 2)
                self._click(context, (cx, cy))
                time.sleep(W_PAGE)
                return True

        if self._ocr_click(context, ["你我", "之间"], roi=LEFT_MID, label="你我之间"):
            return True

        self._click(context, (300, 500))
        time.sleep(W_PAGE)
        return True

    def _skip_signin(self, context):
        time.sleep(W_CLICK)
        for _ in range(10):
            self._click(context, (360, 1100))
            time.sleep(W_SHORT)

    # ═══════ ① 记录心情 ═══════

    def _task_mood(self, context):
        """①记录心情：此时此刻 → 右上角 → 记录心情 → 发布 → 返回"""
        if not self._ocr_click(context, ["此刻", "此时"], label="此时此刻"):
            self._click(context, (120, 150))
            time.sleep(W_CLICK)
        self._click(context, POS_TOPRIGHT)
        time.sleep(W_CLICK)
        if self._ocr_click(context, ["记录心情", "分享见闻"], label="心情选项"):
            self._ocr_click_exact(context, ["发布"], label="发布")
        else:
            time.sleep(W_SHORT)
            if self._ocr_click(context, ["记录心情", "分享见闻"], roi=ROI_MID, label="心情选项(retry)"):
                self._ocr_click_exact(context, ["发布"], label="发布")
        self._go_back(context)
        logger.info("Niwome ①: 完成")

    # ═══════ ② 准备物品 ═══════

    def _task_item(self, context, character):
        """②准备物品：下次外出 → 伞上方 → 确认选择/已选择/退回"""
        if not self._ocr_click(context, ["下次"], roi=[350, 0, 370, 1280], label="下次外出"):
            self._click(context, (600, 300))
            time.sleep(W_CLICK)
        if not self._ocr_click_above(context, ["伞"], offset_y=-50, roi=ROI_MID, label="伞上方"):
            self._click(context, (360, 500))
            time.sleep(W_CLICK)
        time.sleep(W_CLICK)
        if self._ocr_click(context, ["确认选择", "确认"], roi=ROI_BOTTOM, label="确认选择"):
            pass
        elif self._ocr_click(context, ["已选择", "已选"], roi=ROI_FULL, label="已选择"):
            self._go_back(context)
        else:
            self._go_back(context)
        logger.info("Niwome ②: 完成")

    # ═══════ ④ 完成打卡 ═══════

    def _task_checkin(self, context):
        """④完成打卡：习惯打卡 → 工作 → 返回"""
        if not self._ocr_click(context, ["习惯打卡"], roi=[0, 0, 720, 400], label="习惯打卡"):
            self._click(context, (360, 200))
            time.sleep(W_CLICK)
        self._ocr_click(context, ["工作"], roi=ROI_MID, label="工作")
        self._go_back(context)
        logger.info("Niwome ④: 完成")

    # ═══════ ③ 回应动态 ═══════

    def _task_respond(self, context):
        """③回应动态：最新动态 → 点此回应 → NICE → 返回"""
        if not self._ocr_click(context, ["最新动态", "最新"], roi=ROI_MID, label="最新动态"):
            self._click(context, (440, 150))
            time.sleep(W_CLICK)
        self._ocr_click(context, ["点此回应", "点此", "回应"], label="点此回应")
        context.tasker.controller.post_screencap().wait()
        img = context.tasker.controller.cached_image
        match = context.run_recognition_direct(
            JRecognitionType.TemplateMatch,
            JTemplateMatch(template="niwome/nice.png", threshold=0.6),
            img,
        )
        if match and match.hit:
            box = match.best_result.box
            cx = (box.x + box.w // 2) if hasattr(box, "x") else (box[0] + box[2] // 2)
            cy = (box.y + box.h // 2) if hasattr(box, "y") else (box[1] + box[3] // 2)
            self._click(context, (cx, cy))
            time.sleep(W_CLICK)
        else:
            box_nice, text_nice = self._ocr_find(context, ["NICE", "Nice", "nice"], roi=ROI_FULL)
            if not box_nice:
                time.sleep(W_SHORT)
                box_nice, text_nice = self._ocr_find(context, ["NICE", "Nice", "nice", "ICE", "ice"])
            if box_nice:
                cx = box_nice[0] + box_nice[2] // 3
                cy = box_nice[1] + box_nice[3] // 2
                self._click(context, (cx, cy))
                time.sleep(W_CLICK)
            else:
                self._click(context, (360, 600))
                time.sleep(W_SHORT)
        self._go_back(context)
        logger.info("Niwome ③: 完成")

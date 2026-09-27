import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import pytz

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

from utils import logger
from utils.params import parse_params
from utils.json_io import (
    load_json,
    save_json,
)

CURRENT_FILE_PATH = Path(__file__).resolve()
# agent/custom/action -> 项目根
CONFIG_PATH = (
    CURRENT_FILE_PATH.parent.parent.parent.parent / "config" / "maatot_data.json"
)


@AgentServer.custom_action("JudgeDailyTask")
class JudgeDailyTask(CustomAction):
    """
    通用每日任务控制

    读取 config/maatot_data.json ，按 task_key 存储的时间戳判断是否该运行，
    格式：{"<task_key>": 1719500000000}
    每日任务控制的 task_key 以 daily 结尾。
    本动作只判断、不写时间戳；时间戳由 MarkTaskDone 在任务成功后写入。

    custom_action_param:
        task_key (str):  [必填] 任务的唯一标识键。
        timezone (str):  [选填] 时区，默认 "Asia/Shanghai"。
        reset_hour (int): [选填] 每日刷新时刻（小时），默认 5（即 05:00）。

    如果当天已执行过，本节点的 next 会被清空，后续流程自然终止；
    如果是新一天或首次执行，直接继续沿 next 流转。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        param_dict = parse_params(argv.custom_action_param, "task_key")

        task_key = param_dict.get("task_key")
        timezone_str = param_dict.get("timezone", "Asia/Shanghai")
        reset_hour = param_dict.get("reset_hour", 5)

        data = load_json(CONFIG_PATH, {})
        stored_ms = data.get(task_key)
        now_ms = int(time.time() * 1000)

        if stored_ms is None:
            logger.info(f"[{task_key}] 首次执行，允许任务继续")

            return CustomAction.RunResult(success=True)

        try:
            tz = pytz.timezone(timezone_str)
        except Exception:
            logger.warning(f"[{task_key}] 无效的时区：{timezone_str}")
            tz = pytz.UTC
            logger.warning(f"[{task_key}] 使用默认时区：Asia/Shanghai")

        now_dt = datetime.fromtimestamp(now_ms / 1000, tz)

        # 计算今天刷新时间点
        period_start = now_dt.replace(
            hour=reset_hour,
            minute=0,
            second=0,
            microsecond=0,
        )

        # 当前时间早于刷新时间，说明仍属于昨天周期
        if now_dt < period_start:
            period_start = period_start - timedelta(days=1)
        else:
            period_start = period_start

        stored_dt = datetime.fromtimestamp(stored_ms / 1000, tz)

        # 今天刷新周期内已经执行
        if stored_dt >= period_start:
            context.override_next(argv.node_name, [])

            logger.info(f"[{task_key}] 今日已完成，跳过")

        else:
            logger.info(f"[{task_key}] 新一天开始，允许任务继续")

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("JudgeWeeklyTask")
class JudgeWeeklyTask(CustomAction):
    """
    通用周任务控制

    读取 config/maatot_data.json ，按 task_key 存储的时间戳判断是否该运行，
    格式：{"<task_key>": 1719500000000}
    每周任务控制的 task_key 以 weekly 结尾。
    本动作只判断、不写时间戳；时间戳由 MarkTaskDone 在任务成功后写入。

    custom_action_param:
        task_key (str):      [必填] 任务的唯一标识键。
        timezone (str):      [选填] 时区，默认 "Asia/Shanghai"。
        reset_weekday (int): [选填] 周几刷新，0=周一 ... 6=周日，默认 0。
        reset_hour (int):    [选填] 刷新时刻（小时），默认 5（即 05:00）。

    如果本周已执行过，本节点的 next 会被清空，后续流程自然终止；
    如果是新一周或首次执行，直接继续沿 next 流转。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        param_dict = parse_params(argv.custom_action_param, "task_key")
        task_key = param_dict.get("task_key")
        timezone_str = param_dict.get("timezone", "Asia/Shanghai")
        reset_weekday = param_dict.get("reset_weekday", 0)
        reset_hour = param_dict.get("reset_hour", 5)

        # 读取上次执行时间戳
        data = load_json(CONFIG_PATH, {})
        stored_ms = data.get(task_key)
        now_ms = int(time.time() * 1000)
        # 首次执行
        if stored_ms is None:
            logger.info(f"[{task_key}] 首次执行，允许任务继续")
            return CustomAction.RunResult(success=True)

        # 计算当前周期的起点（最近一次 reset_weekday reset_hour:00）
        try:
            tz = pytz.timezone(timezone_str)
        except Exception:
            logger.warning(f"[{task_key}] 无效的时区：{timezone_str}")
            tz = pytz.UTC
            logger.warning(f"[{task_key}] 使用默认时区：Asia/Shanghai")

        now_dt = datetime.fromtimestamp(now_ms / 1000, tz)

        days_since = (now_dt.weekday() - reset_weekday) % 7
        period_start = now_dt.replace(
            hour=reset_hour, minute=0, second=0, microsecond=0
        ) - timedelta(days=days_since)
        if now_dt < period_start:
            period_start -= timedelta(days=7)

        stored_dt = datetime.fromtimestamp(stored_ms / 1000, tz)

        if stored_dt >= period_start:
            context.override_next(argv.node_name, [])
            logger.info(f"[{task_key}] 本周已完成，跳过")
        else:
            logger.info(f"[{task_key}] 新一周开始，允许任务继续")

        return CustomAction.RunResult(success=True)


@AgentServer.custom_action("MarkTaskDone")
class MarkTaskDone(CustomAction):
    """
    通用周期任务成功标记

    在任务成功后，按 task_key 写入当前时间戳到 config/maatot_data.json，
    格式：{"<task_key>": 1719500000000}。
    与 JudgeDailyTask / JudgeWeeklyTask 配合使用：Judge 只判断是否该运行，
    本动作在成功后记录时间戳，避免任务失败也被记录为已完成。

    custom_action_param:
        task_key (str): [必填] 任务的唯一标识键，需与对应 Judge 节点一致。
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        param_dict = parse_params(argv.custom_action_param, "task_key")
        task_key = param_dict.get("task_key")

        data = load_json(CONFIG_PATH, {})
        data[task_key] = int(time.time() * 1000)
        save_json(CONFIG_PATH, data)

        logger.info(f"[{task_key}] 任务成功完成，记录时间戳")

        return CustomAction.RunResult(success=True)

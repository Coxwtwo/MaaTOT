import json
from datetime import datetime
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils import logger

WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


@AgentServer.custom_action("WeekdayCheck")
class WeekdayCheck(CustomAction):
    """
    检查今天是否为配置的目标星期几。
    如果不是，跳过当前任务（调用"停止任务"）。

    custom_action_param:
    {
        "target_weekday": 0-6 (0=周一, 6=周日), 或 -1 表示每天执行
    }
    """

    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        try:
            params = json.loads(argv.custom_action_param)
        except (json.JSONDecodeError, TypeError):
            params = {}

        target_weekday = params.get("target_weekday", -1)

        # -1 = 每天执行
        if target_weekday == -1:
            logger.info("WeekdayCheck: 设置为每天执行，放行")
            return CustomAction.RunResult(success=True)

        today = datetime.now().weekday()  # 0=周一 ... 6=周日

        if today == target_weekday:
            logger.info(
                f"WeekdayCheck: 今天是{WEEKDAY_NAMES[today]}，执行试炼神殿"
            )
            return CustomAction.RunResult(success=True)
        else:
            logger.info(
                f"WeekdayCheck: 今天是{WEEKDAY_NAMES[today]}，"
                f"目标日是{WEEKDAY_NAMES[target_weekday]}，跳过试炼神殿"
            )
            context.run_task("停止任务")
            return CustomAction.RunResult(success=False)

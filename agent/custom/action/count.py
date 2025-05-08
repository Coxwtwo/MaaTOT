import json

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from utils import logger

@AgentServer.custom_action("Count")
class Count(CustomAction):
    """
    控制 node 的执行次数 。

    参数格式:
    {
            "self": "节点名称",
            "count": 当前执行计数,
            "target_count": 最大执行次数,
            "next_node": ["后续节点名称"]
    }
    """
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        argv: dict = json.loads(argv.custom_action_param)
        logger.debug(f"Count argv: {argv}")
        if not argv:
            return CustomAction.RunResult(success=True)
        # 默认达到最大次数后终止任务
        default_next_nodes =[
            "返回主菜单",
            "停止任务"
        ]
        if argv.get("count") < argv.get("target_count"):
            argv["count"] += 1
            context.override_pipeline(
                {
                    argv.get("self"): {
                        "custom_action_param": argv,
                    },
                }
            )
        # 达到最大次数后重置计数器状态，触发后续节点
        else:
            logger.info(f"{argv.get("self")} 节点执行次数达到最大值 {argv.get("target_count")} 次")
            next_nodes = argv.get("next_node", default_next_nodes)
            logger.debug(f"next_nodes: {next_nodes}")
            context.override_pipeline(
                {
                    argv.get("self"): {
                        "custom_action_param": {
                            "self": argv.get("self"),
                            "count": 1,
                            "target_count": argv.get("target_count"),
                            "next_node": next_nodes
                        },
                    },
                }
            )
            # 执行后续节点
            for node in next_nodes:
                context.run_task(node)

        return CustomAction.RunResult(success=True)
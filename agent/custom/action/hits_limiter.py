import json

from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context

from utils import logger

@AgentServer.custom_action("HitsLimiter")
class HitsLimiter(CustomAction):
    """
    限制 node 的最大运行次数 。

    参数格式:
    {
            "current_count": 当前已执行次数,
            "max_count": 最大可执行次数,
            "next_nodes": ["后续节点名称"]
    }
    """
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        param_dict: dict = json.loads(argv.custom_action_param)
        logger.debug(f"Count argv: {argv}")
        if not param_dict:
            return CustomAction.RunResult(success=True)
        # 默认达到最大次数后终止任务
        default_next_nodes =[
            "返回主菜单",
            "停止任务"
        ]
        if param_dict.get("current_count") < param_dict.get("max_count"):
            param_dict["current_count"] += 1
            context.override_pipeline(
                {
                    argv.node_name: {
                        "custom_action_param": param_dict,
                    },
                }
            )
        # 达到最大次数后重置计数器状态，触发后续节点
        else:
            logger.info(f"{argv.node_name} 节点执行次数达到最大值 {param_dict.get("max_count")} 次")
            next_nodes = param_dict.get("next_nodes", default_next_nodes)
            logger.debug(f"next_nodes: {next_nodes}")
            context.override_pipeline(
                {
                    argv.node_name: {
                        "custom_action_param": {
                            "current_count": 1,
                            "max_count": param_dict.get("max_count"),
                            "next_nodes": next_nodes
                        },
                    },
                }
            )
            # 执行后续节点
            for node in next_nodes:
                context.run_task(node)

        return CustomAction.RunResult(success=True)
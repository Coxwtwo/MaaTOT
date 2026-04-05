import json
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils import logger

@AgentServer.custom_action("DynamicOverride")
class DynamicOverride(CustomAction):
    """
    DynamicOverride 通用动态覆盖动作。
    允许在脚本运行期间动态修改 Pipeline 中的节点配置（仅对当前任务上下文生效）。
    主要用于在特定条件下（如能量饮料补给完成后）禁用某些节点以改变任务执行流。
    """
    def run(
        self, context: Context, argv: CustomAction.RunArg
    ) -> CustomAction.RunResult:
        """
        执行覆盖逻辑
        :param argv.custom_action_param: 包含 target_node 和 override_content 的 JSON 字符串
        """
        try:
            # 1. 解析参数
            param_dict = json.loads(argv.custom_action_param)
            target_node = param_dict.get("target_node")
            override_content = param_dict.get("override_content")
            
            if not target_node or override_content is None:
                logger.error("DynamicOverride: 参数缺失 'target_node' 或 'override_content'")
                return CustomAction.RunResult(success=False)
                
            # 2. 应用覆盖：利用框架提供的接口直接修改内存中的节点配置
            # 示例：{"体力检查": {"enabled": false}}
            override_config = {
                target_node: override_content
            }
            
            success = context.override_pipeline(override_config)
            
            if success:
                logger.info(f"DynamicOverride: 已成功对节点 '{target_node}' 应用动态覆盖")
            else:
                logger.error(f"DynamicOverride: 对节点 '{target_node}' 执行覆盖操作失败")
                
            return CustomAction.RunResult(success=success)

        except Exception as e:
            logger.exception(f"DynamicOverride: 发生异常: {e}")
            return CustomAction.RunResult(success=False)

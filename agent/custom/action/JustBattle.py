from maa.agent.agent_server import AgentServer  
from maa.custom_action import CustomAction  
from maa.context import Context  
import json  
from utils import logger
  
@AgentServer.custom_action("JustBattle")  
class JustBattleAction(CustomAction):  
    def run(self, context: Context, argv: CustomAction.RunArg) -> bool:  
        # 从参数中获取关卡编号  
        param = json.loads(argv.custom_action_param)  
        stage_number = param.get("stage_number", "")  
        episode_str, level_str = stage_number.split('-')
        episode_int = int(episode_str)
        level_int = int(level_str)
        
        # 根据关卡编号override节点信息
        if 1 <= episode_int <= 8:
            context.override_pipeline({
                "Click_选择主线篇章": {
                    "expected": "海奥森篇"
                    }
            })
            if episode_int == 5:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E5P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E5P2.png",
                            "threshold": 0.93
                        }
                    })
                elif 25<= level_int <=36:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E5P3.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
            elif episode_int == 6:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E6P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E6P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
            elif episode_int == 7:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E7P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E7P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
        elif 9 <= episode_int <= 15:
            context.override_pipeline({
                "Click_选择主线篇章": {
                    "expected": "剑兰谷篇"
                    }
            })
            if episode_int == 11:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E11P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E11P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
            elif episode_int == 14:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E14P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E14P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
        elif 16 <= episode_int <= 18:
            context.override_pipeline({
                "Click_选择主线篇章": {
                    "expected": "亚宁篇"
                    }
            })
            if episode_int == 18:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E18P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E18P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
            elif episode_int == 17:
                if 1 <= level_int <= 12:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E17P1.png",
                            "threshold": 0.93
                        }
                    })
                elif 13<= level_int <=24:
                    context.override_pipeline({
                        "Click_进入异常副本": {
                            "recognition": "TemplateMatch",
                            "template": "Debate/E17P2.png",
                            "threshold": 0.93
                        }
                    })
                else:
                    print("章节数字超出有效范围")
        else:
            print("章节数字超出有效范围")

        # override 具体关卡编号
        node_name = "Click_进入异常关卡"  
        config = {  
            node_name: {  
                "expected": stage_number 
            }  
        }  
        context.override_pipeline(config)

        return True
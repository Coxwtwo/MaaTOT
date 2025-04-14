import os
import sys
import json
import subprocess
from pathlib import Path


def agent():
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit

    import custom_actions
    import custom_recognitions
    from utils import logger

    Toolkit.init_option("./")

    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    logger.info("AgentSever 启动")
    logger.info("id:"+socket_id)
    AgentServer.join()
    AgentServer.shut_down()
    logger.info("AgentSever 关闭")


def main():
    agent()


if __name__ == "__main__":
    main()
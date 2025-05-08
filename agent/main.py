import os
import sys
import json
import subprocess
from pathlib import Path

# 默认编码 utf-8
sys.stdout.reconfigure(encoding="utf-8")

# 获取当前main.py所在路径并设置上级目录为工作目录
current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)
print(f"设置工作目录为: {parent_dir}")

# 将当前目录添加到路径
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from utils import logger
except ImportError:
    # 如果logger不存在，创建一个简单的logger
    import logging

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
    )
    logger = logging

def read_pip_config() -> dict:
    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "pip_config.json"
    default_config = {
        "enable_pip_install": True,
        "mirror": "https://mirrors.ustc.edu.cn/pypi/simple",
    }

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("读取pip配置失败，使用默认配置")
        return default_config

def write_pip_config(key_values: dict) -> bool:
    config_path = Path("./config/pip_config.json")
    try:
        # 读取现有配置
        config = read_pip_config()
        
        # 更新指定配置项
        for key, value in key_values.items():
            if key in config:
                config[key] = value
            else:
                # 如果要允许新增配置项，移除此判断
                logger.warning(f"尝试写入未知配置项: {key}")
                continue
        # 写回文件
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        logger.exception("写入 pip 配置失败")
        return False

def install_requirements(req_file="requirements.txt", mirror=None) -> bool:
    req_path = Path(req_file)
    if not req_path.exists():
        logger.error(f"requirements.txt 不存在")
        return False

    try:
        logger.info("开始安装依赖...")
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-U",
            "-r",
            str(req_path),
            "--no-warn-script-location",
        ]

        if mirror:
            logger.info(f"使用镜像源: {mirror}")
            cmd.extend(["-i", mirror])

        subprocess.check_call(cmd)
        logger.info("依赖安装完成")
        return True
    except:
        logger.exception("pip 安装依赖时出错")
        return False

def check_and_install_dependencies():
    pip_config = read_pip_config()
    mirror = pip_config.get("mirror", None)
    enable_pip_install = pip_config.get("enable_pip_install", True)

    logger.info(f"启用 pip 安装依赖: {enable_pip_install}")

    if enable_pip_install :
        if install_requirements(mirror=mirror):
            logger.info("依赖检查完成")
            # 修改安装开关
            write_pip_config({
                "enable_pip_install": False
            })
        else:
            logger.warning("依赖安装失败，程序可能无法正常运行")
    else:
        logger.info("跳过依赖安装")



def agent():
    from maa.agent.agent_server import AgentServer
    from maa.toolkit import Toolkit

    import custom
    from utils import logger

    Toolkit.init_option("./")

    socket_id = sys.argv[-1]

    AgentServer.start_up(socket_id)
    logger.info("AgentServer 启动")
    AgentServer.join()
    AgentServer.shut_down()
    logger.info("AgentServer 关闭")


def main():
    check_and_install_dependencies()
    agent()


if __name__ == "__main__":
    main()
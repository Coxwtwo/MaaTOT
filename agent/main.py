import os
import sys
import json
import subprocess
from pathlib import Path

# 默认编码 utf-8
sys.stdout.reconfigure(encoding="utf-8")

# 获取当前main.py所在路径并设置上级目录为工作目录
current_file_path = os.path.abspath(__file__)
current_script_dir = os.path.dirname(current_file_path)  # 包含此脚本的目录
project_root_dir = os.path.dirname(current_script_dir)  # 指定的项目根目录

# 更改CWD到项目根目录
if os.getcwd() != project_root_dir:
    print(f"pre cwd: {os.getcwd()}")
    os.chdir(project_root_dir)
print(f"set cwd: {os.getcwd()}")

# 将脚本自身的目录添加到sys.path，以便导入utils、maa等模块
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)

try:
    from utils import logger
except ImportError:
    # 如果logger不存在，创建一个简单的logger
    import logging

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
    )
    logger = logging

VENV_NAME = ".venv"  # 虚拟环境目录的名称
VENV_DIR = Path(project_root_dir) / VENV_NAME


def _is_running_in_our_venv():
    """检查脚本是否在虚拟环境中运行。"""
    # 使用 sys.prefix 和 sys.base_prefix 来判断是否在虚拟环境中
    in_venv = sys.prefix != sys.base_prefix

    if in_venv:
        logger.debug(f"当前在虚拟环境中运行: {sys.prefix}")
    else:
        logger.debug(f"当前不在虚拟环境中，使用系统Python: {sys.prefix}")

    return in_venv


def ensure_venv_and_relaunch_if_needed():
    """
    确保venv存在，并且如果尚未在脚本管理的venv中运行，
    则在其中重新启动脚本。支持Windows系统。
    """
    logger.info(f"检测到系统: {sys.platform}。当前Python解释器: {sys.executable}")

    if _is_running_in_our_venv():
        logger.info(f"已在目标虚拟环境 ({VENV_DIR}) 中运行。")
        return

    if not VENV_DIR.exists():
        logger.info(f"正在 {VENV_DIR} 创建虚拟环境...")
        try:
            # 使用当前运行此脚本的Python（系统/外部Python）
            subprocess.run(
                [sys.executable, "-m", "venv", str(VENV_DIR)],
                check=True,
                capture_output=True,
            )
            logger.info(f"创建成功")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"创建失败: {e.stderr.decode(errors='ignore') if e.stderr else e.stdout.decode(errors='ignore')}"
            )
            logger.error("正在退出")
            sys.exit(1)
        except FileNotFoundError:
            logger.error(
                f"命令 '{sys.executable} -m venv' 未找到。请确保 'venv' 模块可用。"
            )
            logger.error("无法在没有虚拟环境的情况下继续。正在退出。")
            sys.exit(1)

    if sys.platform.startswith("win"):
        python_in_venv = VENV_DIR / "Scripts" / "python.exe"
    else:
        python3_path = VENV_DIR / "bin" / "python3"
        python_path = VENV_DIR / "bin" / "python"
        if python3_path.exists():
            python_in_venv = python3_path
        elif python_path.exists():
            python_in_venv = python_path
        else:
            python_in_venv = python3_path  # 默认使用python3，让后续错误处理捕获

    if not python_in_venv.exists():
        logger.error(f"在虚拟环境 {python_in_venv} 中未找到Python解释器。")
        logger.error("虚拟环境创建可能失败或虚拟环境结构异常。")
        sys.exit(1)

    logger.info(f"正在使用虚拟环境Python重新启动")

    try:
        # Use absolute path to this script when relaunching inside the venv.
        # sys.argv[0] may be a relative path (e.g. './../agent/main.py') which
        # resolves differently when cwd changes. Use the absolute path of
        # the currently running file (`current_file_path`) to avoid that.
        script_abs = current_file_path
        args = sys.argv[1:]
        cmd = [str(python_in_venv), str(script_abs)] + args
        logger.info(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=os.environ.copy(),
            check=False,  # 不在非零退出码时抛出异常
        )
        # 退出时使用子进程的退出码
        sys.exit(result.returncode)

    except Exception as e:
        logger.exception(f"在虚拟环境中重新启动脚本失败: {e}")
        sys.exit(1)


def read_interface_version(interface_file_name="./interface.json") -> str:
    interface_path = Path(project_root_dir) / interface_file_name
    assets_interface_path = Path(project_root_dir) / "assets" / interface_file_name

    target_path = None
    if interface_path.exists():
        target_path = interface_path
    elif assets_interface_path.exists():
        return "DEBUG"

    if target_path is None:
        logger.warning("未找到interface.json")
        return "unknown"

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            interface_data = json.load(f)
            return interface_data.get("version", "unknown")
    except Exception:
        logger.exception(f"读取interface.json版本失败，文件路径：{target_path}")
        return "unknown"


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
    req_path = Path(project_root_dir) / req_file
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
        succeed_config = {
            "enable_pip_install": False,
            "mirror": "https://mirrors.ustc.edu.cn/pypi/simple",
        }
        write_pip_config(succeed_config)
        return True
    except:
        logger.exception("pip 安装依赖时出错")
        return False


def check_and_install_dependencies():
    pip_config = read_pip_config()
    mirror = pip_config.get("mirror", None)
    enable_pip_install = pip_config.get("enable_pip_install", True)

    logger.info(f"启用 pip 安装依赖: {enable_pip_install}")

    if enable_pip_install:
        if install_requirements(mirror=mirror):
            logger.info("依赖检查完成")
        else:
            logger.warning("依赖安装失败，程序可能无法正常运行")
    else:
        logger.info("禁用 pip 安装依赖，跳过依赖安装")


def agent(is_dev_mode=False):
    try:
        # 清理模块缓存
        utils_modules = [
            name for name in list(sys.modules.keys()) if name.startswith("utils")
        ]
        for module_name in utils_modules:
            del sys.modules[module_name]

        # 动态导入 utils 的所有内容
        import utils
        import importlib

        importlib.reload(utils)

        # 将 utils 的所有公共属性导入到当前命名空间
        for attr_name in dir(utils):
            if not attr_name.startswith("_"):
                globals()[attr_name] = getattr(utils, attr_name)

        if is_dev_mode:
            from utils.logger import change_console_level

            change_console_level("DEBUG")
            logger.info("开发模式：日志等级已设置为DEBUG")

        from maa.agent.agent_server import AgentServer
        from maa.toolkit import Toolkit

        import custom

        Toolkit.init_option("./")

        if len(sys.argv) < 2:
            logger.error("Usage: python agent_main.py <socket_id>")
            logger.error("socket_id is provided by AgentIdentifier.")
            exit(1)

        socket_id = sys.argv[-1]
        logger.debug(f"socket_id: {socket_id}")

        AgentServer.start_up(socket_id)
        logger.info("AgentServer启动")
        AgentServer.join()
        AgentServer.shut_down()
        logger.info("AgentServer关闭")
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("考虑重新配置环境")
        sys.exit(1)
    except Exception as e:
        logger.exception("agent运行过程中发生异常")
        raise


def main():
    # 以 interface.json 的位置区分开发模式和用户模式
    current_version = read_interface_version()
    is_dev_mode = current_version == "DEBUG"

    # 如果是开发模式，启动虚拟环境
    if is_dev_mode:
        ensure_venv_and_relaunch_if_needed()
    check_and_install_dependencies()

    if is_dev_mode:
        os.chdir(Path("./assets"))
        logger.info(f"set cwd: {os.getcwd()}")

    agent(is_dev_mode=is_dev_mode)


if __name__ == "__main__":
    main()

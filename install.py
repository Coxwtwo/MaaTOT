from pathlib import Path

import shutil
import sys
import json
import platform
import subprocess

from configure import configure_ocr_model


working_dir = Path(__file__).parent
install_path = working_dir / Path("install")
version = len(sys.argv) > 1 and sys.argv[1] or "v0.0.1"


def install_deps():
    if not (working_dir / "deps" / "bin").exists():
        print("Please download the MaaFramework to \"deps\" first.")
        print("请先下载 MaaFramework 到 \"deps\"。")
        sys.exit(1)

    shutil.copytree(
        working_dir / "deps" / "bin",
        install_path,
        ignore=shutil.ignore_patterns(
            "*MaaDbgControlUnit*",
            "*MaaThriftControlUnit*",
            "*MaaRpc*",
            "*MaaHttp*",
        ),
        dirs_exist_ok=True,
    )
    shutil.copytree(
        working_dir / "deps" / "share" / "MaaAgentBinary",
        install_path / "MaaAgentBinary",
        dirs_exist_ok=True,
    )


def install_resource():

    configure_ocr_model()

    shutil.copytree(
        working_dir / "assets" / "resource",
        install_path / "resource",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        working_dir / "assets" / "interface.json",
        install_path,
    )

    with open(install_path / "interface.json", "r", encoding="utf-8") as f:
        interface = json.load(f)

    interface["version"] = version

    with open(install_path / "interface.json", "w", encoding="utf-8") as f:
        json.dump(interface, f, ensure_ascii=False, indent=4)


def install_chores():
    shutil.copy2(
        working_dir / "README.md",
        install_path,
    )
    shutil.copy2(
        working_dir / "LICENSE",
        install_path,
    )

def install_agent():
    shutil.copytree(
        working_dir / "agent",
        install_path / "agent",
        dirs_exist_ok=True,
    )


def create_shortcut():
    """
    创建 MaaPiCli.exe 的快捷方式（Windows 生成 .lnk，Linux 生成 .desktop）
    """
    exe_name = "MaaPiCli.exe"
    shortcut_name = "MaaTOT.lnk" if platform.system() == "Windows" else "maa-cli.desktop"
    icon_file = "logo.ico"

    exe_path = install_path / exe_name
    shortcut_path = install_path / shortcut_name
    icon_path = working_dir / icon_file

    # 检查可执行文件是否存在
    if not exe_path.exists():
        print(f"错误：{exe_name} 未找到，无法创建快捷方式")
        return

    try:
        if platform.system() == "Windows":
            # Windows 使用 PowerShell 创建快捷方式
            ps_script = f"""
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
            $Shortcut.TargetPath = '{exe_path}'
            $Shortcut.WorkingDirectory = '{install_path}'
            $Shortcut.IconLocation = '{icon_path},0'  # 设置图标
            $Shortcut.Save()
            """
            subprocess.run(["powershell", "-Command", ps_script], check=True)
        elif platform.system() == "Linux":
            # Linux 生成 .desktop 文件
            desktop_content = f"""
            [Desktop Entry]
            Version=1.0
            Type=Application
            Name=MaaTOT
            Exec={exe_path}
            Icon={icon_path}
            Terminal=true
            Categories=Utility;
            """
            with open(shortcut_path, 'w') as f:
                f.write(desktop_content.strip())
            # 添加可执行权限
            shortcut_path.chmod(0o755)
        print(f"快捷方式已创建：{shortcut_path}")
    except Exception as e:
        print(f"创建快捷方式失败：{str(e)}")


if __name__ == "__main__":
    install_deps()
    install_resource()
    install_chores()
    install_agent()
    create_shortcut()  # 创建快捷方式

    print(f"Install to {install_path} successfully.")
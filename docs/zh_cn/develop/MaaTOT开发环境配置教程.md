<!-- markdownlint-disable MD033 MD041 -->
本教程是在以下教程基础上修改得到的：

- [纯网页端 PR 教程 | MAA 文档站](https://docs.maa.plus/zh-cn/develop/pr-tutorial.html)
- [开发指南 | MAA 文档站](https://docs.maa.plus/zh-cn/develop/development.html#%E5%AE%8C%E6%95%B4%E7%8E%AF%E5%A2%83%E9%85%8D%E7%BD%AE%E6%B5%81%E7%A8%8B-windows)
- [开发前须知 | M9A 文档站](https://1999.fan/zh_cn/develop/development.html)
- [MaaXYZ/MaaPracticeBoilerplate： MaaFramework 通用项目模板](https://github.com/MaaXYZ/MaaPracticeBoilerplate?tab=readme-ov-file)

本教程的前置要求：

- 有github账号，了解github基本操作
- 已安装git，了解如何使用git bash
- 已安装python（≥3.11）
- 已安装VS Code

推荐阅读的其他教程：

- [如何实现一个自己的MAA？MaaFramework集成教程来啦！](https://www.bilibili.com/video/BV1yr421E7MW)

# MaaTOT的完整环境配置流程（Windows）

1. 如果很久以前 Fork 过，先在自己仓库的 `Settings` 里，翻到最下面，删除

2. 打开 [MaaTOT主仓库](https://github.com/Coxwtwo/MaaTOT)，点击 `Fork`，继续点击 `Create fork`

3. 克隆你自己仓库下的 dev 分支到本地，并拉取子模块

    ```bash
    git clone --recurse-submodules <你的仓库的 git 链接> -b main
    ```

    注意不要忘记 **--recursive**，否则可能导致OCR异常失败

    如已克隆但发现资源缺失，可运行:

    ```bash
    git submodule update --init --recursive
    ```

4. 下载OCR资源文件

    下载 OCR（文字识别）资源文件 [ppocr_v5.zip](https://download.maafw.xyz/MaaCommonAssets/OCR/ppocr_v5/ppocr_v5-zh_cn.zip) 解压到 `assets/resource/base/model/ocr/` 目录下，确保路径如下：

    ```plaintext
    assets/resource/base/model/ocr/
    ├── det.onnx
    ├── keys.txt
    └── rec.onnx
    ```

    或在cmd中，切换至MaaTOT主文件夹路径，运行

    ```cmd
    python configure.py
    ```

5. 【可选】安装[MaaDebugger](https://github.com/MaaXYZ/MaaDebugger)
    - 独立的Maa脚本调试工具，网页端操作

    ```cmd
    python -m pip install MaaDebugger
    ```

    - 如遇安装失败，可建立虚拟环境（python=3.12）重试

6. 【可选】【推荐】安装[Maa Pipeline Support](https://marketplace.visualstudio.com/items?itemName=nekosu.maa-support)
    - VS Code插件，在VS Code插件面板中安装
    - 需要安装C++依赖库，不然会报错MaaFramework not loaded。运行MaaTOT的[release包](https://github.com/Coxwtwo/MaaTOT/releases)里的`DependencySetup_依赖库安装_win.bat`安装即可。

7. 【可选】下载 MaaFramework 的 [Release包](https://github.com/MaaXYZ/MaaFramework/releases)，解压到 `deps` 文件夹中。
    - 用于本地测试MaaPiCli版本

8. 【可选】设置嵌入式python
    - 用于本地测试MaaPiCli版本

    在cmd中，切换至MaaTOT主文件夹路径，运行

    ```cmd
    python tools/ci/setup_embed_python.py
    ```

    安装依赖库

    ```cmd
    install/python/python.exe -m pip install -r requirements.txt
    ```

    开发完成后，执行`install.py`即可执行打包，会在`install`文件夹中生成`MaaPiCli.exe`用于测试

    ```cmd
    python install.py
    ```

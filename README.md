<!-- markdownlint-disable MD033 MD041 -->
<div align="center">
  <img alt="LOGO" src="./logo.png" width="64" height="64" />

## MaaTOT

基于全新架构的夏左莫陆小助手。图像技术 + 模拟控制，解放双手！
由 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 强力驱动！

</div>

## 可能会有的功能

- [x] 启动游戏
  - [x] 官服
  - [x] B 服
- [x] 领取奖励
  - [x] 邮件
  - [x] 友谊徽章
  - [x] 每日每周任务
  - [x] 绮思经验
- [x] 基地
  - [x] 资源申请
  - [x] 案件解析
  - [x] 每日每周酬谢
- [ ] 辩论
  - [x] 复盘进修副本
  - [x] 复盘异常关卡刷技能材料
  - [x] 复盘异常关卡刷印象
  - [ ] 复盘异常关卡刷思绪残影（残影卡太多了没写完）
  - [x] 外勤委托：需要提前配好卡组，战力不足时会直接退出。
- [x] 其他
  - [x] 专属甜心制作：目前会自动制作背包中第一件未完成物品。
  - [x] 逸梦系统收集花露
  - [x] 好感度：目前只支持触摸获取好感度，只能指定单个男主获取好感至每日上限。


## 如何使用

**以windows用户为例：**

前置准备:

1. 可以参考 [模拟器支持情况](https://maa.plus/docs/zh-cn/manual/device/windows.html) 下载模拟器，推荐使用 `MuMu 模拟器 12`。

2. 修改模拟器分辨率，最低 `1280 * 720`，更高不限。

3. 在模拟器上安装未定事件簿（支持官服和B服）。

4. 启动未定事件簿并登录账号（只需要登录一次，除非登录失效或者你希望切换账号）。

5. 下载对应平台的压缩包并解压（大多数情况下选择 MaaTOT-win-x86_64-vXXX.zip，除非你确定自己的电脑是 arm 架构）。

6. 确认解压完整，请勿将压缩包解压到有中文的目录下，也不要解压到如 `C:\`、`C:\Program Files\` 等需要 UAC 权限的路径。

开始使用:
1. 首次使用，双击打开 `MaaPiCli.exe`。

2. 设置连接设备。通常输入 `1` 即可，程序会自动检测正在运行的模拟器，你也可以选择手动输入 `adb.exe` 的完整路径。

3. 选择客户端类型。

4. 输入需要执行的任务序号。
    - 以空格分隔，例如 `1 2 3 4 5` 和 `2 3 1 4 5`，序号的顺序代表着执行顺序
    - 序号可重复，例如 `5 1 2 3 4 5`

5. 启动！

 - 后续使用除非需要连接的设备的配置不存在，否则无需再次进行连接设备设置
 - 后续使用无需再次选择客户端和输入需要执行的任务

本项目基于 MaaFramework 开发，使用中遇到的问题可以参考 [MAA常见问题](https://maa.plus/docs/zh-cn/manual/faq.html)


## 图形化界面

本项目图形界面基于 MFAAvalonia 。目前仅Windows可用, 解压后运行 MFAAvalonia.exe。使用步骤与 MaaPiCli.exe 大致相同

## 开发相关
如果你希望参与开发才需要看这节，使用本项目开发的软件请看 [如何使用](#如何使用) 这节。

本项目基于MaaFramework开发，在开发前，请先了解 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 相关事项。

开发相关事项请查看文档 [开发相关](./docs/开发相关.md) 。

## 鸣谢

感谢自动化测试框架 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 开发者的贡献。
感谢GUI 项目 **[MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)** 开发者的贡献。
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
  - [x] 绮思
- [x] 基地
  - [x] 资源申请
  - [x] 案件解析
  - [x] 每日每周酬谢
- [ ] 辩论（注意，外勤委托只能在体力充足的前提下以自动的次数战斗，体力不足时会终止任务）
  - [x] 复盘进修副本
  - [x] 复盘异常关卡刷技能材料
  - [x] 复盘异常关卡刷印象
  - [ ] 复盘异常关卡刷思绪残影（残影卡太多了没写完）
  - [x] 外勤委托：需要提前配好卡组，战力不足时会直接退出。
  - [x] 补充体力：可以喝能量饮料补充体力（目前无法设置使用数量，只能通过多次执行任务喝多瓶能量饮料）
- [x] 其他
  - [x] 专属甜心制作：目前会自动制作背包中第一件未完成物品。
  - [x] 逸梦系统收集花露（每张梦笺收集完成后，需要手动选择新的梦笺。）
  - [x] 好感度：目前只支持触摸获取好感度，只能指定单个男主获取好感至每日上限。

## 图形化界面

本项目图形化界面基于 MFAAvalonia，解压后运行 MFATOT.exe 即可使用图形化界面。

## 如何使用

前置准备:

1. 可以参考 [模拟器支持情况](https://maa.plus/docs/zh-cn/manual/device/windows.html) 下载模拟器，推荐使用 `MuMu 模拟器 12`。

2. 修改模拟器分辨率，最低 `1280 * 720`，更高不限。

3. 在模拟器上安装未定事件簿（支持官服和B服）。

4. 启动未定事件簿并登录账号（只需要登录一次，除非登录失效或者你希望切换账号）。

5. 下载对应平台的压缩包并解压（大多数情况下选择 MaaTOT-win-x86_64-vXXX.zip，除非你确定自己的电脑是 arm 架构）。

6. 确认解压完整，请勿将压缩包解压到有中文的目录下，也不要解压到如 `C:\`、`C:\Program Files\` 等需要 UAC 权限的路径。

开始使用:

   1. 首次使用，双击打开 `MFATOT.exe`。

   2. 设置连接设备。查看右上角**连接**区域，程序会自动检测正在运行的模拟器，你也可以选择手动输入 `adb.exe` 的完整路径。

   3. 选择游戏客户端类型。查看左上角**资源类型**区域，程序会自动选择官服，你可以手动选择官服或B服。

   4. 选择需要执行的任务。
      - 点击任务前的方框勾选任务。
      - 按住并上下拖动任务进行排序。
      - 点击任务末尾的齿轮对任务选项进行设置。
      - 右键点击任务可以删除任务。
      - 点击任务列表右上角加号可以添加任务。

   5. 启动！

   - 后续使用无需再次进行连接设备设置，除非需要连接的设备不存在。
   - 后续使用无需再次选择客户端和需要执行的任务，当然你随时可以进行更改。

本项目基于 MaaFramework 开发，使用中遇到的问题可以参考 [MAA常见问题](https://maa.plus/docs/zh-cn/manual/faq.html)

~~1. 首次使用，双击打开 `MaaPiCli.exe`。~~

~~2. 设置连接设备。通常输入 `1` 即可，程序会自动检测正在运行的模拟器，你也可以选择手动输入 `adb.exe` 的完整路径。~~

~~3. 选择客户端类型。~~

~~4. 输入需要执行的任务序号。
    - 以空格分隔，例如 `1 2 3 4 5` 和 `2 3 1 4 5`，序号的顺序代表着执行顺序
    - 序号可重复，例如 `5 1 2 3 4 5`~~
## 开发相关

如果你希望参与开发才需要看这节，使用本项目开发的软件请看 [如何使用](#如何使用) 这节。

本项目基于MaaFramework开发，在开发前，请先了解 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 相关事项。

开发相关事项请查看文档 [开发相关](./docs/zh_cn/开发相关.md) 。

## 鸣谢

感谢自动化测试框架 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 开发者的贡献。

感谢 GUI 项目 **[MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)** 开发者的贡献。
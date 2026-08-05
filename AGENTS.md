<!-- markdownlint-disable MD033 MD041 -->

# MaaTOT AI Agent 编码指南

欢迎参与 MaaTOT 的开发！本指南帮助 AI Agent 理解项目结构和编码规范。

---

> [!CAUTION]
>
> **首要准则：产出符合编码规范的代码**
>
> **[编码规范](docs/zh_cn/develop/编码规范.md) 是代码产出的基准。AI 生成的代码必须符合规范。**
> AI 应在用户指令可能违反规范时主动提醒，给出符合规范的替代方案，但不替代用户的最终判断。
>
> | 用户意图 | AI 的默认做法 |
> | --- | --- |
> | 希望解决节点不稳定 | 增加中间识别节点或 `pre_wait_freezes` / `post_wait_freezes`，不引入硬延迟 |
> | 希望操作失败后自动恢复 | 分析失败根因（哪个节点、哪个识别不符合预期），修补对应节点，而非盲目重试 |
> | 未提供截图/界面信息就让 AI 写 Pipeline | 说明 Pipeline 强依赖界面信息，缺乏截图只能产出幻觉代码。要求提供截图、ROI、界面跳转关系后再编写 |
> | 让 AI 开发功能并直接提 PR | 先在对话中做增量辅助，由用户做架构设计、自行 review 后再决定是否提交 |
> | 让 AI 全权负责修 bug 不 review | 产出修复并说明改动逻辑，用户理解并 review 后再提交 |
> | 在 Custom 里写大段流程控制 | 将流程逻辑留在 Pipeline JSON，Custom 仅处理复杂算法，遵循「Pipeline 管流程，Custom 管难点」 |
> | 整体识别一次然后连点多次 | 每步操作都有独立识别节点，遵循「识别 → 操作 → 再识别」 |
>
> **核心原则：AI 产出的代码必须合规，用户无需事后纠正。**

---

## 项目概览

MaaTOT 是基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 开发的**未定事件簿**游戏自动化工具。

- **Pipeline**：`assets/resource/base/pipeline/` 下的 JSON 文件定义自动化任务链（识别 → 操作 → 再识别）。
- **Task 入口**：`assets/resource/tasks/T_*.json` 是用户可选的任务包装器（含选项配置）。
- **Custom 扩展**：`agent/custom/action/` 和 `agent/custom/recognition/` 存放 Python 自定义逻辑。
- **配置入口**：`assets/interface.json` 定义任务列表、控制器、资源组和 Agent 启动项。
- **渠道覆盖**：Bilibili 服和国际服在 `assets/resource/bilibili/` 和 `assets/resource/intl/` 下有独立的 文件 覆盖。

## 关键文件

| 文档 | 什么时候看 |
| --- | --- |
| [开发前须知](docs/zh_cn/develop/开发前须知.md) | 了解项目、搭环境、参与开发 |
| [快速开始](docs/zh_cn/develop/快速开始.md) | 了解开发流程，只改一个节点（< 50 行） |
| [编码规范](docs/zh_cn/develop/编码规范.md) | 写 Pipeline 或 Python 代码之前 |
| [Pipeline 说明](docs/zh_cn/develop/Pipeline说明.md) | 了解具体 Pipeline 任务链逻辑（含 Mermaid 图） |
| [Custom 说明](docs/zh_cn/develop/Custom说明.md) | 编写自定义 Action / Recognition |
| [个性化配置](docs/zh_cn/develop/个性化配置.md) | Issue 模板、格式化工具 |

## 编码规范要点

### Pipeline JSON

- **禁止无界面信息编写 Pipeline**：严禁在未向 AI 提供游戏界面截图、界面跳转逻辑等上下文的情况下，让 AI 直接编写 Pipeline。MaaFramework 的 Pipeline 强依赖游戏界面与业务逻辑，缺乏界面信息的 AI 只能依赖幻觉和项目已有代码拼凑，产出代码质量极低。充分的信息至少包括：每个识别节点需提供 `roi` 与模板图片，并说明界面间的跳转关系（从哪个界面、点击什么、跳转到何处）。不满足以上条件的 PR 将被维护者直接关闭。
- **协议合规性**：所有 Pipeline JSON 字段必须严格遵循 MaaFramework Pipeline 协议规范（见下方相关文档链接）。在新增或修改节点时，务必核对字段名称、类型及取值范围。
- **节点命名**：MaaTOT 约定前缀 `Click_` / `Swipe_` / `Flag_` / `Flag_Inverse_` / `Action_` / `Judge_`，入口节点无前缀。详见 [编码规范 §2.2](docs/zh_cn/develop/编码规范.md#22-节点命名规范)。
- **防死循环**：盲动作节点（无 `recognition` 的 Swipe/Click）使用 `max_hit` 限制命中次数，父节点 `next` 末尾追加 fallback。
- **识别驱动**：每一步操作基于识别。推荐 `识别 A → 点击 A → 识别 B → 点击 B`，禁止 `整体识别一次 → 点击 A → 点击 B → 点击 C`。
- **减少硬延迟**：优先 `pre_wait_freezes` / `post_wait_freezes`，避免 `pre_delay` / `post_delay` / `timeout`。
- **OCR 容错**：`expected` 包含常见误识别变体，支持正则。完整句无法匹配时切分或取特征字。
- **日志颜色**：Limegreen（完成）、Red（出错）、Dimgray（信息）、Orange（消极）、Deepskyblue（积极）。
- **分辨率**：所有 ROI 基于**短边 720** 归一化。
- **先复用再新增**：写新节点前先查 `utils.json` 和已有任务链。

### Python Agent

- Custom Action 入口方法 `run()`，Custom Recognition 入口方法 `analyze()`
- 参数解析使用 `utils.params.parse_params()`
- 路径使用 `pathlib.Path` 构建
- 新增模块同步更新 `__init__.py`

## 审查重点

- **禁止无界面信息编写 Pipeline**：缺乏截图/ROI/界面跳转关系的 Pipeline 代码质量极低，不满足条件的 PR 将被直接关闭。
- **禁止硬延迟**：检查是否出现了不必要的 `pre_delay` / `post_delay` / `timeout`。
- **next 覆盖率**：`next` 列表是否覆盖所有可能的预期画面，「一次截图，立即命中」。
- **坐标合法性**：所有 ROI/target 基于短边 720 基准。
- **逻辑边界**：是否处理了弹窗、加载等异常情况。
- **接口同步**：新增任务时 `interface.json` 和 `tasks/T_*.json` 是否同步更新。

## 相关协议文档

MaaFramework 协议细节请直接查阅上游文档（访问网页），本项目不重复编写：

- [任务流水线协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.1-%E4%BB%BB%E5%8A%A1%E6%B5%81%E6%B0%B4%E7%BA%BF%E5%8D%8F%E8%AE%AE.md)（Pipeline JSON 字段、算法类型、动作类型）
- [ProjectInterface V2 协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/3.3-ProjectInterfaceV2%E5%8D%8F%E8%AE%AE.md)（interface.json 配置）
- [回调协议](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/2.3-%E5%9B%9E%E8%B0%83%E5%8D%8F%E8%AE%AE.md)（focus 消息类型）
- [Custom & Agent 文档](https://github.com/MaaXYZ/MaaFramework/blob/main/docs/zh_cn/1.3-Custom%26Agent.md)（Python Agent 基础）

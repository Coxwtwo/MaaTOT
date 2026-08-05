<!-- markdownlint-disable MD033 MD041 -->

# Custom 说明

## 基础说明

一些复杂任务，用纯 Pipeline 写会很长很复杂，所以这部分任务我们用 Python 脚本自定义。

Agent 相关代码参考 [M9A](https://github.com/MAA1999/M9A)。

---

## 自定义模块一览

所有自定义代码位于 `agent/custom/` 目录下，分为两类：

| 类型 | 目录 |
| --- | --- |
| 自定义动作 (Custom Action) | `agent/custom/action/` |
| 自定义识别 (Custom Recognition) | `agent/custom/recognition/` |
| 工具函数 | `agent/custom/utils/` |

### 模块列表

| 注册名 | 类型 | 文件 | 功能 |
| --- | --- | --- | --- |
| `SmartReplenish` | Action | `smart_replenish.py` | 智能选择能量饮料（按保质期和体力缺口） |
| `DynamicOverride` | Action | `dynamic_override.py` | 运行时动态修改 Pipeline 节点配置 |
| `JudgeDailyTask` | Action | `periodic_task.py` | 每日任务周期控制（当日完成后自动跳过） |
| `JudgeWeeklyTask` | Action | `periodic_task.py` | 每周任务周期控制（本周完成后自动跳过） |
| `APCheck` | Recognition | `ap_check.py` | 体力值 OCR 识别与阈值比较 |

---

## 自定义动作 (Custom Action)

`agent\custom\action`下存放了基于 MaaFramework 自定义动作接口实现的逻辑决策模块。

---

## SmartReplenish (智能补给能量饮料)

负责在补给弹窗内根据实时库存和缺口，智能选择最优能量饮料进行单次饮用。

### 1. 功能概述

- **逻辑驱动执行**：内部通过 `context.run_task()` 调用 Pipeline 节点来完成具体点击动作。为了确保精确点击，动作会在执行前动态覆盖目标节点的 `roi`。
- **饮料使用逻辑**：采用"保质期优先"原则。会对比并识别到期时间（单位：小时 > 天），优先饮用最快过期的饮料，不论其体力面值大小。若保质期相同，则根据体力缺口选择最合适的面值。
- **动态定位**：使用模板匹配实时寻找能量饮料图标。只要匹配到图标即判定为剩余数量至少为1。

### 2. 适用范围

- **使用情景**：仅适用于游戏内的 **"体力补充"弹窗界面** 。
- **条件**：需要 Pipeline 中已定义的 `Click_60体力饮料` 和 `Click_30体力饮料` 等节点。

### 3. 输入参数 (JSON 传入)

配置在节点的 `custom_action_param` 字段中：

- `ap_threshold` (int): **[选填]** 补给的目标体力阈值。默认值：`0`。

### 4. 输出结果 (返回逻辑)

- **Success (True)**：成功饮用一瓶饮料。
- **Failure (False)**：体力已达标，或所有能量饮料已耗尽。

### 5. 内置配置 (代码硬编码)

以下配置硬编码在代码中，**无法**通过参数修改：

- **搜索区域**：固定为体力数值的 OCR 识别区域 `[380, 339, 180, 80]` ，饮料图标的搜索区域 `[54, 562, 597, 224]`。
- **识别偏移**：
  - `c_off`: 库存数字区域相对于图标左上角的偏移量。
  - `e_off`: 保质期区域相对于图标左上角的偏移量。

### 6. 使用方法示例

本动作不在任务链中添加或修改，而是在任务配置中覆盖 pipeline 配置。如果当前体力不足 90 ，将智能选择一瓶能量饮料并触发饮用动作。

```json
"pipeline_override": {
    "Action_智能策略补充": {
        "custom_action_param": {
            "ap_threshold": 90
        }
    }
}
```

---

## DynamicOverride (通用动态覆盖)

用于在运行时动态修改 Pipeline 的节点配置，解决任务流转过程中的状态干预需求。

### 1. 功能概述

- **内存覆盖**：通过 `context.override_pipeline()` 修改当前上下文中的节点配置。
- **状态切换**：可用于在补足体力后动态禁用某个任务入口节点。

### 2. 适用范围

- **使用情景**：适用于需要在脚本运行中**动态改变后续执行流**的场景，如补满体力后临时关闭检查开关。
- **限制**：覆盖仅对当前任务实例生效，重启 Agent 后会恢复初始配置。

### 3. 输入参数 (JSON 传入)

配置在节点的 `custom_action_param` 字段中：

- `target_node` (string): **[必填]** 目标节点的唯一名称。
- `override_content` (object): **[必填]** 要覆盖的 JSON 配置。

### 4. 输出结果 (返回逻辑)

- **Success (True)**：成功应用覆盖指令。
- **Failure (False)**：参数解析失败。

### 5. 使用方法示例

利用动态覆盖机制禁用"体力检查"节点：

```json
"Action_禁用体力检查": {
    "action": "Custom",
    "custom_action": "DynamicOverride",
    "custom_action_param": {
        "target_node": "体力检查",
        "override_content": {
                "enabled": false
            }
        },
    "next": [
        "Click_取消"
    ]
}
```

---

## JudgeDailyTask (每日任务周期控制)

用于控制每日任务的执行频率，确保同一任务在每天只执行一次。通过持久化时间戳来判断当天是否已完成。

### 1. 功能概述

- **周期判断**：在 `config/maatot_data.json` 中按 `task_key` 存储上次执行的时间戳（毫秒）。
- **自动跳过**：如果当天（以 `reset_hour` 为分界）已执行过，则通过 `context.override_next()` 清空当前节点的 `next` 列表，后续流程自然终止。
- **首次执行**：如果是首次执行或新的一天，记录当前时间戳并允许任务继续沿 `next` 流转。

### 2. 适用范围

- **使用情景**：适用于任何**每日只需执行一次**的任务入口，如每日签到、每日领取奖励等。
- **条件**：需要可写的 `config/maatot_data.json` 文件。建议以 `_daily` 结尾命名 `task_key`。

### 3. 输入参数 (JSON 传入)

配置在节点的 `custom_action_param` 字段中：

- `task_key` (string): **[必填]** 任务的唯一标识键。不同任务使用不同的 key。建议以 `_daily` 结尾。
- `timezone` (string): **[选填]** 时区，默认 `"Asia/Shanghai"`。
- `reset_hour` (int): **[选填]** 每日刷新时刻（小时），默认 `5`（即 05:00）。

### 4. 输出结果 (返回逻辑)

- **Success (True)**：始终返回成功。
  - 当天未执行：保留 `next` 列表，后续节点正常执行。
  - 当天已执行：清空 `next` 列表，任务入口被跳过。

### 5. 数据存储

时间戳存储在项目根目录的 `config/maatot_data.json` 中，格式为：

```json
{
    "sweetheart_daily": 1719500000000,
    "affection_daily": 1719500001000
}
```

### 6. 使用方法示例

在专属甜心任务入口挂载每日周期判断。若今天已完成，后续流程被跳过；若今天未完成，则继续执行：

```json
"专属甜心": {
    "next": [
        "Judge_专属甜心_Daily"
    ]
},
"Judge_专属甜心_Daily": {
    "action": "Custom",
    "custom_action": "JudgeDailyTask",
    "custom_action_param": {
        "task_key": "sweetheart_daily"
    },
    "next": [
        "Click_甜心",
        "[JumpBack]返回主界面"
    ]
}
```

---

## JudgeWeeklyTask (每周任务周期控制)

用于控制每周任务的执行频率，确保同一任务在每周只执行一次。与 `JudgeDailyTask` 逻辑类似，但周期分界以周为单位。

### 1. 功能概述

- **周期判断**：在 `config/maatot_data.json` 中按 `task_key` 存储上次执行的时间戳（毫秒）。
- **自动跳过**：如果本周（以 `reset_weekday` + `reset_hour` 为分界）已执行过，则通过 `context.override_next()` 清空当前节点的 `next` 列表。
- **首次执行**：如果是首次执行或新的一周，记录当前时间戳并允许任务继续。

### 2. 适用范围

- **使用情景**：适用于任何**每周只需执行一次**的任务入口，如周常副本、周任务等。
- **条件**：需要可写的 `config/maatot_data.json` 文件。建议以 `_weekly` 结尾命名 `task_key`。

### 3. 输入参数 (JSON 传入)

配置在节点的 `custom_action_param` 字段中：

- `task_key` (string): **[必填]** 任务的唯一标识键。不同任务使用不同的 key。建议以 `_weekly` 结尾。
- `timezone` (string): **[选填]** 时区，默认 `"Asia/Shanghai"`。
- `reset_weekday` (int): **[选填]** 周几刷新，`0`=周一 ... `6`=周日，默认 `0`（周一）。
- `reset_hour` (int): **[选填]** 刷新时刻（小时），默认 `5`（即 05:00）。

### 4. 输出结果 (返回逻辑)

- **Success (True)**：始终返回成功。
  - 本周未执行：保留 `next` 列表，后续节点正常执行。
  - 本周已执行：清空 `next` 列表，任务入口被跳过。

### 5. 数据存储

与 `JudgeDailyTask` 共享 `config/maatot_data.json` 文件，通过不同的 `task_key` 区分任务：

```json
{
    "sweetheart_daily": 1719500000000,
    "trial_sanctuary_weekly": 1719586400000
}
```

### 6. 使用方法示例

在试炼神殿任务入口挂载每周周期判断：

```json
"试炼神殿": {
    "next": [
        "Judge_试炼神殿_Weekly"
    ]
},
"Judge_试炼神殿_Weekly": {
    "action": "Custom",
    "custom_action": "JudgeWeeklyTask",
    "custom_action_param": {
        "task_key": "trial_sanctuary_weekly"
    },
    "next": [
        "Click_试炼神殿",
        "[JumpBack]返回主界面"
    ]
}
```

---

## 自定义识别 (Custom Recognition)

`agent\custom\recognition`下存放了基于 MaaFramework 自定义识别接口实现的逻辑模块。

---

## APCheck (体力值判定)

`APCheck` 用于从游戏界面的指定区域识别当前的体力数值，并将其与预设的阈值进行比较，从而决定是否需要触发能量饮料补给流程。

### 1. 功能概述

- **数值提取**：自动读取如 "75/120" 等格式的文字，并提取当前的实时体力。
- **稳健性**：内部会自动合并所有 OCR 文本块，解决因字号差异导致的文本切分问题。
- **逻辑判断**：该识别器纯粹负责"数值判断"，不执行操作。

### 2. 适用范围

- **使用情景**：仅适用于 **"体力补充"弹窗界面** ，需要确保弹窗已打开。

### 3. 输入参数 (JSON 传入)

配置在 Pipeline 节点的 `custom_recognition_param` 字段中：

- `ap_threshold` (int): **[必填]** 所需的最低体力目标值。

### 4. 输出结果 (返回逻辑)

该识别器通过返回 `AnalyzeResult` 与框架通信：

- **命中 (Success)**：当 `当前体力 < ap_threshold` 时。返回一个虚拟坐标盒 `[0, 0, 1, 1]`，触发 Pipeline 节点的 `next` 链路执行补给。
- **未命中 (Failure)**：当 `当前体力 >= ap_threshold` 时。返回 `None`，不进入节点。

### 5. 使用方法示例

本动作不在任务链中添加或修改，而是在任务配置中覆盖 pipeline 配置。若 `APCheck` 判定当前体力低于 90，则会触发 `Action_智能策略补充` 进入补给流程：

```json
"pipeline_override": {
    "Action_智能策略补充": {
        "custom_action_param": {
            "ap_threshold": 90
        }
    }
}
```
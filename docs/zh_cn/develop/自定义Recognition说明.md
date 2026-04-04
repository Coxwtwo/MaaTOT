# 自定义识别 (Custom Recognition) 说明文档

`agent\custom\recognition`下存放了基于 MaaFramework 自定义识别接口实现的逻辑模块。

---

## StaminaCheck (体力值判定)

`StaminaCheck` 用于从游戏界面的指定区域识别当前的体力数值，并将其与预设的阈值进行比较，从而决定是否需要触发能量饮料补给流程。

### 1. 功能概述

- **数值提取**：自动读取如 "75/120" 等格式的文字，并提取当前的实时体力。
- **稳健性**：内部会自动合并所有 OCR 文本块，解决因字号差异导致的文本切分问题。
- **逻辑判断**：该识别器纯粹负责“数值判断”，不执行操作。

### 2. 适用范围

- **使用情景**：仅适用于 **“体力补充”弹窗界面** 。
- **条件**：需要确保弹窗已打开且体力数值在指定的 ROI 范围内。

### 3. 输入参数 (JSON 传入)

配置在 Pipeline 节点的 `custom_recognition_param` 字段中：

- `threshold` (int): **[必填]** 所需的最低体力目标值。无默认值。

### 4. 输出结果 (返回逻辑)

该识别器通过返回 `AnalyzeResult` 与框架通信：

- **命中 (Success)**：当 `当前体力 < threshold` 时。返回一个虚拟坐标盒 `[0, 0, 1, 1]`，触发 Pipeline 节点的 `next` 链路执行补给。
- **未命中 (Failure)**：当 `当前体力 >= threshold` 时。返回 `None`，不进入节点。

### 5. 内置配置 (代码硬编码)

以下配置硬编码在代码中，**无法**通过参数修改：

- **识别引擎**：强制使用 `run_recognition_direct` 调用 `JRecognitionType.OCR`。

### 6. 使用方法示例

该示例展示了如何在任务开始前插入体力判定。若 `StaminaCheck` 判定当前体力低于 90，则会触发 `Action_智能策略补充` 进入补给流程：

```json
"Flag_体力判断": {
    "recognition": "Custom",
    "custom_recognition": "StaminaCheck",
    "custom_recognition_param": {
        "threshold": 90
    },
    "roi": [ 380, 339, 180, 80 ],
    "next": [ "Action_智能策略补充" ]
}
```

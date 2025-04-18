## 基础说明

`assets/resource/base` 存放官服资源。

`assets/resource/bilibili` 存放B服资源。

程序运行时会读取相应目录中所有的 json 格式文件，将任务划分到不同 json 文件中只是为了开发时容易阅读和理解。

**要注意的是，无论选择哪个客户端，程序都会先读取 `assets/resource/base` 中的文件，再读取相应目录中的文件。**

**如果有重复任务，`assets/resource/base` 中的内容会被覆盖。但只有任务中相同字段的内容会被覆盖，其余字段的内容会保留。**

由于不同客户端往往只有启动和关闭时的任务有区别，所以大部分功能代码我们存放在 `assets/resource/base` 中。

以下是各个文件的大致说明：

 - [startup.json](#startup) 启动游戏客户端。
 - [shutdown.json](#shutdown) 关闭游戏客户端。
 - [领取邮件.json](#领取邮件) 领取邮件奖励。
 - [领取友谊徽章.json](#领取友谊徽章) 领取友谊徽章。
 - [专属甜心.json](#专属甜心) 包含专属甜心自动制作服饰。制作家装的功能还没写。
 - [逸梦.json](#逸梦) 只有领取花露的功能，遇到花露收集满的情况会退出。
 - [进修副本.json](#进修副本) 复盘进修副本。
 - [异常副本.json](#异常副本) 复盘异常副本。为了方便使用，在`interface.json`中设置角色材料、印象材料和思绪残影三种任务入口。
 - [utils.json](#utils) 包含一些常用的功能, 如返回主界面、关闭奖励弹窗、点击自动剧情键等。
 - [my_task.json](#my_task) 是一个任务流水线 demo ，在实际开发中不使用，仅是方便开发者理解 Pipeline 的执行次序。

文档[使用颜色](Colors.html)是可视化界面的日志文字颜色。

## <span id="startup">startup.json</span>

### `StartUp`

启动 App 的入口任务。

```mermaid
flowchart LR
    n0["StartUp"] -->|next| n1["Flag_主界面任务<br>(位于主界面)"]
    n0 -->|next| n2["MihoyoSlogan<br>(应用启动页)"]
    n0 -.->|interrupt| n3@{ shape: processes, label: "各种退出取消键"}
    n3 -.-> n0
    n0 -.->|interrupt| n4["StartTOT<br>(启动APP)"]
    n4 -.-> n0
    n2["MihoyoSlogan<br>(应用启动页)"] -->|next| n5["StartApp"]
    n5 -->|next| n6["点击进入"]
    n5 -->|next| n7["Flag_更新版本"]
    n5 -.->|interrupt| n8@{ shape: processes, label: "各种Loading页面"}
    n8 -.-> n5
    n5 -.->|interrupt| n9["Click_下载确定"]
    n9 -.-> n5
    n5 -.->|interrupt| n05["Click_官服接受协议"]
    n05 -.-> n5
```

```mermaid
flowchart LR
    n6 -.->|interrupt| n12["Flag_TipsLoading"]
    n12 -.-> n6
    n6 -.->|interrupt| n13["Click_点击进入"]
    n13 -.-> n6
    n6["点击进入"] -->|next| n10["领取登录奖励"] 
    n6 -->|next| n11["关闭广告弹窗"]

    n10["领取登录奖励"] -->|next| n11
    n10 -.->|interrupt| n14@{ shape: processes, label: "各种退出取消键"}

    n11["关闭广告弹窗"] -->|next| n15["位于思绪界面"]
    n11 -.->|interrupt| n16["Click_主界面思绪"]
    n16 -.-> n11
    n11 -.->|interrupt| n17["Click_过期资源确定"]
    n17 -.-> n11
    n15 -->|next| n18["返回主界面"]
```

### `关闭广告弹窗`

功能是关闭广告弹窗。

广告弹窗形状多变没有一致的的关闭按钮，但都不会遮盖主界面底端的功能按钮，所以点击底端**思绪**按钮关闭弹窗。

因为每次点击后会短暂出现正常主界面，识别主界面的元素难以判定广告是否全部关闭，所以一直点击**思绪**按钮，直到打开思绪界面，程序识别到思绪界面顶端的**思绪整理**才停止点击。

## <span id="shutdown">shutdown.json</span>

### `CloseTOT`

功能是关闭 App ，通常不做更改。

## <span id="领取邮件">领取邮件.json</span>

### `领取邮件`

领取邮件的入口任务。

## <span id="专属甜心">专属甜心.json</span>

```mermaid
flowchart LR
    n0["专属甜心"] -->|next| n1@{ shape: processes, label: "Click_甜心(两种状态)"}
    n0["专属甜心"] -.->|interrupt| n5["返回主界面"]
    n5 -.-> n0
    n1 -->|next| n2["Click_剪刀"]
    n2["Click_剪刀"] -->|next| n3["选择图纸"]
    n3["选择图纸"] -->|next| n6@{ shape: processes, label: "Click_选择第X行制作中图纸"}
    n3["选择图纸"] -->|next| n7["Click_选择第一张图纸"] 
    n3["选择图纸"] -->|next| n8["具体制作步骤"] 
    n3["选择图纸"] -->|next| n9@{ shape: processes, label: "Flag_Inverse_第X行可制作图纸"}
    n9 -->|next| n10["Click_返回主界面键"] 
    n6@{ shape: processes, label: "Click_选择第X行制作中图纸"} -->|next| n11["Click_开始制作"] 
    n6 -->|next| n8["具体制作步骤"]
    n7["Click_选择第一张图纸"] -->|next| n11["Click_开始制作"] 
    n11["Click_开始制作"] -->|next| n8["具体制作步骤"] 
```

### `Click_选择第一行制作中图纸`

`next`列表里必须有`具体制作步骤`，因为夏彦完成步骤的按钮颜色，与图纸黄色进度条颜色相同，识别到`Click_选择第一行制作中图纸`时也可能在夏彦的图纸具体制作步骤页面。


```mermaid
flowchart LR
    n8["具体制作步骤"] -->|next| n14["Flag_蜜意甜心值不足"] 
    n8["具体制作步骤"] -->|next| n15["Flag_Zero蜜意甜心值"]
    n8["具体制作步骤"] -->|next| n16["Click_甜心自动剧情"]
    n8["具体制作步骤"] -.->|interrupt| n17["Click_具体制作步骤"]
    n17 -.-> n8
    n8["具体制作步骤"] -.->|interrupt| n18["Flag_自动制作中"]
    n18 -.-> n8
    n14["Flag_蜜意甜心值不足"]  -->|next| n10["Click_返回主界面键"] 
    n15["Flag_Zero蜜意甜心值"] -->|next| n10["Click_返回主界面键"]
    n16["Click_甜心自动剧情"] -->|next| n19["Click_关闭甜心奖励弹窗"] 
    n16["Click_甜心自动剧情"] -.->|interrupt| n20["Flag_自动剧情开启中"]
    n20 -.-> n16
    n19["Click_关闭甜心奖励弹窗"] -->|next| n3["选择图纸"]
```

### `Flag_自动制作中`

`expected`列表包含的候选项不用删，因为每个男主的界面里这个自动按钮的位置不一样（马哈鱼快出来挨打），而且字体颜色与背景颜色相近，有时就是会识别出奇怪的文字。

## <span id="逸梦">逸梦.json</span>

```mermaid
flowchart LR

```

### `Swipe_收取花露第X行` 

(之前我不知道可以滑动收集，是先识别四位男主的逸梦，再分别匹配四位男主的花上四角星，不仅收集不全还可能因为背景长得像花上四角星而卡住，现在用七个横向滑动来收集花露，简单又好用。以后还要是要好好听小初代说话啦ヾ(×∧×)ノ)

## <span id="utils">utils.json</span>

```mermaid
flowchart LR

```

## <span id="进修副本">进修副本.json</span>

```mermaid
flowchart LR
    n0["进修副本"] -->|next| n1["Click_事件簿_进修"]
    n0 -.->|interrupt| n2["返回主界面"]
    n2 -.-> n0
    n1 -->|next| n3["Click_进修"]

    n3 -->|next| n4["Click_进入进修副本<br>(在interface中<br>设定对应副本)"]
    n3 -->|next| n5["Flag_进修副本<br>列表最下端"]
    n3 -.->|interrupt| n6["Swipe_向上滑动<br>寻找进修副本"]
    n6 -.-> n3

    n5 -->|next| n4["Click_进入进修副本<br>(在interface中<br>设定对应副本)"]
    n5 -->|next| n7["Flag_进修副本<br>列表最上端"]
    n5 -.->|interrupt| n8["Swipe_向下滑动<br>寻找进修副本"]
    n8 -.-> n5
    n7 -->|next| n07["返回主界面"]
```

```mermaid
flowchart LR
    n4["Click_进入进修副本"] -->|next| n9["Click_进入进修关卡<br>(在interface中<br>设定对应关卡)"]
    n4 -->|next| n10["Flag_该副本<br>今日未开启"]
    n10 -->|next| n11["Click_取消消耗<br>晶片开启副本"]
    n11 -->|next| n011["返回主界面"]
    
    n9 -->|next| n12["Click_复盘进修关卡"]
    n12 -->|next| n13["Flag_复盘确认弹窗"]
    n12 -->|next| n14["Flag_体力不足弹窗"]
    n12 -->|next| n15["Flag_使用工作证页面"]

    n13["Flag_复盘确认弹窗"] -->|next| n16["Click_复盘X次确定<br>(在interface中设定次数)"]
    n13["Flag_复盘确认弹窗"] -->|next| n17["Flag_复盘次数最小"]
    n13 -.->|interrupt| n18["Click_复盘次数减号亮"]
    n18 -.-> n13
    n16["Click_复盘X次确定<br>(在interface中设定次数)"] -->|next| n19["Click_复盘结束"]
    n17 --->|next| n07["返回主界面"]
    n19 -->|next| n07["返回主界面"]

    n14["Flag_体力不足弹窗"] -->|next| n20["Click_取消喝饮料"]
    n20 --->|next| n07["返回主界面"]
    n15["Flag_使用工作证页面"] -->|next| n21["Click_取消使用工作证"]
    n21 --->|next| n07["返回主界面"]
```

## <span id="异常副本">异常副本.json</span>

```mermaid
flowchart LR
    n0["异常副本"] -->|next| n1["Click_事件簿_异常"]
    n0 -.->|interrupt| n00["返回主界面"]
    n00 -.-> n0
    n1 -->|next| n3["Click_主线"]
    n3 -->|next| n4["Flag_In异常"]
    n3 -->|next| n5["Click_异常"]
    n4 -->|next| n6["Click_主线<br>换篇章按钮"]
    n5 -->|next| n6
    n6 -->|next| n7["Click_选择<br>主线篇章<br>(在interface中<br>设定对应篇章)"]
    n7 -->|next| n8["Click_选择<br>主线篇章确认"]
```

```mermaid
flowchart LR
    n8["Click_选择<br>主线篇章确认"] -->|next| n9["Click_进入异常副本<br>(在interface中<br>设定对应副本)"]
    n8 -->|next| n10["Flag_异常副本<br>列表最下端"]
    n8 -.->|interrupt| n11["Swipe_向上滑动<br>寻找异常副本"]
    n11 -.-> n8

    n10 -->|next| n9["Click_进入异常副本<br>(在interface中<br>设定对应副本)"]
    n10 -->|next| n12["Flag_异常副本<br>列表最上端"]
    n10 -.->|interrupt| n13["Swipe_向下滑动<br>寻找异常副本"]
    n13 -.-> n10

    n12["Flag_异常副本<br>列表最上端"] -->|next| n012["返回主界面"]
    n12 ~~~ n09

    n9 -->|next| n14["Click_进入异常关卡<br>(在interface中<br>设定对应关卡)"]
    n9 -->|next| n15["Flag_异常关卡<br>列表最下端<br>(在interface中设定<br>对应最下端关卡)"]
    n9 -.->|interrupt| n09["Swipe_向上滑动<br>寻找异常关卡"]
    n09 -.-> n9

    n15 -->|next| n14
    n15 -->|next| n16["Flag_异常关卡<br>列表最上端"]
    n15 -.->|interrupt| n015["Swipe_向下滑动<br>寻找异常关卡"]
    n015 -.-> n15
    n16["Flag_异常关卡<br>列表最上端"]-->|next| n012["返回主界面"]
```

```mermaid
flowchart LR
    n14["Click_进入异常关卡"] -->|next| n17["Click_复盘异常关卡"]
    n17 -->|next| n18["Flag_复盘确认弹窗"]
    n17 -->|next| n19["Flag_体力不足弹窗"]
    n17 -->|next| n20["Flag_剩余次数不足"]

    n18["Flag_复盘确认弹窗"] -->|next| n21["Click_复盘X次确定<br>(在interface中设定次数)"]
    n18["Flag_复盘确认弹窗"] -->|next| n22["Flag_复盘次数最小"]
    n18 -.->|interrupt| n23["Click_复盘次数减号亮"]
    n23 -.-> n18
    n21["Click_复盘X次确定<br>(在interface中设定次数)"] -->|next| n24["Click_复盘结束"]
    n24 -->|next| n012["返回主界面"]

    n19["Flag_体力不足弹窗"] -->|next| n25["Click_取消喝饮料"]
    n25 --->|next| n012["返回主界面"]
    n20["Flag_剩余次数不足"] -->|next| n26["Click_取消使用<br>晶片重置次数"]
    n26 --->|next| n012["返回主界面"]
```

## <span id="使用颜色">使用颜色</span>

**普通提示** <font color=#696969>昏灰 Dimgray #696969</font>

**任务失败** <font color=#FF0000>红色 Red #FF0000</font>

**任务完成** <font color=#32cd32>柠檬绿 Limegreen #32cd32</font>

**消极类提示** <font color=#FFA500>橙色 Orange #FFA500</font>

**积极类提示** <font color=#00BFFF>深天蓝 Deepskyblue #00BFFF</font>

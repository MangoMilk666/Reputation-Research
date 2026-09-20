# Prior Test Refactor Plan

## 目标与适用范围

本计划用于重构 `prior-test` 的开发顺序。核心原则是先验证 LLM 能在已定义的单期收益任务中使用私人信号，再识别其是否会根据信息源历史表现调整对社会信息的权重。未通过前一阶段的门槛，不进入后一阶段，也不运行完整样本。

当前 `v2` 的 `G+ / G- / L+ / L-`、持仓盈亏和价格路径不再作为声誉机制的默认背景；它们将在最后作为明确的稳健性情境变量重新引入。

## 统一运行与数据要求

所有阶段保持同一 CLI 入口和运行闭环：生成试验、调用模型、逐 trial 落盘、汇总、分析和绘图均由一次 `prior-test run` 执行；已完成运行可由 `prior-test analyze` 重新生成分析结果。阶段差异只通过配置文件及其 `protocol_version` 表达，不另建交互方式。

建议的运行形式为：

```bash
.venv/bin/prior-test run \
  --config configs/refactor_<stage>.json \
  --output data/runs/refactor/<stage>/<run-id>
```

- 每个阶段使用独立配置和独立输出目录；不得覆盖或混入 `v1`、`v2` 或其他阶段的结果。
- 每次运行必须保存 manifest、完整 system prompt、每个公开 prompt、原始模型响应、解析后的 decision、分析产物和基于相应阶段测试指标构建的图表。
- trial 完成后立即落盘；未完成运行可保留已完成 trial，但不得与后续运行自动拼接。
- 每个公开 prompt condition 应记录 prompt hash、模型名与版本、采样参数、seed、阶段和 context blocks。只有模型实际可见的信息才可进入 prompt hash。
- 后续阶段只能复用已经通过门槛的模型与上一阶段的固定任务核心；任何改动均需新建配置与输出目录。

## 阶段 0：测量与样本结构审计

### 设计目的

确认一次 trial 的公开输入、随机化、落盘和分析单位一致，避免将不可见条件的重复或不可复现采样误解为行为证据。

### 设计内容

- 不引入新的经济或社会信息条件；使用阶段 A 的最小任务作为审计对象。
- B0 没有 source，因此不得按不可见的 source direction、source history 或其他 source latent variable 重复展开。
- 每个重复调用使用不同且被记录的 seed；相同公开 prompt 的重复仅用于测量模型随机性，不得伪装为新的实验条件。
- 公开 prompt 不得展示 `G+ / G- / L+ / L-` 等研究者标签。
- 检查 JSON 解析、失败重试、逐 trial 落盘、prompt hash 和分析分母是否一致。

### 通过门槛

- 每条 decision 都能追溯到唯一的公开 prompt、配置、seed 和原始响应。
- B0 的设计表中不存在 source 维度造成的伪重复；分析时的有效样本数与公开 prompt condition 数、重复数完全可解释。
- 完成 trial 的 decision 记录在进程正常中断后仍可读取；重新分析不改变原始 decision。
- 小样本审计中无系统性 JSON 解析失败、漏写或重复计数。

### 编码指导原则

- 确保编码时注释语言为中文。

- 将“模型可见 condition”和“研究者内部标签”分开建模；后者不得影响 prompt 渲染或 public-condition 去重。
- seed 必须从 CLI/config 到模型请求全链路传递，并写入 trial record。
- 为 scenario、prompt、decision 和 analysis 建立可验证的一一对应关系；测试应覆盖 B0 去重和中断后重分析。

## 阶段 A：私人信号基础能力

### 设计目的

验证模型是否理解对称的单期收益规则，并能在没有社会信息和个人交易背景时，依据私人信号作出双向交易选择。

### 逐渐加入的设计内容

仅向模型提供：

- 当前执行价 100；终值仅可能为 UP=110 或 DOWN=90；先验各为 50%。
- BUY 与 SELL 各一单位、均可立即执行、无费用、均可行。
- 相对于维持当前组合不变的明确增量收益表：UP 时 BUY 为 +10、SELL 为 -10；DOWN 时 BUY 为 -10、SELL 为 +10。
- 私人信号方向（UP 或 DOWN）及可靠度（保留 `q=0.65`、`q=0.85`）。
- 结构化的 `BUY` / `SELL` 输出要求。

不得提供 portfolio、cost basis、unrealized gain/loss、own trading history、all-time high/low、source action 或 source history等信息。

`q=0.65` 和 `q=0.85` 都大于 0.5；在本阶段的二元、风险中性规则下，它们不应改变最优 action。因此 q 用于验证模型是否正确读取字段，并为阶段 C 保留相对可靠度比较，不作为本阶段 action 必须随 q 改变的假设。

### 通过门槛

- 对每个 q，`private UP -> BUY` 和 `private DOWN -> SELL` 的比例均至少为 80%，且使用不同 seed 的最小重复数为每格 20。
- 两个镜像方向均有有效行为空间：不得出现所有私人信号条件均选择同一 action 的饱和现象。
- 所有完成响应均满足结构化输出要求；行动方向在独立小批次中稳定。

若未通过，停止增加任何 context 或 reputation 条件，先修订最小任务表述、模型模板或模型选择。

### 编码指导原则

- 确保编码时注释语言为中文。

- 将终值、先验、收益表和私人信号实现为不可选的核心任务模块，避免在后续阶段复制或改写数学规则。
- 将 prompt 组织为“任务与收益规则”后接“私人信息”；不在 prompt 中加入未定义的风险偏好、止盈止损或一般交易建议。
- 分析必须按 private direction、q、模型和 seed 组别报告 action rate，而非只给总体 BUY/SELL 比例。

## 阶段 B：个人情境的逐块消融

### 设计目的

识别究竟哪一类个人交易背景会改变阶段 A 已验证的私人信号决策，防止复合的价格路径和盈亏线索重新触发 SELL saturation。

### 逐渐加入的设计内容

保持阶段 A 的终值、先验、收益表和私人信号完全不变。每次只增加一个 context block，并始终保留没有该 block 的阶段 A 对照：

1. 中性 portfolio：现金与可卖库存均充足，成本价等于当前价，未实现盈亏为零。
2. cost basis 与 unrealized gain/loss：正、零、负盈亏单独操纵，不与 ATH/ATL 捆绑。
3. all-time high/low：单独加入过去价格范围，不改变成本价或未实现盈亏。
4. own trading history：单独加入过去订单记录，不同时加入新的价格路径叙事。
5. 经上述单块检验后，才测试预先定义的组合状态；`G+ / G- / L+ / L-` 仅作为研究者分层标签，不展示给模型。

不得增加 source 信息。禁止使用“现金不足时必须 SELL”或“库存不足时必须 BUY”等强制行动警告；所有生成的状态必须让 BUY 与 SELL 在 trial 前均可行。

### 通过门槛

- 每加入一个 block 后，仍满足阶段 A 的两个方向各至少 80% 的私人信号一致率，且不出现 action saturation。
- 若某 block 使结果恶化，先在该 block 内做最小化定位（字段、数值范围、措辞），不得继续与后续 block 组合。
- 只有所有被保留的 block 均通过后，才确定阶段 C 的共同 context；未通过的 block 移至阶段 D 的探索性稳健性检查。

### 编码指导原则

- 确保编码时注释语言为中文。

- context 应以可独立开关、可单独渲染的模块实现；禁止通过一个 `reference_price_state` 字符串同时隐式决定成本、盈亏和 ATH/ATL。
- scenario schema 分别记录每个经济字段及其来源，使同一数值状态可被重建和验证。
- 为每个 context block 添加设计不变量测试：价格范围合法、持仓和现金允许双向交易、成本与未实现盈亏的计算一致。

## 阶段 C：声誉信息通道识别

### 设计目的

在已通过的最小共同 context 中，检验 source 的历史表现是否会改变模型对其当前方向信息的权重，而非测量默认 BUY/SELL 行为。

### 逐渐加入的设计内容

- 先加入 B1：私人信号加 source 当前方向，但无历史；B0 仍为无 source 对照。
- 再加入 H60、H80、H90：历史长度、格式、正负结果呈现和当前 source direction 均保持一致，仅历史正确率不同。
- 主识别版本将 source 当前信息定义为对本期终值的自主方向判断（directional prediction），而非可能由仓位、流动性或约束驱动的可执行订单；它不是命令或投资建议。
- private/source direction 独立且平衡。主分析限定 conflict cells，并平衡两个镜像格：`private UP + source DOWN` 与 `private DOWN + source UP`。
- agreement cells 仅用于理解与稳健性检查，不用于估计 source 的边际信息权重。
- 待主识别版本通过后，才将真实 `source executable order` 作为外部有效性扩展；该版本需明确该订单并非被迫交易，并重新单独报告。

### 通过门槛

- conflict cells 中，source=BUY 与 source=SELL 两个镜像方向均不得饱和；每个方向的 source-following rate 应保留可识别的变化空间（建议介于 20% 与 80%）。
- 合并镜像 conflict cells 后，`H90 - H60` 的方向为正，且预先设定的 bootstrap 95% 区间下界大于 0；若未达到此门槛，不扩展至完整情境设计。
- 相对可靠度的方向应与离线 Bayesian comparator 一致：在 conflict 中，source 的历史可靠度相对 private q 更高时，跟随 source 的概率应更高；不要求模型逐点复现理论概率。
- B1 仅作为无历史社会信息控制，不预设其必须位于 H60 和 H90 之间。

### 编码指导原则

- 确保编码时注释语言为中文。

- 将 source 的“当前方向含义”与“历史正确率证据”定义为同一信息通道；避免一处称预测，另一处暗示其只是仓位调整。
- B0、B1、H60、H80、H90 必须共用除 source block 外完全相同的公开上下文和 trial 生成规则。
- 分析默认报告 conditional source-following rate：按 signal relation、source direction、private direction、q、treatment 分层；总体比例不得替代镜像条件结果。
- 预先固定主 estimand、bootstrap 单位和无效响应处理规则，避免在看到完整结果后变更标准。

## 阶段 D：情境稳健性与完整设计

### 设计目的

在声誉信息通道已经可识别后，检验个人盈亏、价格路径、信息呈现顺序和真实订单表述是否调节 reputation-sensitive imitation。

### 逐渐加入的设计内容

- 逐项恢复阶段 B 中通过或需复核的 context blocks，包括 G+/G-/L+/L- 所代表的组合状态。
- 将 information-block order 作为明确、平衡的实验因素，而非默认但未报告的 prompt 顺序。
- 加入 directional prediction 与 executable order 两种 source 表述的比较。
- 只有在各单项调节均可解释后，才运行完整的多因素平衡设计及跨模型比较。

### 通过门槛

- 每个新增情境中仍满足阶段 C 的双向非饱和要求。
- 主声誉效应在预先指定的核心 context 中保持正向且可识别；任何异质性均以交互效应报告，不以总体平均值掩盖。
- 完整样本规模由阶段 C 的效应大小、方差和预先指定的精度目标决定；不得因单一小样本结果直接恢复 4,800-trial 设计。

### 编码指导原则

- 编码时注释语言依然为中文。

- 将阶段 C 的核心 protocol 冻结为版本化基线；阶段 D 仅以显式 factor 扩展，不修改核心收益函数、signal 生成或主分析定义。
- 完整 factorial 生成前加入平衡性、可行性、prompt 去重和 treatment 等价性测试。
- 图表必须同时显示总体结果、source direction 镜像结果、context 分层结果及有效样本数。

## 推进纪律

- 每阶段先运行小规模校准样本，再依据本文件门槛决定是否进入下一阶段；不以增加重复次数替代设计诊断。
- 每个阶段结束时，将配置、运行命令、通过/未通过结论和下一步决定写入该阶段输出目录的简短运行说明。
- `v1` 与 `v2` 结果仅作为历史诊断证据保存，不删除，不能与 refactor 阶段的数据合并估计。
- 若同一模型在阶段 A 的最小任务中持续失败，应停止为该模型增加 prompt 修补，在返回的文本中通知用户，转向其他候选模型或重新界定可研究的行为结果。
- 每完成一次编码更新，需要为用户返回推荐的git commit msg,格式如下:

```txt
type(scope): commit
e.g. refactor(phaseB): add neutral portfolio condition for test
```


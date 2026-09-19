# Reputation 对 LLM trader 决策的影响：Micro prior test 指导方案

编制日期：2026-09-19。范围：proposal 的 Phase 0，服务于后续 Phase 1 的假设冻结与模型适用性判断；本轮不实施宏观市场实验。

## 1. 研究目标与核心判断

你的研究不是一般性的“LLM 是否从众”，而是：**当 receiver 的私人信号与一个可识别 source 的当前交易方向冲突时，仅改变该 source 的历史可靠性证据，是否会改变 receiver 跟随它的概率？** 正式关注的是 history-inferred reputation，而不是提示词直接告诉模型“此人声誉很高”。

建议将本次 prior test 理解为探索性 pilot，而非贝叶斯意义上的 prior distribution 测试。它要回答四个问题：

1. 所选模型是否理解私人信号、历史记录与 BUY/SELL 的经济含义？
2. 不提供 reputation 标签或准确率汇总时，模型是否能从逐条历史记录中提取并使用 source reliability？
3. 该效应是否跨买卖方向、私人信号强度、历史样本及有限提示词变体保持稳定？
4. 哪组信息强度能形成可测但不过度饱和的反应，值得进入独立的正式 micro experiment？

**工程结论：PAMS 不能开箱即用完成这项 prior test，但你也不需要从零实现整个 agent-market-data-visualization 系统。** 首选独立 Python decision-probe harness：自己编写研究专属的历史生成、context、LLM 调用与实验记录层，复用现成验证、统计与绘图库。当前不需要订单簿；未来若进入市场实验，再用适配器接入 PAMS。

### 1.1 必须收窄的理论表述

- 本设计操纵的是**他人的能力声誉/信息可信度**。Scharfstein–Stein 式为了维护**自身**职业声誉而模仿涉及不同的激励机制；当前没有经理考核、相对绩效惩罚或公众评价，不能声称直接检验了它。
- 依据更可靠的 source 调整行动可能是合理的 Bayesian social learning。发现跟随效应，并不自动证明 irrational herding 或 behavioral bias；要声称过度跟随，必须先给出明确的信息结构与规范性基准。
- 提供外生历史后看到行动变化，支持“从给定证据形成并使用可信度”。它尚不等于声誉在多轮交互中内生形成，也不证明具有人类心理机制。
- source 是脚本生成的实验刺激，不需要再运行一个 LLM；receiver 才是被测 LLM。多个独立调用也不等于多个独立的人类受试者。
- prior test 不检验 H2，不用收益、价格发现或暂时错价来反推 H1。

## 2. 如何借鉴 Hashimoto，如何避免照搬

依据用户提供的 Hashimoto et al. (2026) PDF：

| 已核实的原文事实 | 对本研究的启示 |
| --- | --- |
| §3.1 / Algorithm 1 是单 agent、单次决策的 loss-aversion probe | 支持先验证局部决策机制的路线，但不是本研究的 reputation 处理 |
| §3.2 / Algorithm 2 / PDF pp.8–9 的 herd experiment 有 20 个 agent、3 个 session，每种设置 30 个不同 seed 的 trials | 其 herd micro 本身有交互，不应描述为所有 micro 都是独立单次问答 |
| Base、OFI、leader-board 三种设置；榜单呈现前三名交易者的当前财富与最近订单方向 | 与本题相近，但没有把单一 source 当前方向固定后单独操纵历史正确率 |
| §4 将 LLM 决策方向与订单定价等部分分离，使用 PAMS 做市场模拟 | 可以借鉴决策与执行分层；无需搬入 FCN 权重或宏观参数 |
| Appendix A / PDF p.21 包含 OFI 含义、持仓、未实现损益等上下文 | 不能原样复用：会引入锚定、损失厌恶及额外社会信息 |
| Data availability / PDF p.23 说明代码框架与实验配置可向通讯作者合理请求；生成数据不公开分享 | **公开 PAMS 不等于该论文的实验代码**；本次核查未确认可直接下载的完整作者复现包 |

本方案采用固定情境的单次决策，属于为因果隔离而设计的新 micro protocol，不是声称精确复现 Hashimoto。论文只作为方法依据，不将其中给 agent 的指令当成本次用户指令。

## 3. 最小实验环境

### 3.1 任务与收益

用一个虚构单资产、一期结算、无价格反馈的交易任务。建议参数：

| 项目 | 固定设定 |
| --- | --- |
| 当前成交价格 | 100 |
| 到期价值 | UP 时为 110，DOWN 时为 90；事前各 50% |
| 初始状态 | cash=1000，inventory=10；所有条件相同 |
| 决策 | 主实验：BUY 一单位 / SELL 一单位；附加诊断：加入 HOLD |
| 手续费与冲击 | 均为 0；订单保证按 100 成交 |
| 目标 | 最大化这一次决策相对于保持原仓位的期望增量收益 |
| 增量收益 | BUY：V−100；SELL：100−V；HOLD：0 |
| 私人信号 | UP 或 DOWN；准确率 q=0.65 或 0.85 |
| source 当前行动 | 与私人信号相反；BUY 表示 source 判断 UP，SELL 表示判断 DOWN |
| 历史 | source 过去 20 次同类型、已结算独立任务的方向与真实结果 |

BUY/SELL 都可行，SELL 不要求卖空。初始持仓只是确保可执行，评价的是增量收益，避免模型因当前总持仓风险改变方向。不要加入购入成本、历史最高价、未实现损益、OFI、新闻或排行榜。

主实验采用 BUY/SELL 二元动作，以保持与 Hashimoto 的 herd micro 实验可比，并使“跟随 source”与“跟随私人信号”互斥且易解释。HOLD 不放入主 estimand：它可能代表不确定、风险规避、任务误解或格式策略，而不代表社会信息权重。另设小规模 HOLD 诊断块，检查二元强迫选择是否人为制造 imitation；诊断结果不与主实验合并。

### 3.2 明确信息边界

模型可见：任务规则、q、私人信号、source ID、当前方向，以及本条件允许的历史。

模型不可见：当前真实到期价值、当前 source 是否正确、研究假设、treatment 名称、历史正确率汇总、分析标签和其他条件的输出。使用白名单 renderer，从 `public_context` 生成 prompt；不要直接序列化完整实验对象。

每次调用重置上下文，无跨 trial memory、反思、工具搜索或当前结算反馈。这里研究的是从**提供的记录**推断可信度，不是跨 session 记忆能力。

### 3.3 私人信号准确率与冲突抽样

q 是信息生成机制的校准参数：在总体任务中，私人信号以 q 的概率符合真实状态。选取 source/private 冲突状态后，冲突子样本中的实际准确率不必仍等于 q。不能一边固定冲突和当前真假配额，一边把样本命中率解释为自然市场准确率。

本 pilot 以条件决策为对象，主指标不依赖当前真实状态。当前 outcome 如需保存，只在隐藏层固定，并在同一情境的所有 treatments 共享；也可以对同一决策分别计算 UP 与 DOWN 的潜在收益，无需为不同隐藏真假重复调用完全相同 prompt。若未来评价无条件收益，须另建按完整信息生成过程自然抽样的实验。

不要将 `source_correct/incorrect` 作为本轮额外可见处理：那会直接泄漏答案，也不是 reputation。

## 4. Treatment 与控制变量设计

### 4.1 五组主设计

| 分析代码（仅研究者可见） | 给模型的信息 | 用途 |
| --- | --- | --- |
| B0 | 私人信号，无 source 当前行动或历史 | 私人信号理解与基线方向偏好 |
| B1 | 私人信号 + source 当前行动，无历史 | action-only 基线 |
| H60 | B1 + 20 条历史，其中 12 条正确 | 较低但仍正向的信息可靠度 |
| H80 | B1 + 20 条历史，其中 16 条正确 | 中间强度及剂量反应 |
| H90 | B1 + 20 条历史，其中 18 条正确 | 较高可靠度 |

主比较：H90 − H60。辅助比较：H80 与两端、各历史组与 B1、B1 与 B0。删除 E-high/E-low：它们把研究问题改成“是否服从显式标签”，不能回答 history-inferred reputation；若未来需要提示词 sanity check，应放在独立开发诊断而非正式 treatment。

H60 不采用 20% 或 30% 正确率，原因是稳定的反向指标也有信息价值，会混淆“不值得跟随”与“应反向利用”。低于 50% 的历史可作为单独的反向学习扩展，不是第一轮主设计。

B0 中不存在被观察的 source，故只报告私人信号一致率；分析者可用对应 source 方向做编码参照，但不能称其为真实 imitation。

### 4.2 配对原则

一个 `scenario_cell` = 一个历史家族 × 一个私人信号强度 × 一个方向。该 cell 中五个处理共享资产、状态、source identity、当前方向、规则、模型、模板和采样参数，只有预先声明的信息字段不同。

| 变量 | 控制方式 |
| --- | --- |
| LLM | 固定完整模型版本/权重 revision、服务后端、推理预算、token 上限 |
| persona/system prompt | 完全相同，不设置“谨慎/激进/爱模仿”等人设 |
| q | 仅按预设 0.65/0.85 分层；同 cell 不变 |
| 方向 | 每个家族制作严格 BUY/SELL、UP/DOWN 镜像 |
| 历史长度 | H60/H80/H90 都是 20 条，时间跨度、字段、记录排序规则一致 |
| 历史表现量纲 | 只用方向命中，不混入财富、收益幅度、杠杆、交易次数 |
| 当前 source 行动 | 同 cell 固定，不由另一个随机 LLM 实时决定 |
| ID | 中性编号，如 trader_17；编号与高低历史的分配无系统关联 |
| 上下文与格式 | 相同字段次序及模板；历史处理不出现 high/low、score 或 accuracy 汇总 |
| 执行 | 固定价格、数量、费用与可行性；无撮合反馈 |
| 请求顺序 | 在小批次内随机交错五组，避免模型服务随时间变化与 treatment 重合 |
| 随机性 | 分离 scenario、history、request-order、inference、bootstrap seeds |

有历史与无历史不可能同时保留完全相同的有效内容长度，因此 H90−H60 是最干净的识别比较；历史组与 B1 的差异同时包含“提供历史记录”的影响。需要时加等长、明确与当前 source 无关的记录对照，不把无意义 padding 当作完全解决长度混淆。

### 4.3 历史生成方法

建议先生成并人工抽查 24 个不同 `history_family`，每个家族形成 H60/H80/H90 三份配对记录：

1. 每条记录包括 `period, source_action, realized_direction`；不直接写 correct/incorrect，也不计算分数给模型。
2. 同一家族各 treatment 的 realized_direction 序列完全相同，20 条中 UP/DOWN 各 10 条。
3. source 历史 BUY/SELL 各 10 条。通过成对调整历史预测方向，使正确数分别为 12、16、18，避免高历史只是“经常 BUY”的代理。
4. 各组可固定最近两条为一对相同的正确/错误记录，并让家族间随机交换末条正确与错误，减少最新记录主导。生成器必须检验约束可满足；不得静默放宽。
5. 正确位置、连续成功长度和错误间隔在多个家族间随机化并保存。不同正确数下无法让所有 streak 统计都完全一致，不要声称只改总正确率就自动控制了全部路径特征。
6. 对每个家族制作方向镜像，配对分析时仍视为同一 cluster，而非额外独立历史家族。
7. 一个预先登记的顺序稳健性检查可在保持记录集合不变时重排记录；显著 recency sensitivity 应作为结果报告。

历史是与当前同类任务中的、完整且经过验证的记录，没有只披露成功交易；source 行动表达其方向判断，而不是对冲或被迫平仓。否则正确率不是可识别的能力指标。说明 receiver/source 的信号在给定真实方向和 source 固定能力后独立，防止共同新闻的重复计权。

### 4.4 Private signal 的生成规则（借鉴 Hashimoto 的核心方法）

private signal 不是“你的正确行动是 BUY/SELL”的命令，而是一条关于未来基本面结果的不完全可靠线索。研究者先生成隐藏的未来状态 `Z∈{UP, DOWN}`，再按固定可靠度 `q` 生成 receiver 的 signal：以 q 的概率 signal 与 Z 一致，以 1−q 的概率反向。source 的当前行动也由一个独立、同样定义的方向信号生成，并在冲突 cell 中固定为 receiver signal 的相反方向。模型只看到 signal，不看到 Z；研究者才知道每条线索最终是否正确。

具体实现可采用 Hashimoto 式结构化 analyst report，而不是裸露标签：报告包含同一模板下的若干观察（例如 earnings surprise、需求趋势、成本压力和不确定性），这些观察由 `Z` 与随机噪声生成，最后映射为 UP-leaning 或 DOWN-leaning report。开发阶段应验证模型能稳定读出方向；正式实验冻结模板、字段顺序、长度范围和噪声规则。若使用简化 JSON signal，也必须把 `direction` 解释为“线索指向”，而不是“应执行的动作”。

所有 treatment 使用同一套 `Z → report` 生成器、同一 q 分层和同一 source/private 冲突抽样；reputation treatment 只改变 source 的过去记录。不能让 H90 获得更清晰、更长或更接近真值的 private report，也不能让某一 setting 的 hidden Z 更常与 signal 一致。每个 scenario 的完整 hidden state、生成 seed、signal 质量和 source correctness 都写入研究者表，不能进入 prompt。

## 5. Prompt 与 LLM agent 实现

### 5.1 最小 agent 定义

本轮 agent 只需要一个无状态策略接口：

```python
class DecisionPolicy:
    def decide(self, public_context) -> Decision:
        # Render a fixed prompt, call the frozen model, validate the response.
        # Do not implement a rule mapping history accuracy to the decision.
        ...
```

交易约束由确定性程序检查；历史证据如何影响行动留给 LLM。

不添加“若 source accuracy > q 则跟随”的条件分支，那是后面的规范性 comparator，不是被测 agent。

### 5.2 Hashimoto 式 system prompt、占位符与 context 注入

以下模板应作为所有主 treatment 共用的**冻结 system prompt**。它先定义每个字段的经济含义、信息边界和输出规则，再由程序把一个具体 trial 的 context 注入到 `{{...}}` 占位符中。不要把整段 prompt 手工拼接，也不要让 treatment 名称或研究者计算的声誉分数进入模板。

```text
(Premise) You are a trader in a controlled single-period stock-market
decision experiment. Make one order decision using only the information
provided below.

(Task) Choose BUY or SELL for one unit. BUY means purchasing one unit at
the current market price. SELL means selling one unit already held in the
portfolio. Short selling and cash deficits are not allowed. Both actions,
when feasible, execute at the stated current price and have no fee.
Your objective is to maximize expected incremental payoff relative to
keeping the current portfolio unchanged. The terminal fundamental value is
unknown to you when you decide.

(Field definitions)
- current_price is the price at which the one-unit order executes.
- cash and inventory describe your current feasible portfolio. They are
  constraints, not signals about the terminal value.
- terminal_value_UP and terminal_value_DOWN are the two possible terminal
  fundamental values. The labels UP and DOWN describe the future state;
  they do not tell you which state will occur.
- prior_probability_UP is the experimenter's prior probability of UP.
- private_signal is an imperfect analyst-style clue about the future state.
  Its directional implication is evidence, not an instruction. Its stated
  reliability is the probability that this clue agrees with the future
  state in the data-generating process; the clue can be wrong.
- source.current_action is the current BUY or SELL direction chosen by an
  identifiable other trader. It is social information, not a command.
- source.history contains that trader's past directional predictions and
  the subsequently realized UP or DOWN states. Each record is complete;
  infer reliability from the records yourself. Do not assume that the
  history is summarized by a score.

(Information boundary) The future terminal state is hidden. Do not assume
  that the private signal or the source is correct in the current period.
  Do not invent information, use information from another trial, or infer
  the researcher's treatment label. The source's past record concerns the
  source identified by source.id only.

(Information for this decision)
asset_id: {{asset_id}}
current_price: {{current_price}}
terminal_value_UP: {{terminal_value_UP}}
terminal_value_DOWN: {{terminal_value_DOWN}}
prior_probability_UP: {{prior_probability_UP}}
cash: {{cash}}
inventory: {{inventory}}
private_signal:
  report: {{private_report}}
  directional_implication: {{private_direction}}
  reliability: {{private_reliability}}
source:
  id: {{source_id}}
  current_action: {{source_current_action}}
  history:
{{source_history_rows}}

(Answer format) Return exactly one JSON object with one property:
{"action": "BUY"}
or
{"action": "SELL"}
Do not add a reason, explanation, markdown, or any other property.
```

`{{source_history_rows}}` 由程序渲染为完整的 20 行，例如 `period: 1; prediction: BUY; realized_state: UP`。B0 删除整个 `source` 块；B1 保留 source 的 `id` 与 `current_action`，删除 `history`；H60/H80/H90 注入同长度、同格式但正确次数不同的历史。所有 treatment 保留同一字段定义和同一解释文本；只允许 context 数据块发生预先声明的变化。B0/B1 也应保留相同的空字段占位结构，或在 protocol 中固定“省略字段”的规则，不能一组用自然语言、一组用 JSON。

具体 context 在请求前由 renderer 注入，形成最终 user message；system prompt、字段定义、输出 schema 和占位符顺序保持不变。示例最终 context：

```text
asset_id: SYNTH_1
current_price: 100
terminal_value_UP: 110
terminal_value_DOWN: 90
prior_probability_UP: 0.5
cash: 1000
inventory: 10
private_signal:
  report: "Demand is weakening, but the evidence is noisy."
  directional_implication: DOWN
  reliability: 0.65
source:
  id: trader_17
  current_action: BUY
  history:
    period: 1; prediction: BUY; realized_state: UP
    period: 2; prediction: SELL; realized_state: UP
    ... 18 additional rows ...
```

这里的 `terminal_value_UP/DOWN` 是任务规则，不是当前真实答案；真实状态 `Z` 不得渲染。`private_report` 应由同一 signal generator 产生，不能因为 H60/H80/H90 而改变措辞清晰度、长度或可靠性。`private_direction` 仅表示线索指向，不是“正确行动”。

### 5.3 输出与诊断分离

主任务只输出 action。JSON Schema：object，唯一必填键 `action`，枚举 BUY/SELL，禁止额外键。不要要求长篇思维过程，也不要在交易前问“此人声誉如何”，以免把构念主动提示给模型。reason 不进入主任务输出：它会增加 token、暴露事后合理化叙述，并可能把模型引向“解释声誉”而不是做决策。若需要理解性证据，使用独立、预先标记的诊断调用或在主任务后追加一个不影响 action 的短 reason 字段；reason 只能作探索性编码，不能作为主要因变量。

另用独立调用、单独诊断集测试：历史记录正确次数、私人信号含义、现金/持仓可行性。可信度估计或简短理由可以单独采集作探索性证据，但自述不能作为机制成立的主要证据。诊断调用数单独计入成本。

### 5.4 模型组合与异常规则

- 首轮不把 GPT、Llama、Qwen、Grok 等模型作为同一实验中的 treatment，也不做“谁更好”的横向比较。先选一个可锁定版本作为主模型；模型选择依据是结构化输出、版本可冻结、推理预算和本地/服务可用性，而不是模型排行榜。若预算允许，第二个或第三个本地开源模型只做完整 protocol 的外部稳健性复制：独立 manifest、独立结果、相同 seeds/场景，不能把模型身份放进主回归。
- 本地开源模型可以帮助降低成本、提高可复现性，但要记录量化方式、checkpoint、推理框架、上下文长度、采样实现和硬件。Grok 等仅能在有稳定、可记录接口时纳入；不要为了“模型多样性”混用无法冻结的服务。
- 若后端支持，开发时可用 temperature=0.2、top_p=1 作为起点；不支持的参数不能伪记录为已设置。冻结实际 sampling policy 和 reasoning budget。
- 温度 0 的重复确定性输出不构成新增行为信息；更多相同请求不能替代更多情境家族。提高温度只为适合的采样方案，不为追求显著性。
- 网络/限流故障最多两次退避重试，保持请求内容和参数；记录每个 attempt。若调用结果不确定，不将重发当新增独立 trial。
- 主任务的格式错误、拒答、截断不通过“请认真考虑声誉”重问。保留为 invalid，另报失败率；HOLD 在主任务中是非法输出，在附加 HOLD 诊断块中才是合法行动。
- 请求缓存仅用于恢复已完成的同一 trial；不同 replicate_id 的独立抽样不能共用回答缓存。

## 6. 实验规模、执行顺序与成本

以下数值是建议的 feasibility 配置，不是已有统计功效保证。

### A. 开发与 smoke test（不进入冻结数据）

使用与正式 pilot 不同的 2 个开发历史家族 × 2 个方向 × 2 个 q = 8 个 cells；5 个条件、每个条件 2 次，共 **80 次交易调用**。另做至少 20 次任务理解/历史计数诊断。

检查输入可读性、schema、q 理解、两方向可行性、隐藏变量泄漏、provider 参数与失败日志。修订模板后重新编号；不得混合版本后仅报告有效的一版。

### B. 冻结后的主要 pilot

24 个新历史家族 × 2 个方向 × 2 个 q × 5 个条件 × 5 次独立采样 = **2,400 次交易调用**。

分析单位有三个层级：24 个历史家族、96 个 scenario cells、2,400 条响应。主要不确定性按历史家族处理，不能宣称有 2,400 名独立交易者。样本不足时优先增加历史家族，而非把同一 prompt 重复数无限增加。

### C. 有限稳健性与 source-specific 诊断

- HOLD 诊断块：从主要 pilot 的 8 个开发 cells 和 8 个新 cells 中抽取配对情境，保持同样的五组 treatment、模型和 signal 生成规则，只把 action schema 扩展为 BUY/SELL/HOLD；每 cell 每 treatment 2 次即可。它的目的只是测量 abstention 是否改变主结论，不增加主样本的 estimand。
- 一套语义等价的新 wording，在 12 个新家族 × 2 方向 × 2 q × H60/H80/H90 × 5 次采样上运行：**720 次**。若预算允许，可另用第二个固定模型重复同样方案；分别计费，分别报告。
- 同一批 12 个家族上，把 H60/H90 历史明确归属于不参与当前行动、且能力独立的另一位 trader_B，当前行动仍来自 trader_A：12 × 2 × 2 × 2 × 5 = **480 次**。使用前一项 720 次 wording 检查中的同一家族、同一 wording、同一 q/方向下的 H60/H90 作为“历史属于当前 source”的配对参照；除归属 ID 与必要说明外保持相同。若不做 wording 检查，应另增加这 480 次相关 source 参照调用。若无关交易者历史同样强烈影响行动，source-specific 解释变弱。
- 上述两个模块均做时，冻结交易调用总数为 **3,600**；加开发 80 次为 3,680 次，另加理解诊断与网络故障重试。source attribution 对照属于机制诊断，不替代主比较。

### D. 冻结下一阶段

本次 pilot 所有响应均不并入后续 confirmatory micro experiment。根据效应大小、cluster 方差与成本规划新样本量，冻结主比较、prompt、模型、排除规则及 smallest effect of interest；正式实验重新生成历史家族和调用。

### 成本核算

先测真实 prompt token 与响应 token。费用 = Σ(input_tokens × input_unit_price + output_tokens × output_unit_price)，单位保持一致；推理 token、缓存和失败调用按服务实际账单计入。不要把一次 conversation 当一个 agent 的永久实例来估价。

例如 4,560 次调用、每次约 1,200 输入和 30 输出 token，仅作容量示例约为 547.2 万输入、13.68 万输出 token，不是实测或报价。先用 smoke test 的实测长度替换。固定最大请求数和总费用；并发应遵守服务限制，且每个批次含交错的 treatments。

## 7. 收集什么数据

推荐 JSONL 保存不可变请求/响应，Parquet 保存分析表，manifest 保存配置。小规模不必上 PostgreSQL 或复杂 agent 框架。

| 数据层 | 必需字段 |
| --- | --- |
| 实验 manifest | experiment_id、阶段、创建时间、协议版本、代码 commit、依赖锁文件 hash、停止规则 |
| 情境 | history_family_id、scenario_cell_id、方向、q、source_id、资产状态、隐藏 outcome（若使用） |
| 处理 | treatment_id、history_length、研究者计算的正确数、history_hash、当前 source action、归属 ID |
| 请求 | trial_id、replicate_id、模板版本、完整最终 prompt 或路径、prompt_hash、随机化顺序、批次 |
| 推理配置 | provider、完整 model_id/revision、服务 fingerprint（可用时）、temperature/top_p、预算、seed 支持情况 |
| 原始响应 | raw response、parsed action、provider request_id、finish_reason、token usage、延迟、时间戳 |
| 故障 | attempt_id、错误类别、重试次数、validation_error、是否计费、最终有效性 |
| 派生指标 | follow_source、follow_private、hold、signal_conflict、action_payoff_by_state、分析纳入标记 |

`history_correct_count`、`treatment_id`、hidden outcome 等只能在研究者表中，不能渗入 prompt。API key 不属于实验数据，不写入请求日志。记录 model version 不等于保证后端完全可复现，应说明 seed 和服务版本的实际限制。

数据关系：manifest → histories/scenarios → trial requests → attempts/responses → derived decisions → figures/report。先存原始输出，再解析；支持断点续跑，但不能覆盖原始失败。

## 8. 指标、统计和解释

### 8.1 预先指定的主要指标

冲突条件中，对每条有效响应定义：

- `follow_source = 1(action == source_action)`。
- `follow_private = 1(action == private_signal_implied_action)`。

主实验中两者在有效响应中和为 1。分别报告各处理的比例，避免把方向偏好误当作声誉效应。HOLD 诊断块另报三动作比例。

主 estimand 是在预先定义的历史家族、q 和镜像方向分布上平均的：

`Δ_history = P(follow_source | H90) − P(follow_source | H60)`。

先对每个 cell 的重复采样取平均，再对同家族的方向/q 等权平均，再平均家族差。不要因为某个 cell 多重试、某个方向有效输出较多而给它更大权重。

辅助指标：H80 的中间位置、H90−B1、H60−B1、q 分层效应、BUY/SELL 不对称、无关 source 的高低差、失败率；HOLD 诊断单独报告。二元主实验中“反对私人信号”才等于跟随 source，但仍按 source action 显式编码。

这里估计的是配对情境间的响应概率差，不能称每个 trial 都观察到了同一个人的真实“转向”。如需严格的 pre/post switch 指标，应另设实验；把模型自己之前的回答带入后问会引入承诺和锚定效应。

### 8.2 不确定性与失败响应

主要区间：以 `history_family_id` 为 cluster 做 paired bootstrap，例如 5,000 次；每次重采样整组家族，保留所有方向、q、treatment 和重复响应。24 个 clusters 仍有限，区间用于 pilot 判断，不是精确人口推断。报告家族级散点，避免只有一根总体柱状图。

可选的 logistic/GEE 或分层模型作为辅助，控制 q、方向并包含 treatment×q；若出现完全分离，优先报告比例和区间，不强行解释不稳定的系数。主比较只有 H90−H60，其他比较以探索性区间呈现，避免多重筛选显著结果。

同时报告有效响应比例和 invalid 比例。对 treatment h，在计划调用数 N_h、有效跟随数 F_h、失败数 M_h 下，无假设跟随率界限为 `[F_h/N_h, (F_h+M_h)/N_h]`；由两组上下界计算 Δ 的保守界限。失败不应静默删除，更不能重新采样直到得到足够“合格答案”。

### 8.3 合理学习基准：不是给 LLM 硬编码行为

建议用一个**离线研究者 comparator**，帮助判断跟随是否只是合理的信息加权。假定 source 有稳定、对称正确率 θ，先验 Beta(a,b)，历史 n 次中 k 次正确，则下一次可靠度后验预测值：

`r = (a+k)/(a+b+n)`。

在 UP/DOWN 各半、当前 source/private 冲突、两者信号条件独立时：

`P(source 当前方向正确 | conflict, history) = r(1−q) / [r(1−q)+(1−r)q]`。

在对称增量收益、无交易费、风险中性的本任务里，当 r>q 时跟随 source，r<q 时跟随 private，相等时无差异。以 a=b=1 为**分析者示例假设**，三种历史的 r 为 13/22≈0.591、17/22≈0.773、19/22≈0.864。因此 q=.65 与 .85 分层能够检查不同信息强度下的切换。

这个 prior 并非模型自然持有的已知先验。若 prompt 没有规定 source ability prior，则偏离这条基准不能直接叫 irrational；先验、独立性或稳定性不同都可能解释偏差。若希望做严格的 bias 检验，另开 supplementary block，向模型明确说明完整 prior 与信息生成机制，但不提供 posterior 或决策公式，并预先登记比较标准。不要把这一补充条件与主 history-only 数据混用。

由于该 comparator 的映射被明确编程，它是理解结果的参照，不是 H1 的主要 treatment population。即使 LLM 与它完全一致，也只能支持证据敏感的学习，不能说明 LLM 必要或优于简单模型。

### 8.4 可视化交付

1. 主图：H60/H80/H90 的 source-following rate 与家族 bootstrap 区间，按 q 分面，BUY/SELL 用不同符号；B1 作参照线。
2. 配对效应图：每个历史家族的 H90−H60，显示总体估计及区间。
3. BUY/SELL 堆叠比例图，同时附 invalid 比例；HOLD 诊断另作三动作图。
4. 诊断图：history 差、无关 source 差、wording 稳健性及模型复制结果并列。

图题写明模型、prompt 版本、家族数和有效/计划调用数。不把重复响应误标为独立 agent 数量。

## 9. Go / Revise / Stop 决策

下面是可在运行前采用的工程与探索门槛，不是通用学术标准，也不是证明真实人类机制的门槛。

| 结论 | 预先采用的判据示例 | 下一步 |
| --- | --- | --- |
| 工程可用 | 总有效率≥98%，各组≥95%；理解诊断正确率≥90%；无信息泄漏或方向可行性错误 | 才解释行为差异 |
| Go：适合正式 micro | Δ_history≥10 个百分点，家族区间下限>0；两个镜像方向点估计同号；效果不只来自一两个家族；wording 下仍有同方向历史效应 | 冻结 H1 与强度，另用新数据做 confirmatory micro |
| Revise：证据不充分 | 方向合理但区间宽、对 wording/recency 强依赖、HOLD/失败率很高 | 按事先限定的修订轮数调整任务可读性，或增加新家族，不无限试 prompt |
| 仅标签有效 | Δ_label 清晰但 Δ_history 接近零或不稳定 | 只能称 cue sensitivity，不能当作 history-inferred reputation 成功 |
| 构念失败 | 无关 trader 的历史产生相近高低差，或 buy/sell 效果反向 | 检查 source identity 绑定、方向偏好和泛化正面语义反应 |
| Stop 当前实现 | 理解合格后，预定有限修订仍没有稳定历史效应 | 不进入原定 macro；报告当前模型/表示方式的否定结果 |

若效应区间同时涵盖 0 和有意义的正效应，结论是“不确定”，而不是“没有效应”。若区间很窄且上限低于预设的 10 个百分点，才有理由说在本设计下效应不足以满足工程目标。

极端的 H90 全跟随、H60 全不跟随也是历史敏感性证据，但不适合估计平滑响应曲线。此时在探索轮采用相邻正确数或新 q 校准，然后冻结；不要为让图更好看而选择性删除饱和 cells。建议最多预先允许两轮开发修订，完整保留记录。

Go 仅授权研究逻辑上进入独立正式 micro，并不等于 H2 已被支持或应立即开始大规模市场模拟。

## 10. PAMS 代码复用评估

### 10.1 本次实际检查的对象

本地路径：`/Users/henrysang/Documents/pams`。remote：`git@github.com:masanorihirano/pams.git`。检查时 commit：`4ebd4cbd8639474a833788124e5f682ae0db3d5a`；`pyproject.toml` 版本为 0.2.2。以下是该本地版本的静态代码审查，不代表所有 fork 或未来版本，也没有声称已运行本方案或完成 PAMS 接入测试。

| 需求 | 代码证据 | 复用结论 |
| --- | --- | --- |
| Agent 生命周期与下单入口 | `pams/agents/base.py`：抽象 `submit_orders(markets)`，持仓与现金及订单回调 | 可用于未来 LLM adapter；不是现成 LLM trader |
| 自定义类注册 | `samples/user_class/main.py`，`Runner.class_register` | 可以扩展，不需改写 PAMS 核心 |
| 订单与订单簿 | `pams/order.py`、`pams/order_book.py`、`pams/market.py` | 后续市场阶段复用，本 prior test 不需要 |
| 调度 | `pams/runners/sequential.py`、`pams/session.py` | 市场阶段复用；本轮使用独立批量 runner 更清楚 |
| 订单/成交/撤单事件 | `pams/logs/base.py` 中 OrderLog、ExecutionLog 等与 Logger 回调 | 后续可接自定义落盘；没有自动记录 prompt、token 和失败信息 |
| LLM / reputation 实验 | 本地 `pams`、`samples` 与依赖配置未检出对应实现 | 需新增研究层，不能改一个 config 就跑 |
| FCN 决策 | `pams/agents/fcn_agent.py` 组合 fundamental/chart/noise；访问 `get_fundamental_price()` | 不适合直接继承并保留其核心方向逻辑；可能泄漏真实基本面 |
| 分析和绘图 | examples 可参考一般市场数据流程 | reputation 指标与配对区间需自行定义，绘图库可直接复用 |

尤其要注意：PAMS 持有现金/资产状态不等于你的研究风险约束都自动得到强制执行。未来 adapter 仍须明确 BUY/SELL 的可行性、现金预留、仓位与订单上限，并做集成验证。

### 10.2 三条路线比较

| 路线 | 是否适合当前 prior test | 原因 |
| --- | --- | --- |
| 不改 PAMS，只运行已有 config | 不适合 | 缺少 LLM、history treatment、配对情境与请求记录 |
| 新建独立 micro harness，后续接 PAMS | **推荐** | 隔离信息因果效应，成本小，决策层可直接复用 |
| 立即继承 Agent，在完整 PAMS 市场跑全部实验 | 技术可行但此时不优先 | 成交、价格路径和调度会增加混淆与工程量；即使冻结市场也比直接情境调用复杂 |

因此，“不能直接用 PAMS”与“必须从零构建所有东西”不是二选一。需要自建的是**实验特有逻辑**，不是市场引擎、LLM 推理引擎、统计包与可视化引擎。

### 10.3 后续接入边界（仅保留接口，不开展 macro）

```text
Frozen scenario → ContextBuilder → DecisionPolicy → DecisionLog
                                      ↓
                         DeterministicExecutionAdapter
                                      ↓
                           PAMS Order / Market / Logger
```

日后创建 `LLMReceiverAgent(Agent)`，实现 `submit_orders(markets)`，通过白名单 ContextBuilder 调用同一 DecisionPolicy。BUY/SELL 转换成共同规则的 Order；HOLD 返回空列表。价格、数量、TTL 由确定性适配器统一处理，`runner.class_register(LLMReceiverAgent)` 注册。**不把整个 Market/Simulator 对象交给模型**，尤其不暴露真实基本面。

可先做一个未来集成 smoke test：同一固定公开状态下，离线与 PAMS adapter 生成的 prompt_hash 一致；用固定 mock decision 验证方向、订单及日志关联。只有集成通过，再考虑市场实验。本轮不必为了这项计划修改 PAMS 源码。

## 11. 工具与最小项目结构

| 模块 | 建议工具 | 是否需要自行编写研究逻辑 |
| --- | --- | --- |
| 情境与随机化 | Python、NumPy | 是：约束历史、镜像、随机请求顺序 |
| Schema 与模板 | Pydantic/JSON Schema；Jinja2 或固定 JSON serializer | 是：信息边界和模板；验证器复用 |
| LLM 推理 | 一个固定 remote API 或一个固定本地模型后端 | 只写薄 client adapter；不训练基础模型 |
| 持久化 | JSONL + Parquet，必要时 SQLite | 是：字段与 trial/attempt 关联；存储库复用 |
| 分析 | Pandas、NumPy；SciPy/statsmodels 按需 | 是：estimand 与 cluster bootstrap；统计库复用 |
| 图表 | Matplotlib 或 Plotly | 写少量专用绘图代码 |
| 校验 | pytest、mock LLM | 检验信息泄漏、历史约束、随机化及失败处理 |
| 市场 | PAMS | 当前非必要，后续复用 |

无需一开始引入 LangChain、多 agent 对话、RAG、真实行情采购或向量数据库。固定合成情境足够回答本次问题。

建议独立目录结构（设计建议，尚未创建）：

```text
reputation_micro/
  configs/pilot_v1.yaml
  prompts/system_v1.txt
  src/schema.py
  src/generate_scenarios.py
  src/render_context.py
  src/llm_client.py
  src/run_pilot.py
  src/analyze.py
  src/plot.py
  tests/test_design_invariants.py
  data/manifests/
  data/scenarios/
  data/raw/
  data/derived/
  outputs/figures/
  outputs/pilot_report.md
```

核心执行逻辑：

```python
manifest = freeze_protocol()
cells = generate_matched_cells(manifest)
requests = render_seven_conditions(cells)
validate_no_hidden_fields(requests)
validate_histories_and_mirrors(cells)
queue = randomized_interleaved_replicates(requests, repeats=5)
for trial in queue:
    raw = call_with_transport_retry(trial)  # Same trial, separate attempts
    append_raw_before_parsing(trial, raw)
    append_decision_or_invalid(trial, validate(raw))
analyze_paired_history_family_effects()
```

进入付费推理前的必要校验：历史正确数与方向计数；镜像对称；同 cell 除指定字段外一致；hidden outcome 改变不影响 prompt_hash；所有订单动作可行；mock 输出的 follow_source 编码正确；HOLD 诊断块的三动作编码正确；恢复执行不重复计数；bootstrap 不拆散家族。它们直接保护因果识别，优先于测试每一行模板实现。

## 12. 执行清单与应交付成果

1. 确认主模型、可选复制模型、预算和主任务语言；采用本文件的数值默认值或在运行前记录替代值。
2. 建立 schema、生成器和 public/hidden 分离；生成开发集，人工检查至少两组完整历史及镜像。
3. 用 mock client 检查随机化、日志、分析指标；再做 80 次开发调用和理解诊断。
4. 冻结协议与版本，生成新的 24 个家族，交错运行五组，保留全部 attempts。
5. 在不看单个 treatment 的“好看程度”的前提下按预设规模完成收集；故障按统一规则处理。
6. 输出主效应、家族区间、三动作分布、失败界限和有限稳健性分析。
7. 写出 Go/Revise/Stop 及证据；保留反常结果、方向偏好和模型局限。
8. 另写正式 micro 的冻结协议与样本量规划；不把探索性 pilot 数据并入确认性结果。

最终最小交付包应包括：`protocol/manifest`、历史与情境库、完整 prompt/response 日志、分析表、四类图、可一键重算分析的脚本、pilot report。当前文件只是研究与实施指导，**尚未调用被测模型、运行实验或产生任何实证结果**。

## 13. 核查来源

- 用户 proposal：[Capstone_Proposal_Draft_Reputation_Strategic_Imitation.md](/Users/henrysang/Desktop/Capstone-FinTech/new-ideas/Capstone_Proposal_Draft_Reputation_Strategic_Imitation.md)。本方案主要对齐其 Phase 0、Phase 1、history-only 与 model-suitability gate。
- 用户提供的 [Hashimoto et al. PDF](/Users/henrysang/Desktop/Capstone-FinTech/capstone-literature/stock-market/LLM-agents-reveal-how.pdf)，重点核查 §3、§4、Appendix A、Data availability；[正式论文页面](https://link.springer.com/article/10.1007/s42001-026-00465-4)。上文论文细节以本地全文与页面图像为据。
- [PAMS 官方仓库](https://github.com/masanorihirano/pams)、[官方 Agent 文档](https://pams.hirano.dev/en/latest/reference/agents.html)、[项目介绍](https://pams.hirano.dev/en/latest/user_guide/about.html)。功能判断优先依据本地固定 commit 的代码，而非假设 latest 文档与本地版本完全一致。
- 本地实现证据：[Agent](/Users/henrysang/Documents/pams/pams/agents/base.py)、[FCNAgent](/Users/henrysang/Documents/pams/pams/agents/fcn_agent.py)、[类注册示例](/Users/henrysang/Documents/pams/samples/user_class/main.py)、[Logger](/Users/henrysang/Documents/pams/pams/logs/base.py)、[依赖配置](/Users/henrysang/Documents/pams/pyproject.toml)。

文中 treatment 强度、样本规模、统计流程、工程门槛及 prompt 是针对本项目提出的设计建议，不是 Hashimoto 的原始设置，也不是已有实验发现。

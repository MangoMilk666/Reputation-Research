# Prior Test PRD

## 1. 目的

构建一个小规模、可复现的 decision-probe pilot，判断 LLM 是否会从 source 的逐条历史表现中推断 reputation/credibility，并在 receiver 的私人信号与 source observed order 冲突时改变跟随概率。每个决策均嵌入 receiver 自身的 portfolio、个人交易史、未实现盈亏及价格参照点，避免把外部订单呈现为脱离交易语境的强行动建议。该项目是模型适用性 gate，不是正式市场模拟，也不检验收益、价格发现或 H2。

`qwen3-8b-0919-1848` 属于 protocol v1 探索性诊断；v2 是新 protocol，不与 v1 数据合并。

## 2. 核心问题与成功标准

主 estimand 为：

`Δ_history = P(follow_source | H90) − P(follow_source | H60)`。

进入正式 micro 前，应同时满足：

- 总有效响应率 ≥98%，各 treatment ≥95%；理解诊断 ≥90%。
- `Δ_history` 达到至少 10 个百分点，cluster 区间下限大于 0。
- 在 source/private conflict cells 中，BUY/SELL 镜像方向同号，效应不由少数 history family 或单一 receiver reference-price state 驱动。
- source/private agreement、信息块顺序及 action-only B1 不显示将 source action 当命令的饱和锚定。
- wording 稳健性保持同方向；显式 reliability cue 有效而 history-only 无效时，只判为 cue sensitivity。

若区间宽或严重依赖 recency、HOLD 或单个家族，结论为 Revise；有限修订后仍不稳定则 Stop，不进入 macro。

## 3. 实验范围

每个 scenario 使用单资产、单期、无价格反馈的 BUY/SELL 决策。价格为 100，终值为 UP=110、DOWN=90。所有条件均呈现 receiver 的 cash、inventory、average cost basis、个人交易史、unrealized gain/loss、all-time high 与 all-time low；这些值彼此可复算，且 BUY/SELL 均可行。receiver 看到可靠度为 q=.65 或 .85 的私人 signal；source observed order 与 private signal 独立、完全平衡地生成，形成同等数量的 agreement 与 conflict cells。隐藏真实状态只用于研究者生成与分析，不进入 prompt。

五个条件如下：B0（receiver-state block + 私人 signal）、B1（加 source observed order）、H60/H80/H90（再加 20 条 history，分别 12/16/18 条正确）。B1 是 action-only social-information control，不称为无声誉基线。同一 history family、receiver state、private/source direction 和 q 下配对生成，只有声明的信息字段改变。

主 pilot：24 个 history family（G+/G−/L−/L+ 各 6）× 2 private direction × 2 source direction × 2 q × 5 条件 × 5 次采样 = 4,800 次调用；另设 320 次开发调用、状态理解、HOLD/wording/source attribution 等独立诊断模块。所有 pilot 数据不并入 confirmatory micro。

## 4. 交付物

- 冻结 protocol manifest、版本化 prompt 与 scenario/history 数据。
- 原始 JSONL 请求/响应日志、Parquet 分析表、失败与重试记录。
- conflict-only source-following 主图、family paired-effect 图、agreement/conflict 与 BUY/SELL 分层图、receiver-state 异质性图、失败界限与诊断图。
- 可从原始日志一键重算的分析脚本、pilot report、Go/Revise/Stop 决策。

## 5. 非目标与约束

本轮不实现订单簿、撮合、市场调度、真实行情、OFI、leader-board、RAG、多 agent 对话或跨 trial memory；不把 treatment 名称、研究者计算的准确率、hidden outcome 或 posterior 写入模型上下文。主任务只返回 `{"action":"BUY"}` 或 `{"action":"SELL"}`，不收集思维链。个人 portfolio/history 是 receiver-state block，不是额外 social-information treatment。

# Reputation-Driven Strategic Imitation in LLM-Based Financial Markets

By Henry

[TOC]



## Keywords

Large Language Model Agents; Financial Market Simulation; Reputation; Strategic Imitation; Information Economics; Social Learning; Agent-Based Modeling; Limit Order Book; Price Discovery; Multi-Agent Interaction; Micro-to-Macro Validation

大型语言模型智能体；金融市场模拟；声誉；策略性模仿；信息经济学；社会学习；基于智能体的建模；限价订单簿；价格发现；多智能体交互；微观到宏观验证

---

## Research Questions

**RQ1. How does reputation inferred from performance history affect an LLM trader’s imitation of another trader when their private information conflicts?**

**RQ1. 从历史表现中推断的 reputation，会如何影响 LLM trader 在私人信息冲突时对另一名交易者的模仿行为？**

**RQ2. How does reputation-driven imitation affect price discovery and temporary mispricing when a reputed trader’s current signal is correct or incorrect?**

**RQ2. 当高声誉交易者的当前信号正确或错误时，reputation-driven imitation 会如何影响市场的 price discovery 与 temporary mispricing？**

## Hypothesis

The following hypotheses are **working hypotheses derived from the theoretical literature rather than final preregistered hypotheses**. Before the main experiment, a small-scale prior test will be conducted using controlled decision probes. The final hypotheses, treatment intensity, and measurement thresholds will be fixed after that pilot and before the full market simulation, so that the project does not retrospectively construct hypotheses from the macro results. The prior test also serves as a **model-suitability gate for the use of LLM agents**: if the selected LLM cannot reliably infer and use reputation from behavioral history, the central justification for using an LLM as the reputation-sensitive behavioral model is weakened and the macro experiment should not proceed in its current form.

以下假设目前属于**由理论文献与研究直觉形成的 working hypotheses，而不是最终预注册假设**。正式实验前将先进行小规模 prior test，通过严格控制的 decision probes 检查历史表现是否确实能够产生稳定、可测量的 reputation-sensitive behavior。最终 hypothesis、treatment 强度与测量阈值将在 pilot 之后、完整市场模拟之前固定，从而避免根据宏观实验结果事后构造假设。该 prior test 同时也是对 **“为什么使用 LLM agents”这一建模选择的 suitability gate**：如果所选 LLM 无法稳定地从行为历史中推断并使用 reputation，那么把 LLM 作为 reputation-sensitive behavioral model 的核心理由就会明显减弱，此时不应按原设计继续推进 macro experiment。

**H1 — History-based reputation and imitation.** When an LLM trader’s private signal conflicts with another trader’s action, the probability of following the source is expected to increase with the reliability evidenced by the source’s past performance, even without an explicit reputation label or a hand-coded reputation-response rule.

**H1——基于历史表现的 reputation 与模仿。** 当 LLM trader 的 private signal 与另一交易者的行动冲突时，随着后者历史表现所体现的可靠度提高，LLM 跟随该 source 的概率预计上升；这一效应无需显式 reputation label 或预先编码的 reputation-response rule。

**H2 — Conditional market benefit and risk.** Reputation-driven imitation is expected to improve information aggregation when a high-reputation source is currently well informed, but the same mechanism may amplify correlated order flow and temporary mispricing when the source receives an incorrect or misleading signal.

**H2——声誉机制的条件性收益与风险。** 当高声誉 source 当前掌握的信息正确时，reputation-driven imitation 预计有助于加快信息聚合和价格发现；但当该 source 当前收到错误或误导性信息时，同样的机制可能提高 order-flow correlation，并放大 temporary mispricing 或延长价格恢复时间。

---

## Quick Grasp

**Why LLM agents?** Reputation-sensitive imitation is intrinsically context-dependent: a trader's response to another trader may depend jointly on its own private signal, the source's past reliability, the length and consistency of that history, the source's current action, and the current market state. Conventional agent models can represent this mechanism by specifying an explicit reputation score or weighting function, but doing so requires the researcher to predefine how reputation changes imitation—the very behavioral relationship this project aims to observe. LLM agents provide a complementary modeling approach because they can condition decisions on structured historical and social context without requiring a hand-coded reputation-to-action function. The project therefore uses LLMs not because they are assumed to be more rational or more realistic than conventional agents, but because their context-sensitive decision process makes it possible to test whether reputation-sensitive social learning can emerge from supplied evidence before that mechanism is introduced into a market simulation.

**为什么使用 LLM agents?** Reputation-sensitive imitation 本身具有明显的 context dependence：一个交易者是否跟随另一名交易者，可能同时取决于自己的 private signal、对方过去的可靠度、历史表现的一致性与长度、对方当前行动以及当前市场状态。传统 agent model 当然可以通过显式 reputation score 或 weighting function 实现这一机制，但这要求研究者预先规定“reputation 应当如何改变 imitation”，也就等于提前写入了本研究试图观察的行为关系。LLM agent 提供了一种不同的 behavioral modeling approach：它能够根据结构化的历史与社会信息形成决策，而无需事先硬编码 reputation-to-action mapping。因此，本研究采用 LLM 并不是因为假定其比传统 agent 更理性或更真实，而是因为其 context-sensitive decision process 允许研究首先检验 reputation-sensitive social learning 是否能够从给定 evidence 中形成，再研究这一已经经过 micro validation 的机制进入市场后会产生怎样的宏观信息聚合结果。

The methodological distinction is therefore **representational rather than performance-based**. A conventional reputation-aware agent can certainly be constructed, but the researcher must specify a functional form or behavioral rule that determines how reputation modifies the weight on social information. This project instead asks whether that mapping can be *elicited from context* and validated empirically. In other words, the conventional modeling question is largely “given a specified reputation-response rule, what market outcomes follow?”, whereas the present project first asks “can a context-sensitive agent form and use reputation from evidence without that response rule being hard-coded?” This narrower claim avoids treating LLMs as inherently superior to traditional agents.

因此，本研究与传统 agent modeling 的区别主要是**表示方式上的，而不是性能优劣上的**。当然可以构造一个具备 reputation 的传统 agent，但研究者需要预先指定某种 functional form 或 behavioral rule，决定 reputation 应该怎样改变 social information 的权重。本项目则把这个 mapping 本身留作待验证的行为关系：先观察它能否从 context 中被诱发并通过实验验证。换句话说，传统建模更接近“在已经给定 reputation-response rule 的情况下，市场会发生什么”，而本研究首先问的是“在没有硬编码该 response rule 的情况下，一个 context-sensitive agent 能否从 evidence 中形成并使用 reputation”。这种定位并不声称 LLM 天然优于传统 agent，而是说明它为什么适合作为本研究特定行为机制的建模工具。

This project does **not** study generic crowd-following or ask whether LLM traders herd more than conventional algorithmic traders. The object of study is narrower: **source-specific reputation as an information-economic mechanism**. A receiving trader has its own private signal and observes the current action of one identifiable trader. The current action is held constant while the source's reputation information is manipulated. The key micro-level question is whether an LLM trader rationally or heuristically changes the weight placed on another trader's action when that source has a stronger reputation.

本研究不研究泛化的“大家都在买，所以我也买”的 crowd-following，也不再把 LLM trader 与传统算法 trader 作为主要对比对象。研究对象更窄：**将 source-specific reputation 作为一种 information-economic mechanism 进行隔离和实验操纵**。Receiver trader 拥有自己的 private signal，同时观察一个可识别交易者的当前行动；在控制该行动内容不变的情况下，只改变 source 的 reputation information，观察 LLM trader 是否因为 source reputation 不同而重新分配对私人信号与外部行动的权重。

The formal experiment focuses exclusively on **history-inferred reputation**. The LLM observes standardized records of the source’s previous predictions or trades and their realized outcomes, without any precomputed reputation score or evaluative label. Matched histories differ in observed reliability while the source’s current action and the receiver’s private signal are held fixed; an action-only, no-history condition provides a baseline. Explicit reliability cues may be used as brief diagnostic probes in the prior test, but are not formal experimental treatments.

正式实验只研究 **从历史表现推断 reputation**：LLM 读取 source 过去的预测或交易及其 realized outcome，不提供预先计算的 reputation score 或评价性标签。Matched histories 只改变可观察可靠度，source 当前行动和 receiver private signal 保持不变，并设置仅展示当前行动、不展示历史的 baseline。直接给出 reliability cue 可以作为 prior test 的简短诊断，但不进入正式实验的 treatment。

The design follows a **micro-to-macro validation sequence**. First, static or short-horizon decision probes verify that reputation changes individual decisions under tightly matched numerical states. Only after a stable micro effect is established is the mechanism embedded into a limit-order-book market. The macro experiment then asks whether the same reputation-sensitive imitation improves price discovery when the reputed source is informative and becomes a source of correlated error when the source is temporarily wrong. In this way, any market-level finding is linked to an independently validated individual-level mechanism rather than inferred post hoc from a plausible-looking price path.

实验方法遵循严格的 **micro-to-macro validation sequence**。首先在静态或短时 decision probes 中，以完全匹配的 numerical state 检查 reputation 是否稳定改变个体决策；只有在确认微观行为效应后，才把该机制放入限价订单簿市场。宏观实验随后研究：当 reputed source 信息正确时，这种 reputation-sensitive imitation 是否加快 price discovery；而当 source 暂时出错时，它是否会形成相关性更强的错误订单流。这样，宏观市场结果就能够追溯到已经独立验证的微观机制，而不是仅根据“看起来像”的价格曲线反推心理原因。

The topic is related to herding, but it is not identical to the leaderboard treatment in Hashimoto et al. (2026). Their leaderboard provides information about several currently successful traders and is used as one stimulus for herding. The proposed project instead isolates **the history-inferred reputation of an identifiable source**, holds the source’s current action constant while varying observable past reliability, and tests whether the same reputational mechanism helps or harms market information aggregation depending on whether the source is currently correct. This narrower decomposition is intended to avoid simply repeating a generic herding experiment.

该选题与 herding 有关联，但不等同于 Hashimoto et al. (2026) 中的 leaderboard treatment。后者向 agent 提供若干当前高收益交易者的信息，并把它作为触发 herd behavior 的一种 stimulus；本项目则进一步隔离**单个可识别 source 从历史表现中形成的 reputation**，保持 source 当前行动不变、只改变可观察的历史可靠度，并进一步检验当 source 当前判断正确或错误时，同一种声誉机制会如何改变市场信息聚合。研究重点因此不是重复“leaderboard 会不会引起跟随”，而是拆解 reputation-driven strategic imitation 的因果链条。

---

## Literature Review

### Reputation, Strategic Imitation, and Information Economics

- **Sobel — *A Theory of Credibility* (1985).** Sobel develops a repeated-interaction model in which one party must decide whether another party is trustworthy when motives are uncertain. Credibility is built through a history of reliable behavior, and an informed party may have incentives both to accumulate reputation and, under some circumstances, to exploit it later. This motivates studying **credibility inferred from an observable record of past accuracy** and testing what happens when a historically reliable source receives an incorrect current signal.  
  **中文：** Sobel 的模型研究在动机不确定的重复互动中，一个参与者如何基于对方过去的可靠行为形成信任。声誉不是天然属性，而是通过持续提供准确、有价值的信息逐渐建立；同时，拥有声誉的一方在某些情况下也可能利用已经形成的 credibility。该理论支持本研究关注**从可观察的历史准确性中推断的 credibility**，并为“历史上可靠的 source 在某轮出错时会发生什么”提供理论基础。  
  Link: https://doi.org/10.2307/2297732

- **Scharfstein & Stein — *Herd Behavior and Investment* (1990).** This paper shows that investment imitation can be individually rational when decision makers care about how their ability will be evaluated. Managers may mimic others even when they possess substantive private information because relative performance and reputation affect incentives. The study is important for the present project because it separates imitation from simple irrational crowd-following: observed copying can arise from **reputational and strategic considerations**.  
  **中文：** Scharfstein 与 Stein 说明，投资模仿不一定意味着简单的“非理性从众”。当管理者关心外界如何评价自己的能力时，即使掌握了有价值的 private information，也可能选择模仿他人。因此，imitation 可以来自 reputation-related strategic incentives。本项目借用这一思想，将“跟随某个可信 source”与泛化的 crowd herding 区分开来。  
  Link: https://www.aeaweb.org/articles?id=10.1257/aer.80.3.465

- **Trueman — *Analyst Forecasts and Herding Behavior* (1994).** Trueman shows theoretically that analysts may issue forecasts closer to prior expectations or previously released forecasts than their private information alone would justify. This work demonstrates that professional financial judgments can become socially dependent even when individual private information exists, supporting the use of a controlled conflict between a receiver's private signal and another trader's observable action.  
  **中文：** Trueman 的研究表明，金融分析师即使拥有自己的 private information，也可能发布比其私人信息所支持的程度更接近既有市场预期或其他分析师预测的判断。该研究说明，专业金融决策可以在存在私人信息的情况下仍表现出 social dependence，为本项目设计“private signal 与 reputed source action 明确冲突”的受控实验提供依据。  
  Link: https://doi.org/10.1093/rfs/7.1.97

- **Graham — *Herding among Investment Newsletters: Theory and Evidence* (1999).** Graham develops and empirically tests a model in which an analyst's reputation, ability, public information, and signal correlation affect the probability of herding. The finding that reputation can systematically change imitation behavior is especially relevant to the proposed micro experiment, where source reputation is manipulated while the current recommendation is held fixed.  
  **中文：** Graham 构建并用 investment newsletter 数据检验了一个模型，说明 analyst reputation、ability、public information 与 signal correlation 都会影响 herding probability。该研究最直接地支持本项目的核心实验逻辑：在保持 source 当前行动不变时，单独操纵 reputation，检验 receiver 是否因此改变跟随概率。  
  Link: https://doi.org/10.1111/0022-1082.00103

### LLM Agents, Trust, and Financial Market Simulation

- **Xie et al. — *Can Large Language Model Agents Simulate Human Trust Behavior?* (NeurIPS 2024).** This work evaluates trust decisions across LLM agents using established behavioral-economic trust-game settings and reports that several LLMs exhibit systematic trust behavior, although the strength and biases vary by model and condition. It supports the feasibility of treating trustworthiness cues as controlled context variables, while also warning that trust responses are model-dependent and therefore require repeated testing rather than one-shot examples.  
  **中文：** Xie 等人使用行为经济学中的 Trust Game 系统研究 LLM agent 的信任行为，发现不同模型可以表现出稳定但存在模型差异和偏差的 trust pattern。该研究说明，把可信度相关信息作为受控 context variable 是可行的，同时也提醒本项目必须进行重复试验和 model sensitivity check，而不能把一次语言输出当成可靠行为证据。  
  Link: https://openreview.net/forum?id=CeOwahuQic

- **Hirano — *Building LLM-Based Artificial Market Simulations: Can LLMs Function as Agents in Multi-agent Simulations for Finance?* (PRIMA 2025).** Hirano introduces LLM decision-making into an artificial stock market and varies both prompt content and the proportion of LLM agents. The results show that prompt design materially changes market-level stylized facts. This study is methodologically relevant because it demonstrates that structured prompt/context interventions can be treated as experimental inputs in a reproducible artificial-market framework.  
  **中文：** Hirano 将 LLM decision-making 引入人工股票市场，并系统改变 prompt element 和 LLM agent proportion，结果表明 prompt design 会显著影响宏观 market stylized facts。该研究对本项目的方法论启示在于：context/prompt manipulation 可以作为可复现的实验 treatment，而不是仅用于生成“更像人”的交易文本。  
  Link: https://doi.org/10.1007/978-3-032-13562-9_5

- **Hashimoto et al. — *LLM Agents Reveal How Human Bias Shapes Path-Dependent Market Dynamics* (2026).** Hashimoto et al. first conduct controlled micro experiments on loss aversion and herd behavior and then introduce an LLM-guided FCLAgent into a full artificial market. Their herding experiment includes a leaderboard showing profitable traders and their recent actions, demonstrating that source-performance information can influence LLM trading decisions. This is the closest overlap with the current topic. However, reputation is not isolated as the principal treatment: the study does not isolate histories of differing source reliability while holding a single source’s current action constant, or examine market outcomes conditional on whether that source’s current signal is correct or incorrect.  
  **中文：** Hashimoto 等人先通过 micro experiment 验证 loss aversion 与 herd behavior，再将 FCLAgent 放入完整人工市场。其 herding experiment 中包含 leaderboard，向 agent 展示高收益交易者及其最近行动，说明 source-performance information 确实能够影响 LLM trading decision。这与本项目存在最直接的方法重叠，因此本研究不会把“leaderboard 能触发 herding”作为创新点，而是保持单一 source 当前行动不变，通过改变可观察历史可靠度来隔离 reputation effect，并研究该 source 当前正确/错误时的宏观后果。  
  Link: https://doi.org/10.1007/s42001-026-00465-4

The reputation and financial-herding literature establishes why credibility and reputation can alter imitation, but an implemented conventional agent must still operationalize those theories through an explicit utility specification, weighting rule, or other reputation-to-decision mapping. That is appropriate when the mapping itself is assumed. It is less suitable when the research question is whether a decision maker can *form and use* source-specific credibility from heterogeneous evidence without the researcher fixing that mapping in advance. Recent LLM-agent studies suggest that context-sensitive behavioral responses can instead be elicited and validated experimentally, which motivates using the LLM as a behavioral implementation of reputation formation rather than treating the LLM itself as the phenomenon of interest.

Reputation 与金融 herding 文献已经说明 credibility/reputation 为什么能够改变 imitation，但在真正实现传统 agent 时，研究者仍需要把这些理论操作化为显式 utility specification、weighting rule 或其他 reputation-to-decision mapping。当该 mapping 本身就是模型假设时，这种做法完全合理；但如果研究问题恰恰是“决策者能否从异构 evidence 中形成并使用 source-specific credibility，而不是由研究者提前规定这种关系”，那么预先写死 mapping 会削弱问题本身。近期 LLM-agent 研究提供了另一种可能：context-sensitive behavioral response 可以先通过实验诱发和验证，因此本研究把 LLM 作为 reputation formation 的 behavioral implementation，而不是把 LLM 本身当作研究现象。

Taken together, the reviewed literature supports three premises: reputation can rationally or strategically alter imitation in financial decision making; LLMs can respond systematically to trust-related contextual cues; and micro-level LLM behavioral mechanisms can be embedded into artificial markets. The resulting gap has both a **modeling** and a **market** component: first, whether an LLM can infer and use source-specific reputation from observable history without an explicitly programmed response function; and second, once that mechanism is validated, whether reputation-sensitive imitation improves or damages market information aggregation depending on the current accuracy of the reputed source.

综合来看，已有文献分别支持三个前提：reputation 能够系统性改变金融决策中的 imitation；LLM 对 trust/reliability context 可以产生可重复的行为响应；经过 micro validation 的 LLM behavioral mechanism 可以进一步进入 artificial market。因此，本研究的 gap 同时包含一个 **modeling question** 与一个 **market question**：第一，LLM 能否在没有显式编写 reputation-response function 的情况下，从可观察历史中推断并使用 source-specific reputation；第二，在这一机制经过 micro validation 后，当 reputed source 当前正确或错误时，reputation-sensitive imitation 会如何改善或损害市场的信息聚合。

---

## Experimental Design

### **General principle**

The study uses **context manipulation rather than different system personas**. All receiving traders use the same LLM model/version, system prompt, inference parameters, structured-output schema, market access, portfolio constraints, and decision procedure. The main experimental information enters only through standardized context fields: the receiver's private signal, the source trader's current action, and the source's reputation evidence. This separation is intended to make reputation the interpretable independent variable instead of allowing broad persona differences to alter multiple behavioral dimensions simultaneously.

本研究采用 **context manipulation，而不是不同 system persona**。所有 receiver trader 使用相同的 LLM model/version、system prompt、inference parameters、structured-output schema、市场访问权限、资产与仓位约束以及决策流程。真正变化的信息只通过标准化 context fields 输入，包括 receiver 的 private signal、source trader 的 current action，以及 source 的 reputation evidence。这样可以尽量把 reputation 保持为可解释的 independent variable，避免不同 persona 同时改变风险偏好、交易风格、语言表达和策略目标等多个维度。

The formal treatments therefore provide **behavioral history rather than explicit reputation scores**. An agent that merely reacts to a supplied reliability score would not establish the proposed LLM-specific modeling value. Here the receiver must integrate the source’s observed history, its own private signal, and the current source action without a supplied reputation label or coded weight. A no-history, action-only control isolates the additional effect of historical evidence.

因此正式 treatment **只提供行为历史，不提供显式 reputation score**。如果 agent 只是响应已计算好的可靠度数字，就不足以支持本项目的 LLM-specific 建模理由。这里 receiver 必须在没有 reputation label 或 coded weight 的情况下，把历史表现、自身 private signal 和 source 当前行动结合起来；只展示当前行动、不展示历史的 control 用于隔离历史证据产生的额外效应。

The market environment is a single-asset artificial limit-order-book market. Matching, settlement, order size bounds, position limits, and other hard constraints are implemented in deterministic code. The LLM is used for directional decisions and, where necessary, a bounded confidence score; order price and quantity should remain deterministic or sampled from a common rule so that reputation effects are not confounded by different numerical execution behavior. All experiments are repeated across multiple seeds or independent inference samples.

市场环境采用单资产 artificial limit-order-book market。撮合、结算、订单规模上限、仓位限制等 hard constraints 全部由确定性代码实现。LLM 主要负责 directional decision，并可在需要时输出受限的 confidence score；order price 与 quantity 尽量由公共确定性规则生成，避免 reputation effect 与数值执行差异混淆。所有条件均通过多个随机种子或独立 inference sample 重复运行。

### **Phase 0 — Prior Test and Hypothesis Formation**

Before the formal experiment, the project conducts a small prior test using a fixed library of numerical decision states. Each state contains a latent fundamental direction known to the experimenter, a receiver private signal with a specified reliability, and a conflicting source action. The pilot tests whether changing reputation information produces a stable change in action probability and identifies treatment intensities that are strong enough to measure but not so extreme that decisions become deterministic. The pilot is used to form and freeze the final hypotheses; its observations are not pooled into the confirmatory main experiment.

正式实验前先进行 **Phase 0 prior test**。项目构造一组固定的 numerical decision states，其中包含实验者已知的 latent fundamental direction、具有给定 reliability 的 receiver private signal，以及与该 private signal 冲突的 source action。Pilot 主要检查：改变 reputation information 是否能稳定改变 LLM 的 action probability，并选择“足够产生可测效应、但又不会让决策完全确定化”的 treatment intensity。Pilot 的作用是形成并冻结最终 hypothesis；其数据不与后续 confirmatory experiment 合并统计。

A practical pilot should include both **explicit-cue probes** and **history-only probes**. The explicit condition can begin with no reputation information, clearly high reputation, and clearly low reputation; the history-only condition presents matched performance records without evaluative labels. Directional labels should be counterbalanced—for example, half of the states use a private `BUY` signal and source `SELL` action, and the other half reverse the directions—to reduce any model-specific buy/sell bias. If explicit labels change behavior but history-only evidence does not, the project may still demonstrate prompt sensitivity, but the stronger justification for using LLMs as an endogenous reputation model would not be supported. If neither condition produces a stable effect, the topic should be reconsidered before building the full market experiment.

一个实际的 pilot 应同时包含 **explicit-cue probes** 与 **history-only probes**。Explicit condition 可以从 no reputation、clearly high reputation、clearly low reputation 三种简单条件开始；history-only condition 则提供结构匹配的历史表现记录，但不加入评价性标签。方向应进行 counterbalancing，例如一半状态为 private `BUY` / source `SELL`，另一半反转为 private `SELL` / source `BUY`，从而减少模型固有 buy/sell bias。如果 explicit label 能改变行为，但 history-only evidence 无法产生稳定效应，那么研究最多能够说明 prompt cue sensitivity，而不能充分支持“LLM 适合作为 endogenous reputation model”这一更强的建模理由。如果两类条件都没有稳定效应，则应在进入完整市场实验前重新评估选题。

### **Phase 1 — Micro-Level Reputation and Strategic Imitation Experiment**

Phase 1 tests whether receiving traders infer and use source-specific reputation from **observed performance history alone** under controlled signal conflict. All formal treatments use the same LLM and base prompt; no high/low label or precomputed reliability score is supplied. Matched history records have the same length, order, and template but differ in the proportion of historically correct predictions or trades. For a given scenario, the receiver’s private signal, market state, source identity, and source’s current action remain fixed. The formal conditions are **no history (action-only baseline), lower-reliability history, and higher-reliability history**. Directional conflicts are counterbalanced across `BUY` and `SELL`, and source histories are generated independently of the current outcome so that historical reliability is not conflated with current correctness. This design tests history-sensitive imitation without adding a separate explicit-reputation experiment.

Phase 1 在严格控制的私人信息冲突条件下，检验交易者能否**仅从可观察的历史表现**推断并使用 source-specific reputation。所有正式 treatment 均使用相同 LLM 与基础 prompt，不输入 high/low label 或预先计算的 reliability score。Matched histories 采用相同长度、排序与模板，仅历史预测或交易的正确比例不同。对于同一 scenario，receiver 的 private signal、market state、source identity 与 source 当前行动均固定。正式条件为**不展示历史（仅展示当前行动的 baseline）、低可靠度历史和高可靠度历史**。`BUY` 与 `SELL` 冲突方向进行 counterbalancing，source 历史独立于当前结果生成，避免历史可靠度与当轮正确性混淆。这样无需额外设置 explicit-reputation 正式实验，也能直接检验 history-sensitive imitation。

Primary micro metrics include: **imitation rate under signal conflict**, private-signal override rate, action-switching rate relative to a no-reputation baseline, confidence change where a bounded confidence score is collected, and a reputation-sensitivity coefficient estimated with a logistic or multinomial model. An additional calibration measure is **discrimination quality**: whether high reputation increases imitation more when the source is historically reliable than when it is historically unreliable, rather than simply making agents more socially compliant in every condition.

主要 micro metrics 包括：**imitation rate under signal conflict**、private-signal override rate、相对于 no-reputation baseline 的 action-switching rate、若收集受限 confidence score 时的 confidence change，以及通过 logistic/multinomial model 估计的 reputation-sensitivity coefficient。还应加入一个重要的 calibration measure——**discrimination quality**：高 reputation 是否主要提高对历史可靠 source 的跟随，而不是无条件提高对所有社会信息的服从程度。

### **Phase 2 — Macro Market Experiment: Reputation and Price Discovery**

After Phase 1 confirms a stable micro mechanism, the experiment embeds reputation-sensitive LLM traders into a repeated single-asset LOB market. A small number of identifiable source traders receive higher-precision private signals about an upcoming change in fundamental value, while ordinary traders receive noisier private signals. Source identities persist across rounds so that observable histories can generate endogenous reputation. The macro comparison uses observable histories only: in matched runs, receivers see the designated source’s action either **with its accumulated performance history** or **without access to that history**; no explicit reputation scores are provided.

当 Phase 1 确认稳定的 micro mechanism 后，Phase 2 将 reputation-sensitive LLM traders 放入重复运行的单资产 LOB market。少量可识别 source traders 获得关于 fundamental value 变化的 higher-precision private signal，普通 trader 获得更 noisy 的 private signal。Source identity 跨轮保持稳定，使历史交易结果能够形成 endogenous reputation。Macro comparison 只使用可观察历史：matched runs 中，receiver 要么看到 designated source 的当前行动**及其累积表现记录**，要么只看到当前行动、**无法访问历史记录**；两组均不提供显式 reputation score。

To avoid turning the study into a broad herding experiment, ordinary agents do not receive aggregate majority statistics or a leaderboard of many traders. They observe only their own private signal plus the action/history of the designated source to which they have access. This makes the social-information channel source-specific. Market fundamentals, signal precision, agent endowments, risk constraints, decision timing, order execution, and market microstructure are held fixed across matched runs.

为了避免研究重新退化成泛化 herding experiment，普通 agent 不接收 aggregate majority statistics，也不展示多个 trader 的 leaderboard；它们只观察自己的 private signal，以及其可访问的 designated source 的 action/history，从而把 social-information channel 限定为 source-specific。不同 matched runs 之间保持 market fundamentals、signal precision、agent endowments、risk constraints、decision timing、order execution 与 market microstructure 一致。

The market effect of access to reputation history is examined conditional on whether the reputed source’s **current signal is correct or incorrect**. Source quality is probabilistic rather than infallible—for example, a source may have a high long-run accuracy but still receive an incorrect current signal in some trials. This creates the economically important tension between useful reputation and reputational over-reliance. The experiment therefore does not need to force deception: occasional errors arise naturally from a fixed signal-accuracy process.

宏观实验考察 history access 的市场效应，并区分 reputed source 的**当前 signal 正确还是错误**。Source quality 应设为概率性的，而不是永远正确；例如某 source 长期 accuracy 很高，但在部分 trial 中仍会收到错误 current signal。这样可以自然构造“reputation 有助于信息聚合”与“对 reputation 过度依赖会放大错误”之间的张力，而无需额外加入欺骗行为。错误可以直接来自固定的 signal-accuracy process。

Primary macro metrics include absolute price error relative to fundamental value, time to price convergence, maximum temporary mispricing, short-horizon volatility, order-flow imbalance, action synchronization, bid-ask spread, depth/liquidity changes, trading volume, and recovery time after an incorrect high-reputation signal. A source-influence measure can also be computed as the fraction of receiver decisions that switch toward the source direction after observing its action and history.

主要 macro metrics 包括相对于 fundamental value 的 absolute price error、time to price convergence、maximum temporary mispricing、short-horizon volatility、order-flow imbalance、action synchronization、bid-ask spread、depth/liquidity change、trading volume，以及 high-reputation source 出错后的 recovery time。还可以定义 source-influence measure，例如观察 source action/history 后向 source 方向切换的 receiver decision 占比。

### **Control Variables and Statistical Analysis**

The principal controlled variables are LLM model/version, system prompt, temperature or sampling policy, private-signal format and precision, source action, market state, initial wealth and inventory, hard risk limits, order-size rule, decision frequency, matching rule, and simulation horizon. Reputation histories must contain the same number of observations and the same textual/structured template across high- and low-reputation conditions. The experiment should avoid free-form descriptions such as “this trader is brilliant,” because wording strength would become a second treatment.

主要控制变量包括 LLM model/version、system prompt、temperature/sampling policy、private-signal format 与 precision、source action、market state、initial wealth/inventory、hard risk limits、order-size rule、decision frequency、matching rule 与 simulation horizon。High/low reputation history 必须包含相同 observation 数量并采用完全一致的 textual/structured template。应避免使用“this trader is brilliant”这类带强语义色彩的自由文本，因为 wording strength 会成为额外 treatment。

Micro outcomes are analyzed using proportions, effect sizes, uncertainty intervals, and where appropriate logistic regression with scenario/run-level clustered or hierarchical structure. Macro outcomes are compared across repeated simulation runs with confidence intervals and effect sizes, and the analysis links trial-level imitation measures to price-discovery outcomes. The project should emphasize causal claims only for directly randomized context variables; the relationship between endogenous imitation intensity and macro outcomes is interpreted more cautiously unless additional mediation or ablation designs are introduced.

Micro outcome 使用比例、effect size、uncertainty interval，并在合适时使用带 scenario/run clustering 或 hierarchical structure 的 logistic regression。Macro outcome 通过 repeated simulation runs 比较分布、confidence intervals 与 effect sizes，并进一步连接 trial-level imitation measure 与 price-discovery outcome。只有直接随机化的 context variable 才适合做较强的因果解释；endogenous imitation intensity 与宏观结果之间的关系在没有额外 mediation/ablation 设计时应保持更谨慎的表述。

### **Theoretical basis**

The design combines three lines of theory: reputation and credibility in repeated interaction, strategic imitation in financial decision making, and information aggregation through market prices. The LLM is not itself the theoretical object. It is selected as a **context-sensitive behavioral modeling instrument** because it can integrate variable structured histories, conflicting private and social information, and current market context without requiring the researcher to specify the complete reputation-to-action functional form ex ante. This is a conditional modeling claim rather than an assumption of superiority: Phase 0 and Phase 1 explicitly test whether the chosen LLM actually exhibits the required history-sensitive behavior before any macro interpretation is attempted.

该设计结合三条理论脉络：重复互动中的 reputation/credibility、金融决策中的 strategic imitation，以及市场价格的信息聚合机制。LLM 本身不是理论研究对象，而是一个 **context-sensitive behavioral modeling instrument**：它能够同时整合可变的结构化历史、相互冲突的 private/social information 与当前 market context，而无需研究者事先完整指定 reputation-to-action functional form。这是一项需要被验证的建模主张，而不是“LLM 天然优于传统 agent”的假设；Phase 0 与 Phase 1 会在任何 macro interpretation 之前直接检验所选 LLM 是否真正表现出所需的 history-sensitive behavior。

---

## Technology Stack

| Tech Stack / Framework | Purpose / 用途 |
| --- | --- |
| **Python** | Core implementation for agent logic, experiment orchestration, simulation control, and analysis. / 用于 agent 逻辑、实验调度、模拟控制与分析。 |
| **PAMS** | Reusable artificial-market infrastructure, market/agent scheduling, and LOB simulation. / 复用人工市场、agent scheduling 与 LOB 基础设施。 |
| **Pydantic / JSON Schema** | Structured context, private signals, reputation histories, and schema-constrained LLM outputs. / 定义结构化 context、private signal、reputation history 与受约束的 LLM 输出。 |
| **Jinja2 / structured prompt templates** | Generate matched prompts whose only intended differences are reputation variables. / 生成除 reputation treatment 外尽量一致的 matched prompts。 |
| **vLLM / Transformers / Ollama or fixed remote API** | Serve a fixed LLM with recorded inference configuration. / 以固定模型与可记录推理参数提供 LLM inference。 |
| **NumPy + Pandas / Polars** | Process decision-, order-, and market-level data. / 处理 decision、order 与 market-level 数据。 |
| **SciPy / statsmodels** | Statistical tests, regression, confidence intervals, effect sizes, and robustness analysis. / 完成统计检验、回归、置信区间、效应量与 robustness analysis。 |
| **Parquet + SQLite/PostgreSQL** | Persist event traces and reproducible experiment metadata. / 保存事件轨迹与可复现实验元数据。 |
| **Matplotlib / Plotly** | Visualize imitation rates, reputation-response curves, price error, order flow, and recovery. / 可视化 imitation rate、reputation-response、price error、order flow 与 recovery。 |

### Details

Python is the recommended implementation language. **PAMS** should be evaluated first because it is already used in closely related artificial-market studies and reduces the need to rebuild the exchange, market scheduling, and agent abstractions. The project does not require FCNAgents as the main treatment population; all focal traders can be LLM-guided agents, while deterministic background liquidity agents can be introduced only if needed for stable market operation.

主体实现建议使用 **Python**。市场模拟层优先评估 **PAMS**，因为它已经被与本项目方法最接近的 artificial-market 研究采用，可以减少重复实现 exchange、market scheduling 和 agent abstraction 的工程量。本项目不需要把 FCNAgent 作为主要 treatment population；核心 trader 可以全部采用 LLM-guided decision；只有在维持市场基础流动性确有需要时，才引入在所有 treatment 中保持一致的 deterministic background agents，以避免把 background behavior 误当作 reputation effect。

The prompt layer should be configuration-driven. A base system prompt defines trading objectives, output schema, and available actions; a separate context builder injects private signal, current market state, source action, and reputation evidence. Pydantic or JSON Schema validates every LLM response. To minimize numerical confounds, order price and quantity can be produced by a shared deterministic execution module after the LLM returns direction. Every request should store model identifier, prompt template version, treatment ID, random seed where available, raw structured output, and simulator state hash.

Prompt layer 应采用 configuration-driven 设计。Base system prompt 固定交易目标、output schema 与可选动作；独立 context builder 注入 private signal、current market state、source action 与 reputation evidence。每个 LLM response 通过 Pydantic/JSON Schema 验证。为了减少数值执行混淆，LLM 输出 direction 后由共享 deterministic execution module 统一产生 order price/quantity。每次请求应记录 model identifier、prompt template version、treatment ID、可用的 random seed、raw structured output 与 simulator state hash，以确保可复现性。

---

## Possible Conclusions

One possible result is that histories indicating higher source reliability increase strategic imitation under private-signal conflict relative to lower-reliability or no-history conditions. Such a result would support the project’s LLM modeling rationale: the agent would be using observed evidence to make a source-specific credibility-sensitive decision without a hand-coded reputation-response function, rather than merely following any visible source action.

一种可能结果是：在 private-signal conflict 下，显示更高 source reliability 的历史记录，相比低可靠度历史或不展示历史的条件，显著提高 strategic imitation。这样的结果将支持本研究的 LLM 建模理由：agent 在没有 hand-coded reputation-response function 的情况下，能够根据 observed evidence 作出 source-specific、对 credibility 敏感的决策，而不是看到任何 source action 就一概跟随。

A second possible result is conditional at the market level. Reputation-sensitive imitation may improve price discovery when a historically reliable source receives a correct signal, because information spreads more quickly through the population. The same mechanism may create larger and more persistent temporary mispricing when that source is wrong, because many agents make correlated decisions around a single respected source. These are not contradictory conclusions: they express a single conditional mechanism in which reputation accelerates the propagation of source information, so its market consequence depends on whether the source's current information is accurate. Reputation would therefore act as both an information-aggregation mechanism and a potential concentration-of-error mechanism.

第二种可能结果具有条件性：当历史可靠 source 获得正确 signal 时，reputation-sensitive imitation 可能加快信息传播并提高 price discovery；当该 source 当前出错时，同一种机制可能因为大量 agent 围绕单一可信 source 形成 correlated decisions，而制造更大、更持久的 temporary mispricing。这两种结果并不互相矛盾，而是同一个 conditional mechanism 的两面：reputation 加速了 source information 在群体中的传播，因此其市场后果取决于 source 当前信息是否准确。这样，reputation 可以同时表现为 information-aggregation mechanism 与 potential concentration-of-error mechanism。

A null or weak result is also informative. LLM traders may rely primarily on their own structured private signals, or follow a visible source indiscriminately without differentiating more- from less-reliable histories. Such a result would limit claims that LLM-based market simulations can naturally reproduce reputation-sensitive social learning and would indicate that prompt representation strongly determines the behavioral construct being simulated.

Null/weak result 同样具有研究价值。LLM trader 可能主要依赖自己的 structured private signal；或者无差别跟随可见 source，而不区分不同历史可靠度。这样的结果会限制“LLM market 自然能够模拟 reputation-sensitive social learning”的结论，并说明 prompt representation 本身可能决定了被模拟的 behavioral construct。

---

## Novelty

The first contribution is methodological: the project tests whether an LLM can operationalize **reputation formation from behavioral evidence** without an explicitly programmed reputation-response function. The novelty is therefore not simply the use of an LLM, but the empirical validation of a context-sensitive alternative to fixing the reputation-to-action mapping ex ante. This modeling contribution is deliberately falsifiable: if the history-only condition does not produce stable reputation-sensitive behavior, the stronger `Why LLM?` claim is not supported.

第一项贡献是方法论层面的：本研究检验 LLM 能否在没有显式编写 reputation-response function 的情况下，根据 **behavioral evidence 形成 reputation**。因此，创新点并不是“使用了 LLM”本身，而是对一种 context-sensitive alternative 进行经验验证——不预先固定 reputation-to-action mapping，而是先检验该 mapping 是否能够从 context 中形成。这个建模贡献具有明确的可证伪性：如果 history-only condition 无法产生稳定的 reputation-sensitive behavior，那么更强的 `Why LLM?` 主张就不能成立。

The main contribution is not the broad claim that LLM traders can herd or trust successful peers. Instead, the project **isolates observable source history as a controlled information variable** without supplying a reputation label or hard-coding how that history affects trading decisions. It then connects the validated micro effect to a market-level question: whether reputation-driven imitation improves price discovery when the source is correct but amplifies temporary mispricing when the same reputable source is wrong.

本项目的创新点不是泛泛地证明“LLM 会跟随成功交易者”或“LLM 会表现出 herding”。核心贡献在于**将 source 的可观察历史隔离为可控的信息变量**，不直接提供 reputation label，也不预先编码历史信息如何影响交易决策。随后通过 micro-to-macro design 研究：同一种 reputation-driven imitation 是否在 source 正确时提高 price discovery、而在 reputed source 出错时放大 temporary mispricing。

Relative to Hashimoto et al. (2026), which uses a leaderboard as one context for testing herd behavior, the proposed design holds the source action constant and directly manipulates the source's credibility, making reputation itself rather than generic social information the focal construct. The use of a prior micro test before the market experiment also gives the project a clear falsification point: if reputation cannot be shown to affect individual decisions under controlled conditions, the macro hypothesis is not pursued.

相较于 Hashimoto et al. (2026) 把 leaderboard 作为触发 herd behavior 的一种 context，本研究在保持 source action 不变的条件下直接操纵 source credibility，使 reputation 本身而不是泛化 social information 成为焦点 construct。同时，项目在进入市场模拟前设置 prior micro test，形成清晰的 falsification point：如果受控条件下无法证明 reputation 会改变个体决策，就不继续推进宏观 hypothesis。

---

## Research Limitations

**Construct validity of reputation.** Performance history is an observable proxy for source credibility, not direct evidence that an LLM possesses human-like reputation cognition. Even with matched templates, the model may respond to ordering, sample size, or salient individual outcomes rather than integrate the whole record. The project therefore interprets reputation operationally as observable source-reliability information and avoids claiming that the model possesses human social cognition.

**Reputation 的 construct validity。** 历史表现只是 source credibility 的可观察代理指标，不能据此断言 LLM 具有与人类相同的 reputation cognition。即使使用一致模板，模型也可能受到记录顺序、样本数量或个别显著结果影响，而没有整合全部历史。因此，本项目将 reputation 操作化定义为 observable source-reliability information，而不宣称模型具有与人类一致的社会认知机制。

**Overlap with herding literature.** Reputation-driven imitation is related to herding and social learning, and Hashimoto et al. already show that a leaderboard can trigger LLM herding. The contribution therefore depends on isolating the information contained in source history rather than on claiming an untouched topic. The literature review must be updated continuously to ensure that closely related work does not make the proposed distinction redundant.

**与 herding literature 的重叠。** Reputation-driven imitation 与 herding/social learning 存在天然交叉，Hashimoto et al. 已经表明 leaderboard 能触发 LLM herding。因此，本研究不能把“LLM 会跟随表现好的交易者”作为新发现，创新性依赖于更窄的 causal decomposition。后续必须持续更新文献，以确认 history-inferred reputation 与 source-correctness 的设计仍有独立研究空间。

**LLM necessity and scope of the modeling claim.** Traditional agents can also represent reputation when the researcher specifies an explicit reputation score, utility function, or behavioral weighting rule. The project therefore does not claim that LLMs are necessary or universally superior for reputation modeling. Its narrower claim is that LLMs may provide a useful implementation when the mapping from heterogeneous reputation evidence to action is intentionally left unspecified and tested empirically. If the history-only formal treatment fails, a positive response to explicit cues in the prior test would not rescue this rationale.

**LLM 必要性与建模主张的边界。** 当研究者显式给定 reputation score、utility function 或 behavioral weighting rule 时，传统 agent 同样可以表示 reputation。本项目因此不声称 LLM 对 reputation modeling 是“必需的”，也不声称其普遍优于传统 agent。更窄的主张是：当研究者有意不预先指定“异构 reputation evidence 如何映射为 action”时，LLM 可能提供一种可通过实验验证的实现方式。如果只提供历史记录的正式 treatment 失败，即使 prior test 中显式 cue 有效，也不足以挽救这一 `Why LLM?` 理由。

**Model and prompt dependence.** Results are conditional on the selected LLM, prompt template, inference settings, and structured context design. A limited robustness check across at least one additional model or one alternative prompt wording is desirable, but the project should not expand into a large model benchmark.

**模型与 prompt 依赖。** 研究结果依赖所选 LLM、prompt template、inference settings 与 structured context design。条件允许时应至少使用一个额外模型或一组替代 wording 做有限 robustness check，但不应把项目扩展成大规模 model benchmark。

**Market external validity.** A single-asset artificial LOB is a controlled experimental environment, not a reconstruction of a real exchange. Real reputation is affected by institutions, media, identities, strategic disclosure, regulation, and changing incentives that are intentionally simplified here.

**市场外部有效性。** 单资产 artificial LOB 是受控实验环境，不等于真实交易所。现实中的 reputation 还受到机构身份、媒体、策略性披露、监管与动态激励影响；这些因素在本研究中会被主动简化，以保持研究问题可识别。

**Endogeneity and causal interpretation.** In the macro simulation, earned reputation and trading success are endogenous and can co-evolve with market states. The strongest causal claims therefore come from Phase 1 randomized context manipulations and matched macro treatments. Correlations between influence concentration and mispricing should not automatically be interpreted as complete causal mediation.

**内生性与因果解释。** 在宏观 simulation 中，earned reputation 与 trading success 会与市场状态共同演化，因此最强的因果结论主要来自 Phase 1 的 randomized context manipulation 与 macro matched treatments。Influence concentration 与 mispricing 之间的相关性不能自动解释为完整 causal mediation。

**Computational cost.** Repeated LLM inference across many agents and rounds can dominate simulation cost. The project should first establish the minimum agent population and decision frequency required to reproduce the micro-to-macro mechanism, rather than maximizing market size for realism.

**计算成本。** 多 agent、多轮次的 LLM inference 可能成为主要成本。项目应先确定能够观察 micro-to-macro mechanism 的最小 population 与 decision frequency，而不是为了追求表面 realism 盲目扩大市场规模。

---

## References

1. Graham, J. R. (1999). Herding among investment newsletters: Theory and evidence. *The Journal of Finance, 54*(1), 237–268. https://doi.org/10.1111/0022-1082.00103  
2. Hashimoto, R., Takayanagi, T., Suzuki, M., & Izumi, K. (2026). LLM agents reveal how human bias shapes path-dependent market dynamics. *Journal of Computational Social Science, 9*, Article 32. https://doi.org/10.1007/s42001-026-00465-4  
3. Hirano, M. (2025). Building LLM-based artificial market simulations: Can LLMs function as agents in multi-agent simulations for finance? In *Proceedings of the 26th International Conference on Principles and Practice of Multi-Agent Systems (PRIMA 2025)* (pp. 56–71). Springer. https://doi.org/10.1007/978-3-032-13562-9_5  
4. Scharfstein, D. S., & Stein, J. C. (1990). Herd behavior and investment. *American Economic Review, 80*(3), 465–479.  
5. Sobel, J. (1985). A theory of credibility. *The Review of Economic Studies, 52*(4), 557–573. https://doi.org/10.2307/2297732  
6. Trueman, B. (1994). Analyst forecasts and herding behavior. *The Review of Financial Studies, 7*(1), 97–124. https://doi.org/10.1093/rfs/7.1.97  
7. Xie, C., Chen, C., Jia, F., Ye, Z., Lai, S., Shu, K., Gu, J., Bibi, A., Hu, Z., Jurgens, D., Evans, J., Torr, P., Ghanem, B., & Li, G. (2024). Can large language model agents simulate human trust behavior? In *Advances in Neural Information Processing Systems 37 (NeurIPS 2024)*. https://openreview.net/forum?id=CeOwahuQic

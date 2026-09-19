# Prior Test Architecture

## 1. 总体设计

prior test 实现为无状态、批量执行的 Python harness：

```text
Protocol/Config
      ↓
Scenario, Receiver-State & History Generator ──→ Invariant Validator
      ↓                                  ↓
Matched Trial Cells ──→ Context Renderer ──→ Prompt Hash
      ↓                                  ↓
Randomized Queue ──→ LLM Client ──→ Raw Attempt Log
                                      ↓
                              Schema Validator
                                      ↓
                         Decision/Failure Derived Table
                                      ↓
                       Paired Analysis & Cluster Bootstrap
```

分析和运行层只接受 frozen manifest；任何 prompt、模型、receiver-state schema、source/private relation 或 treatment 改动都产生新 protocol version。已运行的 v1 与计划中的 v2 是不同 protocol；不得合并日志或效应估计。

技术栈采用 OpenAI 标准 Python SDK 的兼容接口调用本地 Ollama LLM：SDK 负责统一请求格式，Ollama 负责本地模型推理。由于本项目只有单轮、无状态的决策调用，不引入 LangChain、LangGraph 或其他 agent orchestration 框架，以减少依赖并保持 prompt、参数和日志的可复现性。

## 2. 目录与模块

```text
prior-test/                              # Self-contained prior-test project
├── .venv/                               # Project-local Python environment; not committed
├── README.md                            # Setup, CLI, data, and figure guide
├── pyproject.toml                   # Package metadata and Python dependencies
├── configs/
│   └── pilot_v2.json      # Planned frozen v2 protocol, model, state, and randomization settings
├── prompts/
│   └── system_v2.txt             # Planned frozen v2 prompt with receiver-state and source blocks
├── src/prior_test/
│   ├── schema.py                         # Data objects: receiver state, own history, source history, trial
│   ├── generate.py                       # Paired source histories, balanced directions/states, trial queue
│   ├── render.py                         # Public-context renderer, block-order variants, prompt hashing
│   ├── client.py                         # Mock client and OpenAI-SDK/Ollama client
│   ├── runner.py                         # Full run orchestration and immutable data collection
│   ├── analyze.py                        # Conflict estimand, bootstrap, balance and heterogeneity tables
│   ├── plot.py                           # PNG figures for rates, paired effects, direction/state diagnostics
│   └── cli.py                            # `prior-test run` and `prior-test analyze` entry point
├── tests/
│   └── test_design_invariants.py        # Pairing, state consistency, balance, leakage, renderer-order tests
└── data/runs/                            # Per-run raw data and artifacts; not committed
```

- `schema.py`：dataclass 定义 receiver portfolio、个人交易史、reference-price state、source history、scenario、trial；严格区分研究者对象与公开 renderer。
- `generate.py`：生成 q、private/source direction 的完全平衡组合和 G+/G−/L−/L+ receiver states；同一家族 H60/H80/H90 共享 realized outcome 序列，只改变 source prediction。
- `render.py`：按计划文档的字段顺序渲染白名单 public context；开发阶段支持 private/source block-order 变体，正式运行冻结其一；绝不序列化完整实验对象。
- `client.py`：通过 OpenAI-compatible SDK 连接 Ollama，负责固定 model adapter、超时、transport retry 与 token usage 记录。
- `runner.py`：交错 treatment、写入 prompt/attempt/decision 日志，并自动触发分析与绘图。
- `analyze.py`：仅在 conflict cell 计算 `follow_source`/`follow_private` 主指标；另输出 agreement、BUY/SELL、q 和 receiver-state 分层，以及 family-level paired bootstrap。
- `plot.py`：输出 conflict 主 treatment 跟随率、family-level H90−H60、方向/一致性/receiver-state 诊断 PNG。
- `tests/`：检查历史计数、portfolio 与未实现盈亏可复算、reference state、direction/relation 平衡、字段泄漏、prompt hash、可行性、重试不重复计数。

## 3. 数据契约

`manifest` 保存 experiment id、protocol version、代码 commit、模型 revision、参数、seed、预算、block order 与停止规则。`scenario` 保存 history family、receiver reference-price state、portfolio、own-history hash、private/source direction、q、source identity、公开状态及 hidden state。`trial` 保存 treatment、source-history hash、模板版本、随机化位置和 replicate。`attempt` 保存完整 prompt 或安全路径、prompt hash、raw response、request id、token、延迟、错误和计费状态。派生表才保存 `signal_relation`、`follow_source`、`follow_private` 和分析纳入标记；agreement cells 不进入 source 独立影响的主估计。

API key 永不写入日志；原始失败不可覆盖。重试产生新的 attempt，但同一 trial 最多只有一个最终有效 decision。

## 4. 执行流程

```python
manifest = freeze_protocol()
cells = generate_matched_cells(manifest)  # includes balanced receiver states and source/private relations
validate_design(cells)
queue = interleave_replicates(render_trials(cells), seed=manifest.order_seed)
for trial in queue:
    for attempt in call_with_retry(trial):
        append_raw(attempt)
    append_parsed_decision(validate_schema(attempt.response))
write_analysis_artifacts(run_directory)
```

`DecisionPolicy` 只负责 render、调用和解析，不编码“高准确率就跟随”的行为规则。离线 Bayesian comparator 仅作为分析参照，不能进入被测 agent。

## 5. 验证与安全边界

付费调用前必须通过 mock client：H60/H80/H90 正确数与方向计数正确；private/source 2×2 组合、agreement/conflict 与 G+/G−/L−/L+ family 分配平衡；portfolio、personal history、cost basis、all-time high/low 与 unrealized P&L 一致且可复算；B0/B1/历史组的信息差异符合协议；hidden outcome 改变不影响公开 prompt；source/private action 可行；schema 拒绝额外字段；随机重跑不重复计数；bootstrap 以 family 为 cluster。

每次运行生成 manifest hash、代码版本和依赖锁定信息。任何 renderer 发现 hidden 字段、treatment label、accuracy summary 或跨 trial 内容时立即 fail closed，而不是继续调用。

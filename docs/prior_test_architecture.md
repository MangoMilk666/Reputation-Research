# Prior Test Architecture

## 1. 总体设计

prior test 实现为无状态、批量执行的 Python harness：

```text
Protocol/Config
      ↓
Scenario & History Generator ──→ Invariant Validator
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

分析和运行层只接受 frozen manifest；任何 prompt、模型或 treatment 改动都产生新 protocol version。

技术栈采用 OpenAI 标准 Python SDK 的兼容接口调用本地 Ollama LLM：SDK 负责统一请求格式，Ollama 负责本地模型推理。由于本项目只有单轮、无状态的决策调用，不引入 LangChain、LangGraph 或其他 agent orchestration 框架，以减少依赖并保持 prompt、参数和日志的可复现性。

## 2. 目录与模块

```text
prior-test/                              # Self-contained prior-test project
├── .venv/                               # Project-local Python environment; not committed
├── README.md                            # Setup, CLI, data, and figure guide
├── pyproject.toml                   # Package metadata and Python dependencies
├── configs/
│   └── pilot_v1.json      # Frozen protocol, model, and randomization settings
├── prompts/
│   └── system_v1.txt             # Frozen system prompt aligned to prior_test_plan
├── src/prior_test/
│   ├── schema.py                         # Data objects and JSON-serialization helpers
│   ├── generate.py                       # Paired histories, mirrored scenarios, trial queue
│   ├── render.py                         # Public-context renderer and prompt hashing
│   ├── client.py                         # Mock client and OpenAI-SDK/Ollama client
│   ├── runner.py                         # Full run orchestration and immutable data collection
│   ├── analyze.py                        # Derived metrics, bootstrap, and output tables
│   ├── plot.py                           # PNG figures for treatment rates and paired effects
│   └── cli.py                            # `prior-test run` and `prior-test analyze` entry point
├── tests/
│   └── test_design_invariants.py        # Pairing, leakage, and renderer-order tests
└── data/runs/                            # Per-run raw data and artifacts; not committed
```

- `schema.py`：dataclass 定义 history、scenario、trial；严格区分研究者对象与公开 renderer。
- `generate.py`：生成 q 分层和镜像方向；同一家族 H60/H80/H90 共享 realized outcome 序列，只改变 source prediction。
- `render.py`：按计划文档的字段顺序渲染白名单 public context；绝不序列化完整实验对象。
- `client.py`：通过 OpenAI-compatible SDK 连接 Ollama，负责固定 model adapter、超时、transport retry 与 token usage 记录。
- `runner.py`：交错 treatment、写入 prompt/attempt/decision 日志，并自动触发分析与绘图。
- `analyze.py`：`follow_source`、`follow_private`、invalid 率及 family-level paired bootstrap。
- `plot.py`：将主 treatment 跟随率和 family-level H90−H60 效应输出为 PNG。
- `tests/`：检查历史计数、镜像、字段泄漏、prompt hash、可行性、重试不重复计数。

## 3. 数据契约

`manifest` 保存 experiment id、protocol version、代码 commit、模型 revision、参数、seed、预算和停止规则。`scenario` 保存 history family、方向、q、source identity、公开状态及 hidden state。`trial` 保存 treatment、history hash、模板版本、随机化位置和 replicate。`attempt` 保存完整 prompt 或安全路径、prompt hash、raw response、request id、token、延迟、错误和计费状态。派生表才保存 `follow_source`、`follow_private` 和分析纳入标记。

API key 永不写入日志；原始失败不可覆盖。重试产生新的 attempt，但同一 trial 最多只有一个最终有效 decision。

## 4. 执行流程

```python
manifest = freeze_protocol()
cells = generate_matched_cells(manifest)
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

付费调用前必须通过 mock client：H60/H80/H90 正确数与方向计数正确；镜像只改变预期方向；B0/B1/历史组的信息差异符合协议；hidden outcome 改变不影响公开 prompt；source/private action 可行；schema 拒绝额外字段；随机重跑不重复计数；bootstrap 以 family 为 cluster。

每次运行生成 manifest hash、代码版本和依赖锁定信息。任何 renderer 发现 hidden 字段、treatment label、accuracy summary 或跨 trial 内容时立即 fail closed，而不是继续调用。

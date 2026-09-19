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
  data/{manifests,scenarios,raw,derived}/
  outputs/{figures,pilot_report.md}
```

- `schema.py`：Pydantic/JSON Schema 定义 manifest、scenario、trial、attempt、decision。
- `generate_scenarios.py`：生成隐藏状态、q、镜像方向及 H60/H80/H90 配对历史。
- `render_context.py`：白名单字段 renderer；绝不序列化完整实验对象。
- `llm_client.py`：通过 OpenAI-compatible SDK 连接 Ollama，负责固定 model adapter、超时、transport retry 与 token usage 记录。
- `run_pilot.py`：交错 treatment、断点续跑；原始响应先落盘再解析。
- `analyze.py`：`follow_source`、`follow_private`、invalid 率及 family-level paired bootstrap。
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
analyze_by_history_family()
```

`DecisionPolicy` 只负责 render、调用和解析，不编码“高准确率就跟随”的行为规则。离线 Bayesian comparator 仅作为分析参照，不能进入被测 agent。

## 5. 验证与安全边界

付费调用前必须通过 mock client：H60/H80/H90 正确数与方向计数正确；镜像只改变预期方向；B0/B1/历史组的信息差异符合协议；hidden outcome 改变不影响公开 prompt；source/private action 可行；schema 拒绝额外字段；随机重跑不重复计数；bootstrap 以 family 为 cluster。

每次运行生成 manifest hash、代码版本和依赖锁定信息。任何 renderer 发现 hidden 字段、treatment label、accuracy summary 或跨 trial 内容时立即 fail closed，而不是继续调用。

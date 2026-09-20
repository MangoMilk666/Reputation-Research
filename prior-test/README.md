# Reputation Prior Test

这是一个无状态、单轮的 LLM decision-probe harness，用于检验 source 的历史可靠性证据是否改变 receiver LLM 的跟随概率。主运行命令会一次完成情境生成、prompt 构建、模型调用、原始数据记录、派生指标计算、统计汇总与 PNG 可视化；不包含订单簿、撮合、LangChain/LangGraph 或多 agent 编排。

调用层通过 OpenAI Python SDK 连接 Ollama 的 OpenAI-compatible endpoint。默认使用 deterministic `mock` backend，仅用来检查工程链路，不能作为实证结果。

## 环境配置

需要 Python 3.11+。所有依赖都必须安装在当前目录的 `.venv/`，不使用全局 Python：

```bash
cd /Users/henrysang/Documents/Reputation-research/prior-test
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . pytest
```

运行本地模型前，启动 Ollama 并拉取默认 v2 配置 `configs/pilot_v2.json` 中的模型：

```bash
ollama serve
ollama pull qwen3:8b
```

默认 Ollama 地址为 `http://localhost:11434/v1`。模型名、温度、token 上限、随机种子、样本量和最多重试次数都在配置文件中冻结；不要将 API key 写入配置或日志。

## Refactor Phase 0：测量与样本结构审计

`configs/refactor_phase0.json` 是 refactor 分支的第一个可运行协议。它只包含最小单期收益任务与私人信号：没有 portfolio、历史价格、个人交易史、source action 或 source history。它用于审计公开 prompt 去重、seed 记录、逐 trial 落盘和结构化响应，不用于估计声誉效应。

正式的小规模审计为 80 个 trial（2 个私人方向 × 2 个 q × 20 个不同 seed）。开发 smoke test 的 `--max-trials` 必须是 4 的倍数；4 条刚好覆盖两个方向和两个 q 各一次。

```bash
.venv/bin/prior-test run \
  --backend mock \
  --config configs/refactor_phase0_qwen.json \
  --max-trials 4 \
  --output data/runs/refactor/phase0/mock-smoke

.venv/bin/prior-test run \
  --backend ollama \
  --config configs/refactor_phase0_qwen.json \
  --output data/runs/refactor/phase0/qwen3-8b-audit
```

阶段 0 的 `summary.json` 报告每个 `q × private direction` 格子的私人信号一致率、BUY/SELL 计数、有效率和公开 prompt condition 数。唯一图表为 `figures/private_signal_consistency.png`；它不生成不适用的 source-following 图。

## Refactor Phase B：中性 portfolio 消融

在 Phase 0 的最小任务已通过后，`refactor_phaseB_neutral_portfolio_{qwen,llama}.json` 是阶段 B 的第一个单块消融协议。它保留完全相同的终值、先验、收益表、私人信号、system prompt 与输出格式，只增加中性 portfolio：现金 1000、库存 10、平均成本价 100、当前持仓市值 1000、未实现盈亏 0。

它不包含 source、source history、own trading history、all-time high/low 或 `G+ / G- / L+ / L-` 标签。正式运行仍为 80 条；smoke test 的 `--max-trials` 必须是 4 的倍数。

```bash
.venv/bin/prior-test run \
  --backend mock \
  --config configs/refactor_phaseB_neutral_portfolio_qwen.json \
  --max-trials 4 \
  --output data/runs/refactor/phaseB-neutral-portfolio/mock-smoke

.venv/bin/prior-test run \
  --backend ollama \
  --config configs/refactor_phaseB_neutral_portfolio_qwen.json \
  --output data/runs/refactor/phaseB-neutral-portfolio/qwen3-8b-audit
```

使用 Llama 时仅替换配置文件为 `configs/refactor_phaseB_neutral_portfolio_llama.json`。若任一 `q × private direction` 格子的私人信号一致率低于 80%，或重新出现 BUY/SELL 饱和，则停止增加后续 context block，并先定位该 portfolio block 的影响。

## CLI 用法

```text
.venv/bin/prior-test run [--backend mock|ollama] [--config PATH] [--output RUN_DIR] [--max-trials N]
.venv/bin/prior-test analyze --output RUN_DIR
```

`run` 是日常使用的完整实验命令，自动完成全部数据与图表产物；`analyze` 不调用模型，只针对一个既有运行目录重新计算 summary、派生表与图。

运行 `run` 时，终端会实时显示当前 trial 序号、总 trial 数、完成百分比、history family、treatment、replicate、有效/无效响应数、已用时间和预估剩余时间（ETA）。进度信息输出到标准错误流，不影响标准输出中的最终 JSON 结果。

| 参数 | 含义 | 示例 |
| --- | --- | --- |
| `--backend` | 推理后端。`mock` 为本地确定性开发模拟；`ollama` 才会连接本地 LLM。默认 `mock`。 | `--backend ollama` |
| `--config` | protocol 配置 JSON 路径。默认 `configs/pilot_v2.json`；`pilot_v1.json` 仅用于复现旧协议。 | `--config configs/pilot_v2.json` |
| `--output` | 本次运行输出目录。目录必须不存在，防止覆盖原始数据。未指定时以 UTC 时间自动命名。`analyze` 必填。 | `--output data/runs/smoke` |
| `--max-trials` | 用于 smoke test，按完整平衡 block 选择 trial，而不是截断随机队列。v2 的 N 必须是 40 的整数倍；40 条恰为一个 family × 两个 private direction × 两个 source direction × 两个 q × 五个 treatment × 一个 replicate。正式运行不填写。 | `--max-trials 40` |

建议先运行测试和 mock smoke test：

```bash
.venv/bin/python -m pytest
.venv/bin/prior-test run --backend mock --max-trials 40 --output data/runs/smoke-v2
```

检查输出后再做 Ollama smoke test：

```bash
.venv/bin/prior-test run --backend ollama --max-trials 40 --output data/runs/ollama-smoke-v2
```

完整 v2 pilot 为 4,800 个 trial；只应在 prompt、模型版本、预算和停止规则冻结后运行：

```bash
.venv/bin/prior-test run --backend ollama --config configs/pilot_v2.json --output data/runs/pilot-v2
```

## 数据与图表产物

每次 `run` 创建一个独立运行目录，例如 `data/runs/pilot-v1/`：

| 产物 | 内容 |
| --- | --- |
| `manifest.json` | 冻结的配置、backend 与计划 trial 数。 |
| `system_prompt.txt` | 本次运行实际使用的完整冻结 system prompt。 |
| `scenarios.jsonl` | 每个 history family 的情境与仅研究者可见的生成结构。 |
| `prompts.jsonl` | 每个 trial 实际发送给模型的 public context 及 prompt hash。 |
| `raw_attempts.jsonl` | 每次调用尝试的原始回复、request id、token、延迟和错误；失败不会被覆盖。 |
| `decisions.jsonl` | 每个 trial 最终有效 action 或 invalid 状态。 |
| `derived_decisions.csv` | 带 `signal_relation`、`follow_source`、`follow_private` 与主样本标记的分析表。 |
| `summary.json` | 有效率、仅 conflict cell 的 H90−H60 主效应、family bootstrap 区间，以及 agreement/conflict、价格状态分层结果。 |
| `figures/source_following_conflict_rates.png` | conflict cells 中 B1/H60/H80/H90 的 source-following rate 柱状图。 |
| `figures/paired_history_effects.png` | conflict cells 中每个 history family 的 H90−H60 配对效应图。 |
| `figures/source_following_by_relation.png` | agreement 与 conflict 下各 treatment 的方向一致率诊断图。 |

`scenarios.jsonl` 中的 hidden/researcher-only 信息不可复制进 `prompts.jsonl`。研究结果应基于 `decisions.jsonl` 与 `derived_decisions.csv`；`mock` 输出仅用于验证流程。

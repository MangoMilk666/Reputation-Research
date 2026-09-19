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

运行本地模型前，启动 Ollama 并拉取 `configs/pilot_v1.json` 中的模型：

```bash
ollama serve
ollama pull qwen3:8b
```

默认 Ollama 地址为 `http://localhost:11434/v1`。模型名、温度、token 上限、随机种子、样本量和最多重试次数都在配置文件中冻结；不要将 API key 写入配置或日志。

## CLI 用法

```text
.venv/bin/prior-test run [--backend mock|ollama] [--config PATH] [--output RUN_DIR] [--max-trials N]
.venv/bin/prior-test analyze --output RUN_DIR
```

`run` 是日常使用的完整实验命令，自动完成全部数据与图表产物；`analyze` 不调用模型，只针对一个既有运行目录重新计算 summary、派生表与图。

| 参数 | 含义 | 示例 |
| --- | --- | --- |
| `--backend` | 推理后端。`mock` 为本地确定性开发模拟；`ollama` 才会连接本地 LLM。默认 `mock`。 | `--backend ollama` |
| `--config` | protocol 配置 JSON 路径。默认 `configs/pilot_v1.json`。 | `--config configs/pilot_v1.json` |
| `--output` | 本次运行输出目录。目录必须不存在，防止覆盖原始数据。未指定时以 UTC 时间自动命名。`analyze` 必填。 | `--output data/runs/smoke` |
| `--max-trials` | 只运行随机化队列前 N 个 trial，用于 smoke test；不改变原始 protocol 配置。省略时运行完整 pilot。 | `--max-trials 20` |

建议先运行测试和 mock smoke test：

```bash
.venv/bin/python -m pytest
.venv/bin/prior-test run --backend mock --max-trials 20 --output data/runs/smoke
```

检查输出后再做 Ollama smoke test：

```bash
.venv/bin/prior-test run --backend ollama --max-trials 20 --output data/runs/ollama-smoke
```

完整 pilot 为 2,400 个 trial；只应在 prompt、模型版本、预算和停止规则冻结后运行：

```bash
.venv/bin/prior-test run --backend ollama --output data/runs/pilot-v1
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
| `derived_decisions.csv` | 带 `follow_source`、`follow_private` 的分析表。 |
| `summary.json` | 有效率、各组 source-following rate、H90−H60 主效应及 family bootstrap 区间。 |
| `figures/source_following_rates.png` | B1/H60/H80/H90 的 source-following rate 柱状图。 |
| `figures/paired_history_effects.png` | 每个 history family 的 H90−H60 配对效应图。 |

`scenarios.jsonl` 中的 hidden/researcher-only 信息不可复制进 `prompts.jsonl`。研究结果应基于 `decisions.jsonl` 与 `derived_decisions.csv`；`mock` 输出仅用于验证流程。

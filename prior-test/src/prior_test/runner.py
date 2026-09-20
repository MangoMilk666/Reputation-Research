from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .analyze import write_analysis_artifacts
from .client import MockClient, OllamaClient, parse_action
from .generate import generate_scenarios, make_trials, select_balanced_smoke_trials
from .render import prompt_hash, render_context
from .schema import to_jsonable


class ProgressReporter:
    """在终端显示 trial 进度、有效响应数、失败数与 ETA。"""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.valid = 0
        self.invalid = 0
        self.started_at = time.monotonic()
        self.is_tty = sys.stderr.isatty()

    def start_trial(self, trial) -> None:
        """在模型调用前显示当前将要执行的 trial。"""
        self._render(trial, status="running")

    def finish_trial(self, trial, is_valid: bool) -> None:
        """在模型调用完成后更新计数，并基于已完成 trial 估计剩余时间。"""
        self.completed += 1
        self.valid += int(is_valid)
        self.invalid += int(not is_valid)
        self._render(trial, status="done")

    def close(self) -> None:
        """结束动态进度行，避免后续输出与进度条位于同一行。"""
        if self.is_tty:
            print(file=sys.stderr)

    def _render(self, trial, status: str) -> None:
        elapsed = time.monotonic() - self.started_at
        rate = self.completed / elapsed if self.completed and elapsed else 0.0
        remaining = (self.total - self.completed) / rate if rate else 0.0
        current = min(self.completed + (status == "running"), self.total)
        bar_width = 24
        filled = round(bar_width * current / self.total)
        bar = "#" * filled + "-" * (bar_width - filled)
        message = (
            f"[{bar}] [{status}] trial {current}/{self.total} "
            f"({current / self.total:.1%}) | family={trial.scenario.family_id} "
            f"treatment={trial.treatment_id} replicate={trial.replicate_id} | "
            f"valid={self.valid} invalid={self.invalid} | elapsed={elapsed:.0f}s ETA={remaining:.0f}s"
        )
        # 交互式终端覆盖同一行，重定向日志则逐行输出，便于之后回看。
        if self.is_tty:
            print(f"\r{message:<180}", end="", file=sys.stderr, flush=True)
        elif status == "done":
            print(message, file=sys.stderr, flush=True)


def write_jsonl(path: Path, record: dict) -> None:
    """追加不可变实验记录，避免重试或重新分析时覆盖原始证据。"""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def run(config: dict, system_prompt: str, output_dir: Path, backend: str, max_trials: int | None) -> int:
    """执行一次完整 protocol：生成情境、调用模型、记录原始输出并产出分析文件。"""
    output_dir.mkdir(parents=True, exist_ok=False)
    scenarios = generate_scenarios(config)
    trials = make_trials(scenarios, config)
    if max_trials is not None:
        trials = select_balanced_smoke_trials(trials, max_trials, config)
    progress = ProgressReporter(total=len(trials))
    # manifest 冻结本次运行的一切公开参数，使之后可判断两次结果能否比较。
    manifest = {**config, "backend": backend, "planned_trial_count": len(trials)}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    scenario_path, prompt_path, raw_path, decision_path = output_dir / "scenarios.jsonl", output_dir / "prompts.jsonl", output_dir / "raw_attempts.jsonl", output_dir / "decisions.jsonl"
    for scenario in scenarios:
        write_jsonl(scenario_path, to_jsonable(scenario))
    client = MockClient() if backend == "mock" else OllamaClient(
        config["base_url"], config["model"], config["temperature"], config["max_tokens"], config.get("thinking")
    )
    for trial in trials:
        progress.start_trial(trial)
        context = render_context(trial, config)
        scenario = trial.scenario
        trial_seed = config["request_seed"] + trial.order_index + 1
        trial_record = {
            "trial_id": trial.trial_id,
            "family_id": scenario.family_id,
            "reference_price_state": scenario.portfolio.reference_price_state if scenario.portfolio else None,
            "private_direction": scenario.private_direction,
            "source_action": scenario.source_action,
            "signal_relation": scenario.signal_relation,
            "private_reliability": scenario.private_reliability,
            "treatment_id": trial.treatment_id,
            "replicate_id": trial.replicate_id,
            "order_index": trial.order_index,
            "private_action": "BUY" if scenario.private_direction == "UP" else "SELL",
            "prompt_hash": prompt_hash(system_prompt, context),
            "context_blocks": config.get("context_blocks", ["legacy_v2_context"]),
            "trial_seed": trial_seed,
        }
        # 公开输入和模型原始输出分开保存，防止派生分析污染原始记录。
        write_jsonl(prompt_path, {**trial_record, "user_context": context})
        final_action, error = None, None
        final_attempt_id, final_seed = None, None
        for attempt_id in range(1, config["max_attempts"] + 1):
            completion = None
            attempt_seed = config["request_seed"] + trial.order_index + attempt_id
            try:
                completion = client.complete(system_prompt=system_prompt, user_context=context, seed=attempt_seed)
                action = parse_action(completion.content)
                write_jsonl(raw_path, {**trial_record, "attempt_id": attempt_id, "attempt_seed": attempt_seed, "raw_response": completion.content, "request_id": completion.request_id, "usage": completion.usage, "latency_ms": completion.latency_ms, "error": None})
                final_action = action
                final_attempt_id, final_seed = attempt_id, attempt_seed
                break
            except Exception as exc:  # 每一次失败也要保存，才能计算保守失败界限。
                error = f"{type(exc).__name__}: {exc}"
                # 解析失败时保留模型原文；网络失败没有原文时才写入空值。
                write_jsonl(raw_path, {
                    **trial_record,
                    "attempt_id": attempt_id,
                    "attempt_seed": attempt_seed,
                    "raw_response": completion.content if completion else None,
                    "request_id": completion.request_id if completion else None,
                    "usage": completion.usage if completion else {},
                    "latency_ms": completion.latency_ms if completion else None,
                    "error": error,
                })
                time.sleep(min(0.25 * attempt_id, 1.0))
        write_jsonl(decision_path, {**trial_record, "action": final_action, "valid": final_action is not None, "final_attempt_id": final_attempt_id, "final_seed": final_seed, "final_error": error if final_action is None else None})
        progress.finish_trial(trial, is_valid=final_action is not None)
    progress.close()
    # 单次 run 同时产出数据、汇总表和图。
    write_analysis_artifacts(output_dir)
    return len(trials)

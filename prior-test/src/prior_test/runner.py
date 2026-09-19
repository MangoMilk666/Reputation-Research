from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .analyze import write_analysis_artifacts
from .client import MockClient, OllamaClient, parse_action
from .generate import generate_scenarios, make_trials
from .render import prompt_hash, render_user_context
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
        # Interactive terminals redraw one compact line; redirected logs remain readable.
        if self.is_tty:
            print(f"\r{message:<180}", end="", file=sys.stderr, flush=True)
        elif status == "done":
            print(message, file=sys.stderr, flush=True)


def write_jsonl(path: Path, record: dict) -> None:
    """Append immutable experimental records. / 追加不可变实验记录。"""
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def run(config: dict, system_prompt: str, output_dir: Path, backend: str, max_trials: int | None) -> int:
    '''
    正式跑数据，调用所有封装好的函数。
    '''
    output_dir.mkdir(parents=True, exist_ok=False)
    scenarios = generate_scenarios(config)
    trials = make_trials(scenarios, config)
    if max_trials is not None:
        trials = trials[:max_trials]
    progress = ProgressReporter(total=len(trials))
    # The manifest freezes every user-visible run setting. / manifest 冻结用户可见的每项运行设置。
    manifest = {**config, "backend": backend, "planned_trial_count": len(trials)}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "system_prompt.txt").write_text(system_prompt, encoding="utf-8")
    scenario_path, prompt_path, raw_path, decision_path = output_dir / "scenarios.jsonl", output_dir / "prompts.jsonl", output_dir / "raw_attempts.jsonl", output_dir / "decisions.jsonl"
    for scenario in scenarios:
        write_jsonl(scenario_path, to_jsonable(scenario))
    client = MockClient() if backend == "mock" else OllamaClient(config["base_url"], config["model"], config["temperature"], config["max_tokens"])
    for trial in trials:
        progress.start_trial(trial)
        context = render_user_context(trial)
        trial_record = {"trial_id": trial.trial_id, "family_id": trial.scenario.family_id, "direction": trial.scenario.direction, "private_reliability": trial.scenario.private_reliability, "treatment_id": trial.treatment_id, "replicate_id": trial.replicate_id, "order_index": trial.order_index, "source_action": trial.scenario.source_action, "private_action": "BUY" if trial.scenario.private_direction == "UP" else "SELL", "prompt_hash": prompt_hash(system_prompt, context)}
        # Store public prompt inputs separately from raw model outputs. / 将公开 prompt 输入与原始模型输出分开保存。
        write_jsonl(prompt_path, {**trial_record, "user_context": context})
        final_action, error = None, None
        for attempt_id in range(1, config["max_attempts"] + 1):
            try:
                completion = client.complete(system_prompt=system_prompt, user_context=context, seed=config["request_seed"] + trial.order_index + attempt_id)
                action = parse_action(completion.content)
                write_jsonl(raw_path, {**trial_record, "attempt_id": attempt_id, "raw_response": completion.content, "request_id": completion.request_id, "usage": completion.usage, "latency_ms": completion.latency_ms, "error": None})
                final_action = action
                break
            except Exception as exc:  # preserve each failed attempt for exclusion bounds
                error = f"{type(exc).__name__}: {exc}"
                write_jsonl(raw_path, {**trial_record, "attempt_id": attempt_id, "raw_response": None, "request_id": None, "usage": {}, "latency_ms": None, "error": error})
                time.sleep(min(0.25 * attempt_id, 1.0))
        write_jsonl(decision_path, {**trial_record, "action": final_action, "valid": final_action is not None, "final_error": error if final_action is None else None})
        progress.finish_trial(trial, is_valid=final_action is not None)
    progress.close()
    # 单次 run 同时产出数据、汇总表和图。
    write_analysis_artifacts(output_dir)
    return len(trials)

from __future__ import annotations

import json
import random
from collections import defaultdict
from csv import DictWriter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    """Load immutable JSONL records.
    读取不可变 JSONL 记录。"""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def summarize(run_dir: Path, bootstrap_reps: int = 5000) -> dict:
    """Calculate protocol-defined rates and family-cluster uncertainty.
    计算协议规定的跟随率与 history-family cluster 不确定性。
    """
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    valid = [row for row in decisions if row["valid"]]
    by_treatment: dict[str, list[dict]] = defaultdict(list)
    for row in valid:
        if row["treatment_id"] != "B0":
            by_treatment[row["treatment_id"]].append(row)
    rates = {name: sum(row["action"] == row["source_action"] for row in rows) / len(rows) for name, rows in by_treatment.items()}
    family_rates: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for row in valid:
        if row["treatment_id"] in {"H60", "H90"}:
            family_rates[row["family_id"]][row["treatment_id"]].append(int(row["action"] == row["source_action"]))
    effects = [sum(values["H90"]) / len(values["H90"]) - sum(values["H60"]) / len(values["H60"]) for values in family_rates.values() if values["H60"] and values["H90"]]
    rng = random.Random(20260921)
    boot = sorted(sum(rng.choice(effects) for _ in effects) / len(effects) for _ in range(bootstrap_reps)) if effects else []
    return {"planned_trials": len(decisions), "valid_trials": len(valid), "valid_rate": len(valid) / len(decisions) if decisions else 0, "follow_source_rates": rates, "delta_history_h90_minus_h60": sum(effects) / len(effects) if effects else None, "family_count": len(effects), "bootstrap_95_ci": [boot[int(.025 * len(boot))], boot[int(.975 * len(boot))]] if boot else None}


def write_analysis_artifacts(run_dir: Path) -> dict:
    """Write summary, derived decision table, and reproducible figures.
        写入 summary、派生决策表和可复现图表；由 CLI 的 run 自动调用。
    """
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    for row in decisions:
        row["follow_source"] = row["valid"] and row["action"] == row["source_action"] if row["treatment_id"] != "B0" else None
        row["follow_private"] = row["valid"] and row["action"] == row["private_action"]
    with (run_dir / "derived_decisions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(handle, fieldnames=list(decisions[0]) if decisions else [])
        if decisions:
            writer.writeheader()
            writer.writerows(decisions)
    result = summarize(run_dir)
    (run_dir / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    from .plot import write_figures
    write_figures(run_dir, decisions, result)
    return result

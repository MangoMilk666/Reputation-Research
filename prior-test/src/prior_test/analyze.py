from __future__ import annotations

import json
import random
from collections import defaultdict
from csv import DictWriter
from pathlib import Path


def load_jsonl(path: Path) -> list[dict]:
    """读取不可变 JSONL 记录；分析只从已保存的决策重算，不再调用模型。"""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _rate(rows: list[dict]) -> float | None:
    """计算 source-following 比率；空分组保留为空而不是伪造零值。"""
    return sum(row["action"] == row["source_action"] for row in rows) / len(rows) if rows else None


def summarize(run_dir: Path, bootstrap_reps: int = 5000) -> dict:
    """按 v2 规则计算 conflict 主效应、分层比例和 family cluster 区间。"""
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    valid = [row for row in decisions if row["valid"]]
    non_b0 = [row for row in valid if row["treatment_id"] != "B0"]
    conflict = [row for row in non_b0 if row["signal_relation"] == "conflict"]
    by_treatment: dict[str, list[dict]] = defaultdict(list)
    for row in conflict:
        by_treatment[row["treatment_id"]].append(row)
    conflict_rates = {name: _rate(rows) for name, rows in by_treatment.items()}
    by_relation: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in non_b0:
        by_relation[row["signal_relation"]][row["treatment_id"]].append(row)
    relation_rates = {relation: {treatment: _rate(rows) for treatment, rows in groups.items()} for relation, groups in by_relation.items()}
    by_state: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in conflict:
        by_state[row["reference_price_state"]][row["treatment_id"]].append(row)
    state_rates = {state: {treatment: _rate(rows) for treatment, rows in groups.items()} for state, groups in by_state.items()}
    family_rates: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for row in conflict:
        if row["treatment_id"] in {"H60", "H90"}:
            family_rates[row["family_id"]][row["treatment_id"]].append(int(row["action"] == row["source_action"]))
    effects = [sum(values["H90"]) / len(values["H90"]) - sum(values["H60"]) / len(values["H60"]) for values in family_rates.values() if values["H60"] and values["H90"]]
    rng = random.Random(20260921)
    boot = sorted(sum(rng.choice(effects) for _ in effects) / len(effects) for _ in range(bootstrap_reps)) if effects else []
    return {
        "planned_trials": len(decisions),
        "valid_trials": len(valid),
        "valid_rate": len(valid) / len(decisions) if decisions else 0,
        "conflict_follow_source_rates": conflict_rates,
        "conflict_treatment_sample_sizes": {name: len(rows) for name, rows in by_treatment.items()},
        "follow_source_rates_by_relation": relation_rates,
        "conflict_follow_source_rates_by_reference_state": state_rates,
        "delta_history_h90_minus_h60_conflict": sum(effects) / len(effects) if effects else None,
        "family_count": len(effects),
        "bootstrap_95_ci": [boot[int(.025 * len(boot))], boot[int(.975 * len(boot))]] if boot else None,
        "paired_effect_note": None if effects else "No complete H60/H90 conflict family pair is available in this run.",
    }


def write_analysis_artifacts(run_dir: Path) -> dict:
    """写入派生表、汇总 JSON 和可复现图表，且不改变原始决策文件。"""
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    for row in decisions:
        has_source = row["treatment_id"] != "B0"
        row["follow_source"] = row["valid"] and row["action"] == row["source_action"] if has_source else None
        row["follow_private"] = row["valid"] and row["action"] == row["private_action"]
        row["is_primary_conflict_cell"] = has_source and row["signal_relation"] == "conflict"
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

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


def _private_signal_rate(rows: list[dict]) -> float | None:
    """计算 action 与私人信号隐含方向一致的比例，空分组不伪造零值。"""
    return sum(row["action"] == row["private_action"] for row in rows) / len(rows) if rows else None


def _load_manifest(run_dir: Path) -> dict:
    """读取运行时冻结的配置，以便按 protocol 选择对应分析口径。"""
    return json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))


def summarize(run_dir: Path, bootstrap_reps: int = 5000) -> dict:
    """按 v2 规则计算 conflict 主效应、分层比例和 family cluster 区间。"""
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    protocol = _load_manifest(run_dir)["protocol_version"]
    if protocol in {"refactor_phase0", "refactor_phaseB_neutral_portfolio", "refactor_phaseB_unrealized_pnl"}:
        return summarize_private_signal_protocol(decisions, protocol)
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


def summarize_private_signal_protocol(decisions: list[dict], protocol: str) -> dict:
    """输出阶段 0/B 所需的私人信号一致率、样本量和行动饱和诊断。"""
    valid = [row for row in decisions if row["valid"]]
    legacy_variant = {
        "refactor_phase0": "no_portfolio",
        "refactor_phaseB_neutral_portfolio": "neutral_portfolio",
    }.get(protocol, "unknown_context_variant")
    cells: dict[tuple[float, str], list[dict]] = defaultdict(list)
    cells_by_variant: dict[str, dict[tuple[float, str], list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in valid:
        cells[(row["private_reliability"], row["private_direction"])].append(row)
        cells_by_variant[row.get("context_variant", legacy_variant)][(row["private_reliability"], row["private_direction"])].append(row)
    cell_summary = {
        f"q{reliability:g}_{direction}": {
            "sample_size": len(rows),
            "private_signal_consistent_rate": _private_signal_rate(rows),
            "buy_rate": sum(row["action"] == "BUY" for row in rows) / len(rows) if rows else None,
        }
        for (reliability, direction), rows in sorted(cells.items())
    }
    action_counts = {action: sum(row["action"] == action for row in valid) for action in ("BUY", "SELL")}
    public_condition_count = len({row["prompt_hash"] for row in decisions})
    variant_summary = {
        variant: {
            f"q{reliability:g}_{direction}": {
                "sample_size": len(rows),
                "private_signal_consistent_rate": _private_signal_rate(rows),
                "buy_rate": sum(row["action"] == "BUY" for row in rows) / len(rows) if rows else None,
            }
            for (reliability, direction), rows in sorted(variant_cells.items())
        }
        for variant, variant_cells in sorted(cells_by_variant.items())
    }
    return {
        "analysis_kind": "refactor_private_signal_protocol",
        "protocol_version": protocol,
        "planned_trials": len(decisions),
        "valid_trials": len(valid),
        "valid_rate": len(valid) / len(decisions) if decisions else 0,
        "public_prompt_condition_count": public_condition_count,
        "private_signal_cells": cell_summary,
        "private_signal_cells_by_context_variant": variant_summary,
        "action_counts": action_counts,
        "action_rates": {action: count / len(valid) if valid else None for action, count in action_counts.items()},
        "phase_gate_note": (
            "Each q×private-direction cell requires at least 20 valid trials, "
            "a private-signal-consistent rate of at least 0.80, and neither action is saturated."
        ),
    }


def write_analysis_artifacts(run_dir: Path) -> dict:
    """写入派生表、汇总 JSON 和可复现图表，且不改变原始决策文件。"""
    decisions = load_jsonl(run_dir / "decisions.jsonl")
    for row in decisions:
        has_source = row["source_action"] is not None
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

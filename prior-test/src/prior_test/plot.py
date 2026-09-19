from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def write_figures(run_dir: Path, decisions: list[dict], summary: dict) -> None:
    """从派生决策输出 v2 主效应、family 配对效应和关系诊断图。"""
    import matplotlib.pyplot as plt

    figures = run_dir / "figures"
    figures.mkdir(exist_ok=True)
    treatments = ["B1", "H60", "H80", "H90"]
    rates = [summary["conflict_follow_source_rates"].get(name, 0) or 0 for name in treatments]
    fig, axis = plt.subplots(figsize=(6, 4))
    axis.bar(treatments, rates, color=["#8da0cb", "#fc8d62", "#66c2a5", "#1b9e77"])
    axis.set_ylim(0, 1)
    axis.set_ylabel("Conflict source-following rate")
    axis.set_title("Source-following in conflict cells")
    fig.tight_layout()
    fig.savefig(figures / "source_following_conflict_rates.png", dpi=180)
    plt.close(fig)

    families: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for row in decisions:
        if row["valid"] and row["signal_relation"] == "conflict" and row["treatment_id"] in {"H60", "H90"}:
            families[row["family_id"]][row["treatment_id"]].append(int(row["action"] == row["source_action"]))
    effects = {family: sum(values["H90"]) / len(values["H90"]) - sum(values["H60"]) / len(values["H60"]) for family, values in families.items() if values["H60"] and values["H90"]}
    fig, axis = plt.subplots(figsize=(7, 4))
    axis.axhline(0, color="black", linewidth=.8)
    if effects:
        axis.scatter(list(effects), list(effects.values()), color="#1b9e77")
        axis.tick_params(axis="x", rotation=60)
    else:
        axis.text(.5, .5, "No complete H60/H90 conflict family\npair is available in this run.", ha="center", va="center", transform=axis.transAxes)
        axis.set_xticks([])
    axis.set_ylabel("H90 − H60 source-following rate")
    axis.set_title("Paired history-family effects in conflict cells")
    fig.tight_layout()
    fig.savefig(figures / "paired_history_effects.png", dpi=180)
    plt.close(fig)

    by_relation = summary["follow_source_rates_by_relation"]
    fig, axis = plt.subplots(figsize=(7, 4))
    for relation, color in (("agreement", "#7570b3"), ("conflict", "#d95f02")):
        axis.plot(treatments, [by_relation.get(relation, {}).get(name, 0) or 0 for name in treatments], marker="o", label=relation, color=color)
    axis.set_ylim(0, 1)
    axis.set_ylabel("Source-direction agreement rate")
    axis.set_title("Action agreement by signal relation")
    axis.legend(title="signal relation")
    fig.tight_layout()
    fig.savefig(figures / "source_following_by_relation.png", dpi=180)
    plt.close(fig)

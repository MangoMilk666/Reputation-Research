from __future__ import annotations

import hashlib

from .schema import Trial


def render_user_context(trial: Trial) -> str:
    """Render only protocol-approved public fields.
        仅渲染协议允许的公开字段。"""
    scenario = trial.scenario
    # Fixed field order protects treatment comparability. / 固定字段顺序以保护处理组可比性。
    lines = [
        "(Information for this decision)",
        "asset_id: SYNTH_1", "current_price: 100", "terminal_value_UP: 110",
        "terminal_value_DOWN: 90", "prior_probability_UP: 0.5", "cash: 1000", "inventory: 10",
        "private_signal:",
        f'  report: "The analyst evidence leans {scenario.private_direction}, but it is noisy."',
        f"  directional_implication: {scenario.private_direction}",
        f"  reliability: {scenario.private_reliability}",
    ]
    if trial.treatment_id != "B0":
        lines.extend(["source:", "  id: trader_17", f"  current_action: {scenario.source_action}"])
        if trial.treatment_id.startswith("H"):
            lines.append("  history:")
            lines.extend(f"    period: {row.period}; prediction: {row.source_action}; realized_state: {row.realized_state}" for row in scenario.histories[trial.treatment_id])
    return "\n".join(lines)


def prompt_hash(system_prompt: str, user_context: str) -> str:
    return hashlib.sha256(f"{system_prompt}\n{user_context}".encode()).hexdigest()

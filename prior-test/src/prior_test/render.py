from __future__ import annotations

import hashlib

from .schema import Trial


def _render_own_history(trial: Trial) -> list[str]:
    """将 receiver 自己的成交记录写成固定长度、固定字段顺序的公开文本。"""
    return [f"  period: {row.period}; order: {row.action}; quantity: {row.quantity}; execution_price: {row.execution_price:g}" for row in trial.scenario.own_history]


def _render_private_signal(trial: Trial) -> list[str]:
    """渲染私人分析师线索；方向是证据，不是要求模型照做的命令。"""
    scenario = trial.scenario
    return [
        "private_signal:",
        f'  report: "The analyst evidence leans {scenario.private_direction}, but it is noisy."',
        f"  directional_implication: {scenario.private_direction}",
        f"  reliability: {scenario.private_reliability}",
    ]


def _render_source(trial: Trial) -> list[str]:
    """只在允许的处理组呈现 source；B1 不含历史，历史组才含完整记录。"""
    if trial.treatment_id == "B0":
        return []
    lines = ["source:", "  id: trader_17", f"  observed_order: {trial.scenario.source_action}"]
    if trial.treatment_id.startswith("H"):
        lines.append("  history:")
        lines.extend(f"    period: {row.period}; prediction: {row.source_action}; realized_state: {row.realized_state}" for row in trial.scenario.histories[trial.treatment_id])
    return lines


def render_user_context(trial: Trial, information_block_order: str = "private_then_source") -> str:
    """仅渲染 v2 白名单字段，并按冻结顺序放置私人与社会信息块。"""
    portfolio = trial.scenario.portfolio
    lines = [
        "(Information for this decision)",
        "asset_id: SYNTH_1",
        f"current_price: {portfolio.current_price:g}",
        f"all_time_high: {portfolio.all_time_high:g}",
        f"all_time_low: {portfolio.all_time_low:g}",
        "terminal_value_UP: 110",
        "terminal_value_DOWN: 90",
        "prior_probability_UP: 0.5",
        "portfolio:",
        f"  cash: {portfolio.cash:g}",
        f"  inventory: {portfolio.inventory}",
        f"  average_cost_basis: {portfolio.average_cost_basis:g}",
        f"  current_position_market_value: {portfolio.current_position_market_value:g}",
        f"  unrealized_gain_loss: {portfolio.unrealized_gain_loss:g}",
        f"  reference_price_state: {portfolio.reference_price_state}",
        "own_trading_history:",
        *_render_own_history(trial),
    ]
    private_block, source_block = _render_private_signal(trial), _render_source(trial)
    # 开发时可比较两种等价顺序；每次正式运行只能冻结其中一种。
    if information_block_order == "private_then_source":
        lines.extend(private_block)
        lines.extend(source_block)
    elif information_block_order == "source_then_private":
        lines.extend(source_block)
        lines.extend(private_block)
    else:
        raise ValueError("information_block_order must be private_then_source or source_then_private")
    return "\n".join(lines)


def prompt_hash(system_prompt: str, user_context: str) -> str:
    """为最终发送的两段文本生成稳定哈希，以便审计与复算。"""
    return hashlib.sha256(f"{system_prompt}\n{user_context}".encode()).hexdigest()

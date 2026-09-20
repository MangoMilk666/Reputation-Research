from __future__ import annotations

import random

from .schema import HistoryRecord, OwnTradeRecord, PortfolioState, Scenario, Trial


# 四类价格路径来自 v2 协议，用于平衡 receiver 的个人参照点。
REFERENCE_STATES = ("G+", "G-", "L-", "L+")
PRIVATE_SIGNAL_PROTOCOLS = {
    "refactor_phase0",
    "refactor_phaseB_neutral_portfolio",
    "refactor_phaseB_unrealized_pnl",
    "refactor_phaseB_all_time_range",
}


def make_history(correct_count: int, rng: random.Random) -> list[HistoryRecord]:
    """生成满足长度、方向和正确数约束的一组 source 历史记录。"""
    outcomes = ["UP"] * 10 + ["DOWN"] * 10
    rng.shuffle(outcomes)
    return make_history_from_outcomes(outcomes, correct_count, rng)


def make_history_from_outcomes(outcomes: list[str], correct_count: int, rng: random.Random) -> list[HistoryRecord]:
    """在固定 outcome 序列上改变预测，以配对比较 H60、H80 与 H90。"""
    if correct_count not in {12, 16, 18}:
        raise ValueError("correct_count must be one of 12, 16, 18")
    if len(outcomes) != 20 or outcomes.count("UP") != 10 or outcomes.count("DOWN") != 10:
        raise ValueError("outcomes must contain exactly 10 UP and 10 DOWN states")
    correct_buy_count = correct_count // 2
    up_indexes = [index for index, value in enumerate(outcomes) if value == "UP"]
    down_indexes = [index for index, value in enumerate(outcomes) if value == "DOWN"]
    buy_indexes = set(rng.sample(up_indexes, correct_buy_count))
    buy_indexes.update(rng.sample(down_indexes, 10 - correct_buy_count))
    records = [HistoryRecord(index, "BUY" if index - 1 in buy_indexes else "SELL", realized) for index, realized in enumerate(outcomes, start=1)]
    validate_history(records, correct_count)
    return records


def validate_history(records: list[HistoryRecord], correct_count: int) -> None:
    """阻止生成器静默放宽历史长度、方向平衡或目标正确数。"""
    if len(records) != 20:
        raise ValueError("history length must be 20")
    if sum(row.source_action == "BUY" for row in records) != 10:
        raise ValueError("history must have 10 BUY predictions")
    if sum(row.realized_state == "UP" for row in records) != 10:
        raise ValueError("history must have 10 UP outcomes")
    if sum(row.is_correct for row in records) != correct_count:
        raise ValueError("history correct count invariant failed")


def make_receiver_state(reference_state: str) -> tuple[PortfolioState, list[OwnTradeRecord]]:
    """构造四类可复算的资产路径，并保证 BUY 与 SELL 在每条 trial 中均可行。"""
    if reference_state not in REFERENCE_STATES:
        raise ValueError("unknown receiver reference-price state")
    specifications = {
        "G+": (90.0, 100.0, 80.0),
        "G-": (90.0, 120.0, 80.0),
        "L-": (110.0, 120.0, 100.0),
        "L+": (110.0, 120.0, 80.0),
    }
    cost_basis, all_time_high, all_time_low = specifications[reference_state]
    portfolio = PortfolioState(1000.0, 10, cost_basis, 100.0, all_time_high, all_time_low, reference_state)
    own_history = [
        OwnTradeRecord(period=1, action="BUY", quantity=5, execution_price=cost_basis),
        OwnTradeRecord(period=2, action="BUY", quantity=5, execution_price=cost_basis),
    ]
    validate_receiver_state(portfolio, own_history)
    return portfolio, own_history


def validate_receiver_state(portfolio: PortfolioState, own_history: list[OwnTradeRecord]) -> None:
    """核验个人历史、价格参照点与盈亏数值一致，且不需要强制交易警告。"""
    if portfolio.cash < portfolio.current_price or portfolio.inventory < 1:
        raise ValueError("every v2 trial must allow both one-unit BUY and SELL")
    if portfolio.all_time_low > portfolio.current_price or portfolio.all_time_high < portfolio.current_price:
        raise ValueError("current price must lie between all-time low and high")
    bought_quantity = sum(row.quantity for row in own_history if row.action == "BUY")
    weighted_cost = sum(row.quantity * row.execution_price for row in own_history if row.action == "BUY")
    if bought_quantity != portfolio.inventory or weighted_cost / bought_quantity != portfolio.average_cost_basis:
        raise ValueError("own trading history must reproduce inventory and average cost basis")
    expected_sign = 1 if portfolio.reference_price_state.startswith("G") else -1
    if portfolio.unrealized_gain_loss * expected_sign <= 0:
        raise ValueError("reference state must agree with unrealized gain/loss sign")


def generate_scenarios(config: dict) -> list[Scenario]:
    """生成 v2 的完整平衡组合：family、价格状态、两类方向与私人可靠度。"""
    if config.get("protocol_version") in PRIVATE_SIGNAL_PROTOCOLS:
        return generate_private_signal_scenarios(config)
    rng = random.Random(config["order_seed"])
    scenarios: list[Scenario] = []
    for family_number in range(1, config["history_families"] + 1):
        portfolio, own_history = make_receiver_state(REFERENCE_STATES[(family_number - 1) % len(REFERENCE_STATES)])
        outcomes = ["UP"] * 10 + ["DOWN"] * 10
        rng.shuffle(outcomes)
        histories = {f"H{pct}": make_history_from_outcomes(outcomes, count, rng) for pct, count in ((60, 12), (80, 16), (90, 18))}
        for private_direction in ("UP", "DOWN"):
            for source_action in ("BUY", "SELL"):
                for reliability in config["private_reliabilities"]:
                    scenarios.append(Scenario(f"family_{family_number:02d}", reliability, private_direction, source_action, portfolio, own_history, histories))
    return scenarios


def make_neutral_portfolio() -> PortfolioState:
    """构造阶段 B 的中性 portfolio：有足够现金与库存，但没有盈亏或价格路径线索。"""
    portfolio = PortfolioState(
        cash=1000.0,
        inventory=10,
        average_cost_basis=100.0,
        current_price=100.0,
        all_time_high=100.0,
        all_time_low=100.0,
        reference_price_state=None,
    )
    if portfolio.cash < portfolio.current_price or portfolio.inventory < 1:
        raise ValueError("neutral portfolio must allow both one-unit BUY and SELL")
    if portfolio.unrealized_gain_loss != 0:
        raise ValueError("neutral portfolio must have zero unrealized gain/loss")
    return portfolio


def make_unrealized_pnl_portfolios() -> dict[str, PortfolioState]:
    """构造浮盈、零盈亏、浮亏三种 portfolio；除平均成本价与盈亏外完全相同。"""
    portfolios = {
        "unrealized_gain": 90.0,
        "unrealized_neutral": 100.0,
        "unrealized_loss": 110.0,
    }
    result = {
        variant: PortfolioState(
            cash=1000.0,
            inventory=10,
            average_cost_basis=cost_basis,
            current_price=100.0,
            all_time_high=100.0,
            all_time_low=100.0,
            reference_price_state=None,
        )
        for variant, cost_basis in portfolios.items()
    }
    expected_pnl = {"unrealized_gain": 100.0, "unrealized_neutral": 0.0, "unrealized_loss": -100.0}
    for variant, portfolio in result.items():
        if portfolio.cash < portfolio.current_price or portfolio.inventory < 1:
            raise ValueError("unrealized-pnl portfolio must allow both one-unit BUY and SELL")
        if portfolio.unrealized_gain_loss != expected_pnl[variant]:
            raise ValueError("unrealized-pnl portfolio calculation invariant failed")
    return result


def make_all_time_range_portfolios() -> dict[str, PortfolioState]:
    """构造三种历史价格范围；成本价和未实现盈亏恒为中性，仅改变当前价在范围中的位置。"""
    ranges = {
        "at_all_time_high": (100.0, 80.0),
        "mid_price_range": (120.0, 80.0),
        "at_all_time_low": (120.0, 100.0),
    }
    result = {
        variant: PortfolioState(
            cash=1000.0,
            inventory=10,
            average_cost_basis=100.0,
            current_price=100.0,
            all_time_high=all_time_high,
            all_time_low=all_time_low,
            reference_price_state=None,
        )
        for variant, (all_time_high, all_time_low) in ranges.items()
    }
    for portfolio in result.values():
        if portfolio.cash < portfolio.current_price or portfolio.inventory < 1:
            raise ValueError("all-time-range portfolio must allow both one-unit BUY and SELL")
        if portfolio.unrealized_gain_loss != 0:
            raise ValueError("all-time-range portfolio must keep unrealized gain/loss neutral")
        if portfolio.all_time_low > portfolio.current_price or portfolio.all_time_high < portfolio.current_price:
            raise ValueError("current price must remain inside the displayed all-time range")
    return result


def generate_private_signal_scenarios(config: dict) -> list[Scenario]:
    """生成阶段 0/B 共用的私人信号条件；每个 context variant 都独立平衡。"""
    protocol = config["protocol_version"]
    if protocol == "refactor_phaseB_unrealized_pnl":
        variants = make_unrealized_pnl_portfolios().items()
    elif protocol == "refactor_phaseB_all_time_range":
        variants = make_all_time_range_portfolios().items()
    elif protocol == "refactor_phaseB_neutral_portfolio":
        variants = [("neutral_portfolio", make_neutral_portfolio())]
    else:
        variants = [("no_portfolio", None)]
    scenarios: list[Scenario] = []
    for variant, portfolio in variants:
        family_id = f"phaseB_{variant}" if portfolio else "phase0_baseline"
        for reliability in config["private_reliabilities"]:
            for private_direction in ("UP", "DOWN"):
                scenarios.append(
                    Scenario(
                        family_id=family_id,
                        private_reliability=reliability,
                        private_direction=private_direction,
                        source_action=None,
                        portfolio=portfolio,
                        own_history=[],
                        histories={},
                        context_variant=variant,
                    )
                )
    return scenarios


def make_trials(scenarios: list[Scenario], config: dict) -> list[Trial]:
    """展开处理与重复调用，并用独立随机种子打乱实际请求顺序。"""
    if config.get("protocol_version") in PRIVATE_SIGNAL_PROTOCOLS:
        return make_private_signal_trials(scenarios, config)
    trials: list[Trial] = []
    for scenario in scenarios:
        for treatment_id in config["treatments"]:
            for replicate_id in range(1, config["replicates"] + 1):
                trial_id = f"{scenario.family_id}_{scenario.portfolio.reference_price_state}_private{scenario.private_direction}_source{scenario.source_action}_q{scenario.private_reliability}_{treatment_id}_r{replicate_id}"
                trials.append(Trial(trial_id, scenario, treatment_id, replicate_id, -1))
    rng = random.Random(config["request_seed"])
    rng.shuffle(trials)
    return [Trial(item.trial_id, item.scenario, item.treatment_id, item.replicate_id, index) for index, item in enumerate(trials)]


def make_private_signal_trials(scenarios: list[Scenario], config: dict) -> list[Trial]:
    """仅按私人信号与 q 展开 B0，避免在不可见 source 条件上制造伪重复。"""
    trials: list[Trial] = []
    for scenario in scenarios:
        for replicate_id in range(1, config["replicates"] + 1):
            trial_id = (
                f"{scenario.family_id}_private{scenario.private_direction}_"
                f"q{scenario.private_reliability}_B0_r{replicate_id}"
            )
            trials.append(Trial(trial_id, scenario, "B0", replicate_id, -1))
    rng = random.Random(config["request_seed"])
    rng.shuffle(trials)
    return [Trial(item.trial_id, item.scenario, item.treatment_id, item.replicate_id, index) for index, item in enumerate(trials)]


def select_balanced_smoke_trials(trials: list[Trial], max_trials: int, config: dict) -> list[Trial]:
    """选择完整 family×replicate block，保留 v2 的方向与一致性平衡。"""
    if config.get("protocol_version") in PRIVATE_SIGNAL_PROTOCOLS:
        return select_private_signal_smoke_trials(trials, max_trials, config)
    block_size = len(config["private_reliabilities"]) * 2 * 2 * len(config["treatments"])
    if max_trials < block_size or max_trials % block_size:
        raise ValueError(f"--max-trials must be a multiple of {block_size}; each v2 smoke block contains one family, both private/source directions, all q values, and all treatments.")
    blocks: dict[tuple[str, int], list[Trial]] = {}
    for trial in trials:
        blocks.setdefault((trial.scenario.family_id, trial.replicate_id), []).append(trial)
    ordered_blocks = sorted(blocks.values(), key=lambda block: min(trial.order_index for trial in block))
    selected = [trial for block in ordered_blocks[: max_trials // block_size] for trial in block]
    return sorted(selected, key=lambda trial: trial.order_index)


def select_private_signal_smoke_trials(trials: list[Trial], max_trials: int, config: dict) -> list[Trial]:
    """按完整 context variant×方向×q block 选择阶段 0/B 的 smoke trial。"""
    block_size = len({(trial.scenario.context_variant, trial.scenario.private_reliability, trial.scenario.private_direction) for trial in trials})
    if max_trials < block_size or max_trials % block_size:
        raise ValueError(
            f"--max-trials must be a multiple of {block_size}; each private-signal block "
            "contains every context variant, both private directions, and all q values."
        )
    blocks: dict[int, list[Trial]] = {}
    for trial in trials:
        blocks.setdefault(trial.replicate_id, []).append(trial)
    ordered_blocks = sorted(blocks.values(), key=lambda block: min(trial.order_index for trial in block))
    selected = [trial for block in ordered_blocks[: max_trials // block_size] for trial in block]
    return sorted(selected, key=lambda trial: trial.order_index)

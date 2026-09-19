from __future__ import annotations

import random

from .schema import HistoryRecord, Scenario, Trial


def make_history(correct_count: int, rng: random.Random) -> list[HistoryRecord]:
    """Create a valid standalone history; paired families share outcomes.
        创建合法的独立历史；配对 family 共享同一 realized outcome 序列。
    """
    outcomes = ["UP"] * 10 + ["DOWN"] * 10
    # 打乱结果顺序，但可复现
    rng.shuffle(outcomes)
    return make_history_from_outcomes(outcomes, correct_count, rng)


def make_history_from_outcomes(outcomes: list[str], correct_count: int, rng: random.Random) -> list[HistoryRecord]:
    """Keep outcomes fixed while varying source predictions to achieve reliability.
        保持 outcome 不变，只改变 source prediction，以实现不同可靠度。
    """
    if correct_count not in {12, 16, 18}:
        raise ValueError("correct_count must be one of 12, 16, 18")
    if len(outcomes) != 20 or outcomes.count("UP") != 10 or outcomes.count("DOWN") != 10:
        raise ValueError("outcomes must contain exactly 10 UP and 10 DOWN states")
    correct_buy_count = correct_count // 2
    up_indexes = [index for index, value in enumerate(outcomes) if value == "UP"]
    down_indexes = [index for index, value in enumerate(outcomes) if value == "DOWN"]
    buy_indexes = set(rng.sample(up_indexes, correct_buy_count))
    buy_indexes.update(rng.sample(down_indexes, 10 - correct_buy_count))
    records: list[HistoryRecord] = []
    for index, realized in enumerate(outcomes, start=1):
        action = "BUY" if index - 1 in buy_indexes else "SELL"
        records.append(HistoryRecord(index, action, realized))
    validate_history(records, correct_count)
    return records


def validate_history(records: list[HistoryRecord], correct_count: int) -> None:
    if len(records) != 20:
        raise ValueError("history length must be 20")
    if sum(row.source_action == "BUY" for row in records) != 10:
        raise ValueError("history must have 10 BUY predictions")
    if sum(row.realized_state == "UP" for row in records) != 10:
        raise ValueError("history must have 10 UP outcomes")
    if sum(row.is_correct for row in records) != correct_count:
        raise ValueError("history correct count invariant failed")


def generate_scenarios(config: dict) -> list[Scenario]:
    rng = random.Random(config["order_seed"])
    scenarios: list[Scenario] = []
    for family_number in range(1, config["history_families"] + 1):
        outcomes = ["UP"] * 10 + ["DOWN"] * 10
        rng.shuffle(outcomes)
        histories = {f"H{pct}": make_history_from_outcomes(outcomes, count, rng) for pct, count in ((60, 12), (80, 16), (90, 18))}
        for private_direction in ("UP", "DOWN"):
            source_action = "SELL" if private_direction == "UP" else "BUY"
            for q in config["private_reliabilities"]:
                scenarios.append(Scenario(f"family_{family_number:02d}", private_direction, q, private_direction, source_action, histories))
    return scenarios


def make_trials(scenarios: list[Scenario], config: dict) -> list[Trial]:
    trials: list[Trial] = []
    for scenario in scenarios:
        for treatment_id in config["treatments"]:
            for replicate_id in range(1, config["replicates"] + 1):
                trial_id = f"{scenario.family_id}_{scenario.direction}_q{scenario.private_reliability}_{treatment_id}_r{replicate_id}"
                trials.append(Trial(trial_id, scenario, treatment_id, replicate_id, -1))
    rng = random.Random(config["request_seed"])
    rng.shuffle(trials)
    return [Trial(item.trial_id, item.scenario, item.treatment_id, item.replicate_id, index) for index, item in enumerate(trials)]


def select_balanced_smoke_trials(trials: list[Trial], max_trials: int, config: dict) -> list[Trial]:
    """选择完整的 family × replicate block，避免 smoke test 破坏主配对设计。"""
    block_size = len(config["private_reliabilities"]) * 2 * len(config["treatments"])
    if max_trials < block_size or max_trials % block_size:
        raise ValueError(
            f"--max-trials must be a multiple of {block_size}; "
            "each smoke block contains one family, two directions, two q values, and all treatments."
        )
    # 根据随机队列中最早出现的位置排列 block，保留请求顺序的随机性。
    blocks: dict[tuple[str, int], list[Trial]] = {}
    for trial in trials:
        blocks.setdefault((trial.scenario.family_id, trial.replicate_id), []).append(trial)
    ordered_blocks = sorted(blocks.values(), key=lambda block: min(trial.order_index for trial in block))
    selected = [trial for block in ordered_blocks[: max_trials // block_size] for trial in block]
    # 重新交错已选 trial，避免同一 treatment 连续调用。
    return sorted(selected, key=lambda trial: trial.order_index)

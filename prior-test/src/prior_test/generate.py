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

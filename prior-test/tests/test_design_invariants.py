import random

from prior_test.generate import REFERENCE_STATES, generate_scenarios, make_history, make_trials, select_balanced_smoke_trials, validate_history, validate_receiver_state
from prior_test.render import render_user_context


def config():
    """提供最小 v2 配置，使每个测试只关注一个设计不变量。"""
    return {"order_seed": 1, "request_seed": 2, "history_families": 4, "private_reliabilities": [.65, .85], "treatments": {"B0": None, "B1": None, "H60": 12, "H80": 16, "H90": 18}, "replicates": 2}


def test_history_constraints():
    """三种声誉历史均须保持相同长度和方向配额。"""
    for count in (12, 16, 18):
        validate_history(make_history(count, random.Random(count)), count)


def test_receiver_state_is_recomputable_and_two_actions_are_feasible():
    """所有价格状态都不能触发强制买卖或负余额警告。"""
    scenarios = generate_scenarios(config())
    assert {scenario.portfolio.reference_price_state for scenario in scenarios} == set(REFERENCE_STATES)
    for scenario in scenarios:
        validate_receiver_state(scenario.portfolio, scenario.own_history)
        assert scenario.portfolio.cash >= scenario.portfolio.current_price
        assert scenario.portfolio.inventory >= 1


def test_treatments_do_not_leak_hidden_labels_and_keep_receiver_state():
    """B0 只删除 source，不能删除 receiver 的共同经济背景。"""
    scenario = generate_scenarios(config())[0]
    trials = {trial.treatment_id: trial for trial in make_trials([scenario], config())}
    b0_context = render_user_context(trials["B0"])
    assert "source:" not in b0_context
    assert "portfolio:" in b0_context and "own_trading_history:" in b0_context
    assert "must BUY" not in b0_context and "must SELL" not in b0_context
    assert "  history:" not in render_user_context(trials["B1"])
    context = render_user_context(trials["H90"])
    assert "  history:" in context
    assert "H90" not in context and "correct_count" not in context and "hidden" not in context


def test_paired_history_treatments_share_realized_outcomes():
    """同一 family 的三个历史处理必须共享同一 outcome 序列。"""
    histories = generate_scenarios(config())[0].histories
    sequences = [[row.realized_state for row in histories[treatment]] for treatment in ("H60", "H80", "H90")]
    assert sequences[0] == sequences[1] == sequences[2]


def test_private_source_directions_are_balanced():
    """每个 family 必须同时包含四个方向组合及两类信号关系。"""
    scenarios = [scenario for scenario in generate_scenarios(config()) if scenario.family_id == "family_01"]
    assert {(scenario.private_direction, scenario.source_action) for scenario in scenarios} == {("UP", "BUY"), ("UP", "SELL"), ("DOWN", "BUY"), ("DOWN", "SELL")}
    assert {scenario.signal_relation for scenario in scenarios} == {"agreement", "conflict"}


def test_context_uses_v2_protocol_field_order():
    """公开 context 的开头字段固定，保证处理组只在批准字段上不同。"""
    context = render_user_context(make_trials([generate_scenarios(config())[0]], config())[0])
    assert context.startswith("(Information for this decision)\nasset_id: SYNTH_1\ncurrent_price: 100\nall_time_high:")


def test_information_block_order_is_explicit_and_validated():
    """开发阶段可以切换信息块顺序，但非法取值必须立即失败。"""
    trial = make_trials([generate_scenarios(config())[0]], config())[0]
    reverse_context = render_user_context(trial, "source_then_private")
    assert reverse_context.index("source:") < reverse_context.index("private_signal:")
    try:
        render_user_context(trial, "unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("非法信息块顺序必须被拒绝")


def test_smoke_selection_keeps_complete_v2_block():
    """40 条 smoke block 必须保留一个 family 的全部方向、q 和 treatment。"""
    cfg = config()
    selected = select_balanced_smoke_trials(make_trials(generate_scenarios(cfg), cfg), 40, cfg)
    assert len(selected) == 40
    assert len({trial.scenario.family_id for trial in selected}) == 1
    assert {trial.treatment_id for trial in selected} == {"B0", "B1", "H60", "H80", "H90"}
    assert {(trial.scenario.private_direction, trial.scenario.source_action) for trial in selected} == {("UP", "BUY"), ("UP", "SELL"), ("DOWN", "BUY"), ("DOWN", "SELL")}

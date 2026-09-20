import random
import json

from prior_test.client import OllamaClient
from prior_test.generate import REFERENCE_STATES, generate_scenarios, make_history, make_neutral_portfolio, make_trials, select_balanced_smoke_trials, validate_history, validate_receiver_state
from prior_test.render import render_context, render_user_context
from prior_test.runner import run


def config():
    """提供最小 v2 配置，使每个测试只关注一个设计不变量。"""
    return {"order_seed": 1, "request_seed": 2, "history_families": 4, "private_reliabilities": [.65, .85], "treatments": {"B0": None, "B1": None, "H60": 12, "H80": 16, "H90": 18}, "replicates": 2}


def phase0_config(replicates: int = 2):
    """提供阶段 0 的最小配置，用于验证公开条件和审计产物。"""
    return {
        "protocol_version": "refactor_phase0",
        "private_reliabilities": [.65, .85],
        "treatments": {"B0": None},
        "replicates": replicates,
        "order_seed": 1,
        "request_seed": 2,
        "max_attempts": 1,
        "base_url": "http://localhost:11434/v1",
        "model": "mock-model",
        "temperature": .2,
        "max_tokens": 64,
        "thinking": False,
        "context_blocks": ["core_task", "private_signal"],
    }


def phase_b_neutral_portfolio_config(replicates: int = 2):
    """提供阶段 B 第一个消融块的配置，并保持阶段 0 的核心任务参数不变。"""
    cfg = phase0_config(replicates)
    cfg["protocol_version"] = "refactor_phaseB_neutral_portfolio"
    cfg["context_blocks"] = ["core_task", "neutral_portfolio", "private_signal"]
    return cfg


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


def test_phase0_has_only_four_public_conditions_and_no_source_pseudoreplication():
    """阶段 0 只能按私人方向与 q 生成条件，重复调用不应引入隐藏 source 条件。"""
    cfg = phase0_config()
    trials = make_trials(generate_scenarios(cfg), cfg)
    assert len(trials) == 8
    assert {trial.treatment_id for trial in trials} == {"B0"}
    assert {trial.scenario.source_action for trial in trials} == {None}
    contexts = {render_context(trial, cfg) for trial in trials}
    assert len(contexts) == 4
    assert all("source:" not in context and "portfolio:" not in context for context in contexts)
    assert all("reference_price_state" not in context for context in contexts)


def test_phase0_smoke_selection_keeps_private_direction_and_q_balanced():
    """阶段 0 的最小 smoke block 必须同时覆盖两种私人方向与全部 q。"""
    cfg = phase0_config()
    selected = select_balanced_smoke_trials(make_trials(generate_scenarios(cfg), cfg), 4, cfg)
    assert len(selected) == 4
    assert {(trial.scenario.private_direction, trial.scenario.private_reliability) for trial in selected} == {
        ("UP", .65), ("UP", .85), ("DOWN", .65), ("DOWN", .85)
    }


def test_phase_b_neutral_portfolio_is_feasible_and_has_no_price_path_label():
    """阶段 B 的首个 block 只能加入零盈亏 portfolio，不得泄漏价格路径或社会信息。"""
    portfolio = make_neutral_portfolio()
    assert portfolio.cash >= portfolio.current_price
    assert portfolio.inventory >= 1
    assert portfolio.average_cost_basis == portfolio.current_price
    assert portfolio.unrealized_gain_loss == 0
    assert portfolio.reference_price_state is None
    cfg = phase_b_neutral_portfolio_config()
    trials = make_trials(generate_scenarios(cfg), cfg)
    contexts = {render_context(trial, cfg) for trial in trials}
    assert len(contexts) == 4
    assert all("portfolio:" in context and "unrealized_gain_loss: 0" in context for context in contexts)
    assert all("source:" not in context and "own_trading_history:" not in context for context in contexts)
    assert all("all_time_high" not in context and "reference_price_state" not in context for context in contexts)


def test_phase_b_mock_run_uses_private_signal_analysis_and_records_neutral_block(tmp_path):
    """阶段 B 的汇总与图表必须沿用私人信号口径，并记录新增的唯一 context block。"""
    cfg = phase_b_neutral_portfolio_config()
    output = tmp_path / "phaseB"
    run(cfg, "Return JSON only.", output, "mock", None)
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    prompts = (output / "prompts.jsonl").read_text(encoding="utf-8").splitlines()
    assert summary["analysis_kind"] == "refactor_private_signal_protocol"
    assert summary["protocol_version"] == "refactor_phaseB_neutral_portfolio"
    assert all('"neutral_portfolio"' in row for row in prompts)
    assert (output / "figures/private_signal_consistency.png").exists()


def test_phase0_mock_run_records_seed_and_writes_phase_specific_artifacts(tmp_path):
    """阶段 0 运行必须记录每次请求 seed，并产生私有信号审计图表而非 v2 图表。"""
    cfg = phase0_config()
    output = tmp_path / "phase0"
    run(cfg, "Return JSON only.", output, "mock", None)
    decisions = (output / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    raw_attempts = (output / "raw_attempts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(decisions) == len(raw_attempts) == 8
    assert all('"final_seed"' in row for row in decisions)
    assert all('"attempt_seed"' in row for row in raw_attempts)
    assert (output / "figures/private_signal_consistency.png").exists()
    assert not (output / "figures/source_following_conflict_rates.png").exists()


def test_ollama_native_payload_carries_seed():
    """thinking 模式下也必须把审计 seed 传给 Ollama 原生采样选项。"""
    client = object.__new__(OllamaClient)
    client.model, client.temperature, client.max_tokens, client.thinking = "qwen3:8b", .2, 64, False
    payload = client._native_payload("system", "context", 12345)
    assert payload["options"]["seed"] == 12345

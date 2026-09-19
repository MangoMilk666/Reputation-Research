import random

from prior_test.generate import generate_scenarios, make_history, make_trials, select_balanced_smoke_trials, validate_history
from prior_test.render import render_user_context


def config():
    return {"order_seed": 1, "request_seed": 2, "history_families": 2, "private_reliabilities": [.65, .85], "treatments": {"B0": None, "B1": None, "H60": 12, "H80": 16, "H90": 18}, "replicates": 2}


def test_history_constraints():
    for count in (12, 16, 18):
        validate_history(make_history(count, random.Random(count)), count)


def test_treatments_do_not_leak_hidden_state_or_labels():
    scenario = generate_scenarios(config())[0]
    trials = {trial.treatment_id: trial for trial in make_trials([scenario], config())}
    assert "source" not in render_user_context(trials["B0"])
    assert "  history:" not in render_user_context(trials["B1"])
    context = render_user_context(trials["H90"])
    assert "  history:" in context
    assert "H90" not in context and "correct_count" not in context and "hidden" not in context


def test_paired_history_treatments_share_realized_outcomes():
    histories = generate_scenarios(config())[0].histories
    realized_sequences = [[row.realized_state for row in histories[treatment]] for treatment in ("H60", "H80", "H90")]
    assert realized_sequences[0] == realized_sequences[1] == realized_sequences[2]


def test_context_uses_protocol_field_order():
    context = render_user_context(make_trials([generate_scenarios(config())[0]], config())[0])
    assert context.startswith("(Information for this decision)\nasset_id: SYNTH_1\ncurrent_price: 100")


def test_smoke_selection_keeps_a_complete_paired_block():
    cfg = config()
    selected = select_balanced_smoke_trials(make_trials(generate_scenarios(cfg), cfg), 20, cfg)
    assert len(selected) == 20
    assert len({trial.scenario.family_id for trial in selected}) == 1
    assert {trial.treatment_id for trial in selected} == {"B0", "B1", "H60", "H80", "H90"}

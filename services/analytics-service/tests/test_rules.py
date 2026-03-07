from analytics_service.rules import SessionSignalSnapshot, evaluate_coaching, evaluate_diagnostics


def test_rules_produce_expected_coaching() -> None:
    snapshot = SessionSignalSnapshot(
        brake_release_variance=0.5,
        rear_slip_events=4,
        early_throttle_pct=0.6,
        exit_speed_delta_kmh=-7,
    )
    messages = evaluate_coaching(snapshot)
    assert len(messages) == 3


def test_rules_produce_diagnostics() -> None:
    snapshot = SessionSignalSnapshot(rear_slip_events=5, exit_speed_delta_kmh=-9)
    diagnostics = evaluate_diagnostics(snapshot)
    assert len(diagnostics) >= 1

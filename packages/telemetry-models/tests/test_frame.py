from datetime import UTC, datetime

import pytest
from telemetry_models import TelemetryFrame, WheelValues


def test_frame_model_creation() -> None:
    frame = TelemetryFrame(received_at=datetime.now(UTC), frame_index=1, gear=3)
    assert frame.frame_index == 1
    assert frame.gear == 3


def test_frame_rejects_invalid_throttle() -> None:
    with pytest.raises(ValueError):
        TelemetryFrame(
            received_at=datetime.now(UTC),
            frame_index=1,
            throttle=1.5,
        )


def test_frame_contains_wheel_value_contract() -> None:
    frame = TelemetryFrame(
        received_at=datetime.now(UTC),
        frame_index=1,
        tire_slip=WheelValues(fl=0.1, fr=0.2, rl=0.3, rr=0.4),
    )
    assert frame.tire_slip.rr == 0.4

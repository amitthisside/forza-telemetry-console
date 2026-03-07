from datetime import UTC, datetime

from telemetry_models import TelemetryFrame


def test_frame_model_creation() -> None:
    frame = TelemetryFrame(received_at=datetime.now(UTC), frame_index=1)
    assert frame.frame_index == 1

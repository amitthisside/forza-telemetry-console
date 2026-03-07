from datetime import UTC, datetime

import pytest
from event_contracts import (
    SUBJECTS,
    CoachingMessageEvent,
    SessionEvent,
    SessionEventType,
    Severity,
    TelemetryFrameEvent,
)
from telemetry_models import TelemetryFrame


def test_subject_registry_contains_core_channels() -> None:
    assert SUBJECTS["telemetry_frame"] == "telemetry.frame.v1"
    assert SUBJECTS["coaching"] == "coaching.event.v1"


def test_telemetry_event_envelope_contract() -> None:
    frame = TelemetryFrame(received_at=datetime.now(UTC), frame_index=1)
    event = TelemetryFrameEvent(
        event_id="evt-1",
        published_at=datetime.now(UTC),
        frame=frame,
    )
    assert event.source == "telemetry-ingest"


def test_session_event_validates_lap_number() -> None:
    with pytest.raises(ValueError):
        SessionEvent(
            event_id="evt-2",
            published_at=datetime.now(UTC),
            event_type=SessionEventType.LAP_STARTED,
            session_id="s-1",
            lap_number=-1,
        )


def test_coaching_message_confidence_bounds() -> None:
    with pytest.raises(ValueError):
        CoachingMessageEvent(
            event_id="evt-3",
            published_at=datetime.now(UTC),
            session_id="s-1",
            rule_id="rule-1",
            message="late braking",
            severity=Severity.MEDIUM,
            confidence=1.5,
        )

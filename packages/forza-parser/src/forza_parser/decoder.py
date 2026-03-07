from datetime import UTC, datetime

from telemetry_models import TelemetryFrame

EXPECTED_MIN_PACKET_BYTES = 64


def decode_packet(packet: bytes, frame_index: int) -> TelemetryFrame:
    if len(packet) < EXPECTED_MIN_PACKET_BYTES:
        raise ValueError("packet too small for Forza telemetry format")

    return TelemetryFrame(received_at=datetime.now(UTC), frame_index=frame_index)

import math
import struct
from datetime import UTC, datetime

from telemetry_models import Orientation, TelemetryFrame, Vector3, WheelValues

SUPPORTED_PACKET_SIZES = frozenset({232, 311, 324})

_SLED_PACKET_SIZE = 232


def _float_at(packet: bytes, offset: int) -> float:
    return struct.unpack_from("<f", packet, offset)[0]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def decode_packet(packet: bytes, frame_index: int) -> TelemetryFrame:
    packet_size = len(packet)
    if packet_size not in SUPPORTED_PACKET_SIZES:
        raise ValueError(f"unsupported Forza telemetry packet size: {packet_size}")

    current_engine_rpm = _float_at(packet, 16)
    velocity_x = _float_at(packet, 32)
    velocity_y = _float_at(packet, 36)
    velocity_z = _float_at(packet, 40)

    speed_from_velocity_kmh = math.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2) * 3.6

    # Data Out formats provide direct speed and world position fields after the Sled layout.
    has_extended_layout = packet_size > _SLED_PACKET_SIZE
    position = Vector3()
    speed_kmh = speed_from_velocity_kmh
    if has_extended_layout:
        position = Vector3(
            x=_float_at(packet, 252),
            y=_float_at(packet, 256),
            z=_float_at(packet, 260),
        )
        speed_kmh = max(0.0, _float_at(packet, 264) * 3.6)

    return TelemetryFrame(
        received_at=datetime.now(UTC),
        frame_index=frame_index,
        speed=max(0.0, speed_kmh),
        rpm=max(0.0, current_engine_rpm),
        gear=0,
        throttle=0.0,
        brake=0.0,
        steering=_clamp(_float_at(packet, 52) / 10.0, -1.0, 1.0),
        world_position=position,
        orientation=Orientation(
            yaw=_float_at(packet, 56),
            pitch=_float_at(packet, 60),
            roll=_float_at(packet, 64),
        ),
        tire_slip=WheelValues(
            fl=_float_at(packet, 84),
            fr=_float_at(packet, 88),
            rl=_float_at(packet, 92),
            rr=_float_at(packet, 96),
        ),
        wheel_rotation_speed=WheelValues(
            fl=_float_at(packet, 100),
            fr=_float_at(packet, 104),
            rl=_float_at(packet, 108),
            rr=_float_at(packet, 112),
        ),
        acceleration=Vector3(
            x=_float_at(packet, 20),
            y=_float_at(packet, 24),
            z=_float_at(packet, 28),
        ),
    )

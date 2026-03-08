import math
import struct
from datetime import UTC, datetime

from telemetry_models import Orientation, TelemetryFrame, Vector3, WheelValues

SUPPORTED_PACKET_SIZES = frozenset({232, 311, 324})

_SLED_PACKET_SIZE = 232


def _float_at(packet: bytes, offset: int) -> float:
    return struct.unpack_from("<f", packet, offset)[0]


def _uint8_at(packet: bytes, offset: int) -> int:
    return struct.unpack_from("<B", packet, offset)[0]


def _int8_at(packet: bytes, offset: int) -> int:
    return struct.unpack_from("<b", packet, offset)[0]


def _uint16_at(packet: bytes, offset: int) -> int:
    return struct.unpack_from("<H", packet, offset)[0]


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

    # Data Out/Data Out Dash layouts provide direct world position and control fields.
    has_extended_layout = packet_size >= 311
    position = Vector3()
    speed_kmh = speed_from_velocity_kmh
    throttle = 0.0
    brake = 0.0
    clutch = None
    gear = 0
    steering = _clamp(_float_at(packet, 52) / 10.0, -1.0, 1.0)
    lap_number = None
    lap_time_ms = None
    current_race_time_ms = None
    lap_distance = None
    if has_extended_layout:
        # Reference: Forza Data Out packet fields (offsets from packet start).
        position = Vector3(
            x=_float_at(packet, 232),
            y=_float_at(packet, 236),
            z=_float_at(packet, 240),
        )
        speed_kmh = max(0.0, _float_at(packet, 244) * 3.6)
        lap_distance = max(0.0, _float_at(packet, 280))
        lap_time_ms = max(0, int(_float_at(packet, 292) * 1000.0))
        current_race_time_ms = max(0, int(_float_at(packet, 296) * 1000.0))
        lap_number = _uint16_at(packet, 300)

        throttle = _clamp(_uint8_at(packet, 303) / 255.0, 0.0, 1.0)
        brake = _clamp(_uint8_at(packet, 304) / 255.0, 0.0, 1.0)
        clutch = _clamp(_uint8_at(packet, 305) / 255.0, 0.0, 1.0)
        gear = _uint8_at(packet, 307)
        steering = _clamp(_int8_at(packet, 308) / 127.0, -1.0, 1.0)

    return TelemetryFrame(
        received_at=datetime.now(UTC),
        frame_index=frame_index,
        speed=max(0.0, speed_kmh),
        rpm=max(0.0, current_engine_rpm),
        gear=gear,
        throttle=throttle,
        brake=brake,
        steering=steering,
        clutch=clutch,
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
        current_race_time_ms=current_race_time_ms,
        lap_distance=lap_distance,
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

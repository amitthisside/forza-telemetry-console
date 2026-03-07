import struct

import pytest
from forza_parser import SUPPORTED_PACKET_SIZES, decode_packet


def _sled_packet() -> bytes:
    packet = bytearray(232)
    struct.pack_into("<f", packet, 16, 4200.0)
    struct.pack_into("<f", packet, 32, 10.0)
    struct.pack_into("<f", packet, 36, 0.0)
    struct.pack_into("<f", packet, 40, 0.0)
    struct.pack_into("<f", packet, 56, 1.1)
    struct.pack_into("<f", packet, 60, 2.2)
    struct.pack_into("<f", packet, 64, 3.3)
    struct.pack_into("<f", packet, 84, 0.1)
    struct.pack_into("<f", packet, 88, 0.2)
    struct.pack_into("<f", packet, 92, 0.3)
    struct.pack_into("<f", packet, 96, 0.4)
    return bytes(packet)


def _data_out_packet() -> bytes:
    packet = bytearray(311)
    struct.pack_into("<f", packet, 16, 5100.0)
    struct.pack_into("<f", packet, 252, 123.0)
    struct.pack_into("<f", packet, 256, 456.0)
    struct.pack_into("<f", packet, 260, 789.0)
    struct.pack_into("<f", packet, 264, 50.0)
    return bytes(packet)


def test_decode_packet_validates_size() -> None:
    with pytest.raises(ValueError):
        decode_packet(b"tiny", 1)


def test_decode_packet_extracts_sled_values() -> None:
    frame = decode_packet(_sled_packet(), 4)
    assert frame.frame_index == 4
    assert frame.rpm == 4200.0
    assert frame.orientation.yaw == pytest.approx(1.1)
    assert frame.tire_slip.rr == pytest.approx(0.4)


def test_supported_packet_sizes_contract() -> None:
    assert SUPPORTED_PACKET_SIZES == frozenset({232, 311, 324})


def test_decode_packet_extracts_data_out_speed_and_position() -> None:
    frame = decode_packet(_data_out_packet(), 7)
    assert frame.rpm == 5100.0
    assert frame.speed == pytest.approx(180.0)
    assert frame.world_position.x == pytest.approx(123.0)

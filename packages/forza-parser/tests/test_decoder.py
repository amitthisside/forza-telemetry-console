import pytest
from forza_parser import decode_packet


def test_decode_packet_validates_size() -> None:
    with pytest.raises(ValueError):
        decode_packet(b"tiny", 1)

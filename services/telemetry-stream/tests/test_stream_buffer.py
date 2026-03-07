from telemetry_stream.ring_buffer import FrameRingBuffer


def test_ring_buffer_limit() -> None:
    buffer = FrameRingBuffer(capacity=2)
    buffer.append({"frame": 1})
    buffer.append({"frame": 2})
    buffer.append({"frame": 3})

    assert buffer.recent(10) == [{"frame": 2}, {"frame": 3}]

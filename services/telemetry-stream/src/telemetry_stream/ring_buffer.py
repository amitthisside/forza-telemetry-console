from collections import deque


class FrameRingBuffer:
    def __init__(self, capacity: int) -> None:
        self._frames: deque[dict[str, object]] = deque(maxlen=capacity)

    def append(self, frame: dict[str, object]) -> None:
        self._frames.append(frame)

    def recent(self, limit: int) -> list[dict[str, object]]:
        if limit <= 0:
            return []
        return list(self._frames)[-limit:]

    def __len__(self) -> int:
        return len(self._frames)

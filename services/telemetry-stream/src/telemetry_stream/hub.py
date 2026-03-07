import asyncio
from collections import defaultdict


class WebSocketHub:
    def __init__(self, queue_size: int) -> None:
        self._queue_size = queue_size
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, object]]]] = defaultdict(set)

    def subscribe(self, channel: str) -> asyncio.Queue[dict[str, object]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(maxsize=self._queue_size)
        self._subscribers[channel].add(queue)
        return queue

    def unsubscribe(self, channel: str, queue: asyncio.Queue[dict[str, object]]) -> None:
        subscribers = self._subscribers.get(channel)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(channel, None)

    def broadcast(self, channel: str, message: dict[str, object]) -> int:
        delivered = 0
        for queue in list(self._subscribers.get(channel, set())):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(message)
                delivered += 1
            except asyncio.QueueFull:
                continue
        return delivered

    def subscriber_count(self, channel: str) -> int:
        return len(self._subscribers.get(channel, set()))

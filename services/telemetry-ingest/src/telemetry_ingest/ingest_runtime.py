import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from event_contracts import TelemetryFrameEvent
from forza_parser import decode_packet

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    packets_received: int = 0
    packets_decoded: int = 0
    parser_errors: int = 0
    events_published: int = 0
    publish_errors: int = 0


class TelemetryDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        stats: IngestStats,
        source: str,
        session_id: str,
        event_publisher: Callable[[TelemetryFrameEvent], None] | None = None,
    ) -> None:
        self.stats = stats
        self.source = source
        self.session_id = session_id
        self.event_publisher = event_publisher

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.stats.packets_received += 1
        try:
            frame = decode_packet(data, self.stats.packets_received)
        except ValueError as exc:
            self.stats.parser_errors += 1
            logger.debug("Failed to decode packet from %s:%s: %s", addr[0], addr[1], exc)
            return

        self.stats.packets_decoded += 1
        if self.event_publisher is not None:
            try:
                event = TelemetryFrameEvent(
                    event_id=f"evt-{self.stats.packets_received}",
                    published_at=frame.received_at,
                    source=self.source,
                    session_id=self.session_id,
                    frame=frame,
                )
                self.event_publisher(event)
                self.stats.events_published += 1
            except Exception as exc:  # pragma: no cover - safeguard path
                self.stats.publish_errors += 1
                logger.warning("Failed to publish frame event: %s", exc)


async def start_udp_listener(
    bind_host: str,
    bind_port: int,
    stats: IngestStats,
    source: str,
    session_id: str,
    event_publisher: Callable[[TelemetryFrameEvent], None] | None = None,
) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    transport, _protocol = await loop.create_datagram_endpoint(
        lambda: TelemetryDatagramProtocol(
            stats,
            source=source,
            session_id=session_id,
            event_publisher=event_publisher,
        ),
        local_addr=(bind_host, bind_port),
    )
    return cast(asyncio.DatagramTransport, transport)

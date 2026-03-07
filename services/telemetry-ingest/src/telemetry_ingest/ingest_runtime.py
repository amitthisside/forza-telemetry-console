import asyncio
import logging
from dataclasses import dataclass
from typing import cast

from forza_parser import decode_packet

logger = logging.getLogger(__name__)


@dataclass
class IngestStats:
    packets_received: int = 0
    packets_decoded: int = 0
    parser_errors: int = 0


class TelemetryDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, stats: IngestStats) -> None:
        self.stats = stats

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.stats.packets_received += 1
        try:
            decode_packet(data, self.stats.packets_received)
        except ValueError as exc:
            self.stats.parser_errors += 1
            logger.debug("Failed to decode packet from %s:%s: %s", addr[0], addr[1], exc)
            return

        self.stats.packets_decoded += 1


async def start_udp_listener(
    bind_host: str,
    bind_port: int,
    stats: IngestStats,
) -> asyncio.DatagramTransport:
    loop = asyncio.get_running_loop()
    transport, _protocol = await loop.create_datagram_endpoint(
        lambda: TelemetryDatagramProtocol(stats),
        local_addr=(bind_host, bind_port),
    )
    return cast(asyncio.DatagramTransport, transport)

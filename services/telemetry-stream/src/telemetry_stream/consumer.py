import asyncio
import json
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


async def consume_telemetry_subject(
    nats_url: str,
    subject: str,
    on_frame: Callable[[dict[str, object]], None],
    stop_event: asyncio.Event,
) -> None:
    import nats

    while not stop_event.is_set():
        try:
            nc = await nats.connect(servers=[nats_url], name="telemetry-stream")
            logger.info("Connected to NATS at %s", nats_url)
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("NATS connect failed: %s", exc)
            await asyncio.sleep(2)
            continue

        try:
            async def _handler(msg) -> None:
                try:
                    payload = json.loads(msg.data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    logger.debug("Dropping non-JSON message on %s", msg.subject)
                    return

                if isinstance(payload, dict):
                    on_frame(payload)

            subscription = await nc.subscribe(subject, cb=_handler)
            logger.info("Subscribed to %s", subject)

            while not stop_event.is_set():
                await asyncio.sleep(0.25)

            await subscription.unsubscribe()
        finally:
            await nc.close()

    logger.info("NATS consumer stopped")

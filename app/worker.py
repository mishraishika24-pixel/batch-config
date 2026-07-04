"""Worker process entrypoint.

Runs a simple poll loop against Postgres: claim a small batch of PENDING
items (`SELECT ... FOR UPDATE SKIP LOCKED`), process them, repeat. When
the queue is empty it backs off for `worker_poll_interval_seconds` instead
of hot-looping. Stateless and horizontally scalable: run as many of these
as needed, they safely share the same queue.

Run with: python -m app.worker
"""

import logging
import signal
import time
from types import FrameType

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import SessionLocal
from app.repositories.batch_repository import BatchRepository
from app.services.item_processor import SimulatedItemProcessor
from app.services.worker_service import WorkerService

logger = logging.getLogger(__name__)

_shutdown_requested = False


def _handle_shutdown_signal(signum: int, frame: FrameType | None) -> None:
    global _shutdown_requested
    logger.info("shutdown_signal_received", extra={"signal": signum})
    _shutdown_requested = True


def run() -> None:
    configure_logging()
    settings = get_settings()
    processor = SimulatedItemProcessor()

    # SIGTERM: how container orchestrators (Docker, k8s) ask a process to
    # stop. Handling it lets the current claimed items finish their commit
    # before exiting, instead of being killed mid-transaction.
    signal.signal(signal.SIGTERM, _handle_shutdown_signal)
    signal.signal(signal.SIGINT, _handle_shutdown_signal)

    logger.info(
        "worker_started",
        extra={
            "poll_interval_seconds": settings.worker_poll_interval_seconds,
            "claim_batch_size": settings.worker_claim_batch_size,
        },
    )

    while not _shutdown_requested:
        session = SessionLocal()
        try:
            worker_service = WorkerService(BatchRepository(session), processor, settings)
            claimed = worker_service.process_once()
        except Exception:
            # A DB blip or unexpected bug must not crash the process; log,
            # back off, and let the next iteration retry.
            logger.exception("worker_iteration_failed")
            claimed = 0
        finally:
            session.close()

        if claimed == 0 and not _shutdown_requested:
            time.sleep(settings.worker_poll_interval_seconds)

    logger.info("worker_stopped")


if __name__ == "__main__":
    run()

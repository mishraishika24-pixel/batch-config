"""Pluggable per-item processing logic.

The problem statement ("batch processing system") is domain-agnostic, so
the actual unit of work is intentionally abstracted behind this interface.
In a real system, `SimulatedItemProcessor` would be replaced with whatever
the batch items actually need done (e.g. sending emails, transforming
records, calling a downstream API) -- the worker, retry, and status-
tracking machinery around it stays the same.
"""

from abc import ABC, abstractmethod
from typing import Any


class ItemProcessingError(Exception):
    """Raised by an ItemProcessor when a single item cannot be processed.

    Isolated to one item: it must never abort processing of the rest of
    the batch.
    """


class ItemProcessor(ABC):
    @abstractmethod
    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Process a single item's payload and return a JSON-serializable result.

        Raise ItemProcessingError for expected, item-specific failures.
        """


class SimulatedItemProcessor(ItemProcessor):
    """Deterministic stand-in for real business logic.

    Contract (documented so it's trivially testable and demoable):
      - payload `{"simulate_failure": true, "failure_reason": "..."}`
        raises ItemProcessingError, to exercise failure handling end to end.
      - otherwise, echoes the payload back and, if a string `value` field
        is present, adds an uppercased `processed_value`.
    """

    def process(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("simulate_failure"):
            raise ItemProcessingError(
                str(payload.get("failure_reason", "simulated processing failure"))
            )

        result: dict[str, Any] = {"echo": payload}
        value = payload.get("value")
        if isinstance(value, str):
            result["processed_value"] = value.upper()
        return result

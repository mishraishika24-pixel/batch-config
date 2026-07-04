"""SimulatedItemProcessor is pure business logic with no external
dependencies, so it's tested directly with no fixtures beyond itself.
"""

import pytest

from app.services.item_processor import ItemProcessingError, SimulatedItemProcessor


@pytest.fixture()
def processor() -> SimulatedItemProcessor:
    return SimulatedItemProcessor()


def test_process_echoes_payload_and_uppercases_string_value(processor):
    result = processor.process({"value": "hello"})

    assert result == {"echo": {"value": "hello"}, "processed_value": "HELLO"}


def test_process_handles_payload_without_a_value_field(processor):
    result = processor.process({"other": 1})

    assert result == {"echo": {"other": 1}}


def test_process_raises_on_simulate_failure_flag(processor):
    # This is the mechanism every other test uses to deterministically
    # exercise the failure path end to end.
    with pytest.raises(ItemProcessingError, match="boom"):
        processor.process({"simulate_failure": True, "failure_reason": "boom"})


def test_process_raises_with_default_message_when_reason_omitted(processor):
    with pytest.raises(ItemProcessingError, match="simulated processing failure"):
        processor.process({"simulate_failure": True})

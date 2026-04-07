"""Tests for worker adapter interface and mock implementation."""

from backend.adapters.worker.base import WorkerResult, WorkerTask
from backend.adapters.worker.mock_worker import MockWorkerAdapter


def test_worker_task_defaults():
    """WorkerTask should have sensible defaults."""
    task = WorkerTask()
    assert task.task_type == ""
    assert task.timeout_sec == 120
    assert task.mode == "replay"
    assert task.determinism_hint == "best_effort"
    assert task.task_id is not None


def test_worker_result_defaults():
    """WorkerResult should have sensible defaults."""
    result = WorkerResult()
    assert result.schema_valid is False
    assert result.parse_errors == []
    assert result.task_id is not None


async def test_mock_worker_health():
    """Mock worker should always be healthy."""
    worker = MockWorkerAdapter()
    assert await worker.health() is True


def test_mock_worker_adapter_code():
    """Mock worker should have correct adapter code."""
    worker = MockWorkerAdapter()
    assert worker.adapter_code == "mock_deterministic_v1"


def test_mock_worker_supported_task_types():
    """Mock worker should support forecast task types."""
    worker = MockWorkerAdapter()
    assert "event_forecast" in worker.supported_task_types


async def test_mock_worker_execute_returns_valid_result():
    """Mock worker should return a valid WorkerResult."""
    worker = MockWorkerAdapter()
    task = WorkerTask(
        task_type="event_forecast",
        input_payload={"event_type": "earnings_beat", "symbol": "AAPL"},
    )
    result = await worker.execute(task)

    assert isinstance(result, WorkerResult)
    assert result.schema_valid is True
    assert result.task_id == task.task_id
    assert "hypotheses" in result.parsed_json
    assert "selected_hypothesis" in result.parsed_json
    assert result.model_name == "mock_deterministic"


async def test_mock_worker_deterministic():
    """Same input should produce same output."""
    worker = MockWorkerAdapter()
    payload = {"event_type": "earnings_beat", "symbol": "AAPL"}

    task1 = WorkerTask(task_type="event_forecast", input_payload=payload)
    task2 = WorkerTask(task_type="event_forecast", input_payload=payload)

    r1 = await worker.execute(task1)
    r2 = await worker.execute(task2)

    assert r1.output_hash == r2.output_hash
    assert r1.parsed_json["confidence_after"] == r2.parsed_json["confidence_after"]


async def test_mock_worker_different_input_different_output():
    """Different input should produce different output."""
    worker = MockWorkerAdapter()

    r1 = await worker.execute(
        WorkerTask(task_type="event_forecast", input_payload={"symbol": "AAPL"})
    )
    r2 = await worker.execute(
        WorkerTask(task_type="event_forecast", input_payload={"symbol": "MSFT"})
    )

    assert r1.output_hash != r2.output_hash


async def test_mock_worker_produces_horizons():
    """Mock worker should produce horizon data."""
    worker = MockWorkerAdapter()
    task = WorkerTask(
        task_type="event_forecast",
        input_payload={"event_type": "earnings_beat"},
    )
    result = await worker.execute(task)

    horizons = result.parsed_json.get("horizons", {})
    assert "1d" in horizons
    assert "5d" in horizons
    assert "p_outperform" in horizons["1d"]
    assert "ret_q50" in horizons["1d"]

"""Worker adapter base interface.

Per ADR-004, all worker types (API, CLI, manual bridge, heuristic)
share the same WorkerTask/WorkerResult contract.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class WorkerTask:
    """Unified task contract sent to any worker adapter."""
    task_id: UUID = field(default_factory=uuid4)
    task_type: str = ""
    schema_name: str = ""
    schema_version: str = "1.0.0"
    prompt_template_id: str = ""
    prompt_version: str = ""
    input_payload: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    timeout_sec: int = 120
    mode: str = "replay"
    determinism_hint: str = "best_effort"


@dataclass
class WorkerResult:
    """Unified result contract returned by any worker adapter."""
    task_id: UUID = field(default_factory=uuid4)
    raw_text: str = ""
    parsed_json: dict[str, Any] = field(default_factory=dict)
    schema_valid: bool = False
    parse_errors: list[str] = field(default_factory=list)
    reasoning_trace_summary: dict[str, Any] = field(default_factory=dict)
    output_hash: str = ""
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    model_name: str = ""
    model_version: str = ""


class WorkerAdapter(ABC):
    """Abstract interface for worker adapters."""

    @abstractmethod
    async def health(self) -> bool:
        """Check if the worker is healthy and available."""
        ...

    @abstractmethod
    async def execute(self, task: WorkerTask) -> WorkerResult:
        """Execute a task and return the result."""
        ...

    @property
    @abstractmethod
    def adapter_code(self) -> str:
        """Unique identifier for this adapter."""
        ...

    @property
    @abstractmethod
    def supported_task_types(self) -> list[str]:
        """List of task types this adapter can handle."""
        ...

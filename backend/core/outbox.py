"""Transactional outbox for event publishing.

Every critical state transition writes an outbox row in the
same DB transaction. A separate poller publishes them later.
"""

from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.trace import get_trace
from backend.models.ops import OutboxEvent


async def emit_event(
    db: AsyncSession,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    payload: dict[str, Any],
    schema_version: str = "1.0.0",
    partition_key: str | None = None,
) -> OutboxEvent:
    """Write an event to the transactional outbox.

    MUST be called within the same transaction as the
    ledger write it corresponds to.
    """
    trace = get_trace()

    outbox = OutboxEvent(
        topic=f"{aggregate_type}.{event_type}",
        partition_key=partition_key or aggregate_id,
        event_name=event_type,
        event_version=schema_version,
        schema_name=aggregate_type,
        schema_version=schema_version,
        payload_json=payload,
        trace_id=trace.trace_id,
        idempotency_key=f"{aggregate_type}:{aggregate_id}:{event_type}:{uuid4().hex[:8]}",
        status="pending",
    )
    db.add(outbox)
    # Do NOT commit - caller controls the transaction
    return outbox

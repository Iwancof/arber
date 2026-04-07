"""Document ingestion service.

Handles raw document intake, deduplication, and event extraction pipeline entry.
"""

import hashlib
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.kill_switch import check_source_ingest_allowed
from backend.core.outbox import emit_event
from backend.models.content import DedupCluster, RawDocument


async def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of document content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def ingest_document(
    db: AsyncSession,
    *,
    source_id: UUID,
    headline: str | None,
    url: str | None,
    raw_text: str | None,
    raw_payload_json: dict[str, Any],
    published_at: datetime,
    language_code: str | None = None,
    source_tier: str = "medium_vendor",
    native_doc_id: str | None = None,
    market_profile_hint_id: UUID | None = None,
    visibility_scope: str = "internal",
    metadata_json: dict[str, Any] | None = None,
) -> RawDocument:
    """Ingest a raw document with deduplication.

    Returns the RawDocument (existing if duplicate, new otherwise).
    Raises RuntimeError if source ingest is paused by kill switch.
    """
    # Kill switch: check source-level ingest pause
    ingest_ok = await check_source_ingest_allowed(
        db, source_id=str(source_id)
    )
    if not ingest_ok:
        raise RuntimeError(
            f"Source ingest paused for source_id={source_id}. "
            f"Kill switch SOURCE_INGEST_PAUSE or FULL_FREEZE is active."
        )

    content_for_hash = raw_text or str(raw_payload_json)
    content_hash = await compute_content_hash(content_for_hash)

    # Check for duplicate by source + content_hash
    existing = await db.execute(
        select(RawDocument).where(
            RawDocument.source_id == source_id,
            RawDocument.content_hash == content_hash,
        )
    )
    if existing_doc := existing.scalar_one_or_none():
        return existing_doc

    # Check for duplicate by source + native_doc_id
    if native_doc_id:
        existing_native = await db.execute(
            select(RawDocument).where(
                RawDocument.source_id == source_id,
                RawDocument.native_doc_id == native_doc_id,
            )
        )
        if existing_doc := existing_native.scalar_one_or_none():
            return existing_doc

    # Create dedup cluster
    dedup_key = f"{source_id}:{content_hash}"
    dedup_result = await db.execute(
        select(DedupCluster).where(DedupCluster.dedup_key == dedup_key)
    )
    cluster = dedup_result.scalar_one_or_none()
    if cluster is None:
        cluster = DedupCluster(dedup_key=dedup_key, cluster_size=1)
        db.add(cluster)
        await db.flush()
    else:
        cluster.cluster_size += 1

    doc = RawDocument(
        source_id=source_id,
        dedup_cluster_id=cluster.dedup_cluster_id,
        native_doc_id=native_doc_id,
        headline=headline,
        url=url,
        language_code=language_code,
        source_tier=source_tier,
        published_at=published_at,
        content_hash=content_hash,
        raw_text=raw_text,
        raw_payload_json=raw_payload_json or {},
        visibility_scope=visibility_scope,
        market_profile_hint_id=market_profile_hint_id,
        metadata_json=metadata_json or {},
    )
    db.add(doc)
    await db.flush()

    # Update cluster representative
    if cluster.representative_doc_id is None:
        cluster.representative_doc_id = doc.raw_document_id

    # Emit outbox event within the same transaction
    await emit_event(
        db,
        event_type="created",
        aggregate_type="raw_document",
        aggregate_id=str(doc.raw_document_id),
        payload={
            "source_id": str(source_id),
            "headline": headline,
            "content_hash": content_hash,
            "published_at": published_at.isoformat(),
        },
    )

    await db.commit()
    await db.refresh(doc)
    return doc

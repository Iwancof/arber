"""Research Scout service layer.

Manages research cases, jobs, symbol dossiers,
candidate symbols, and analog searches.

State machines
--------------
Case:
  new -> monitoring -> enriching ->
  awaiting_human -> promotion_pending ->
  resolved | retired

Job:
  queued -> running -> completed | failed |
  canceled | stale

Candidate:
  new -> monitoring -> needs_more_evidence ->
  promotion_pending -> promoted | rejected |
  expired
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.outbox import emit_event
from backend.models.research import (
    CandidateSymbol,
    ResearchCase,
    ResearchEvidence,
    ResearchJob,
    ResearchQueryPlan,
    ResearchScope,
    SymbolDossierSnapshot,
)

logger = logging.getLogger("eos.research")


# -----------------------------------------------------------
# Case
# -----------------------------------------------------------
async def create_research_case(
    db: AsyncSession,
    *,
    case_type: str,
    market_code: str,
    title: str,
    primary_symbol: str | None = None,
    benchmark_symbol: str | None = None,
    trigger_reason: str | None = None,
    scopes: list[dict[str, Any]] | None = None,
) -> ResearchCase:
    """Create a new research case with scopes."""
    case = ResearchCase(
        case_type=case_type,
        market_code=market_code,
        title=title,
        primary_symbol=primary_symbol,
        benchmark_symbol=benchmark_symbol,
        trigger_reason=trigger_reason,
        status="new",
    )
    db.add(case)
    await db.flush()

    for s in scopes or []:
        scope = ResearchScope(
            case_id=case.case_id,
            scope_type=s["scope_type"],
            scope_key=s["scope_key"],
            scope_role=s["scope_role"],
            metadata_json=s.get(
                "metadata_json", {}
            ),
        )
        db.add(scope)

    await db.flush()
    await emit_event(
        db,
        event_type="created",
        aggregate_type="research_case",
        aggregate_id=str(case.case_id),
        payload={
            "case_type": case_type,
            "market_code": market_code,
            "title": title,
        },
    )
    await db.commit()
    await db.refresh(case)
    return case


async def get_research_case(
    db: AsyncSession,
    case_id: UUID,
) -> ResearchCase | None:
    """Get a single research case by ID."""
    result = await db.execute(
        select(ResearchCase).where(
            ResearchCase.case_id == case_id,
        )
    )
    return result.scalar_one_or_none()


async def list_research_cases(
    db: AsyncSession,
    *,
    market_code: str | None = None,
    status: str | None = None,
    primary_symbol: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ResearchCase], int]:
    """List cases with optional filters.

    Returns (items, total_count).
    """
    stmt = select(ResearchCase)
    if market_code:
        stmt = stmt.where(
            ResearchCase.market_code
            == market_code,
        )
    if status:
        stmt = stmt.where(
            ResearchCase.status == status,
        )
    if primary_symbol:
        stmt = stmt.where(
            ResearchCase.primary_symbol
            == primary_symbol,
        )

    # count
    from sqlalchemy import func
    cnt_stmt = select(
        func.count()
    ).select_from(ResearchCase)
    if market_code:
        cnt_stmt = cnt_stmt.where(
            ResearchCase.market_code
            == market_code,
        )
    if status:
        cnt_stmt = cnt_stmt.where(
            ResearchCase.status == status,
        )
    if primary_symbol:
        cnt_stmt = cnt_stmt.where(
            ResearchCase.primary_symbol
            == primary_symbol,
        )
    total = (
        await db.execute(cnt_stmt)
    ).scalar_one()

    result = await db.execute(
        stmt.order_by(
            ResearchCase.priority.desc(),
            ResearchCase.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


# -----------------------------------------------------------
# Job
# -----------------------------------------------------------
async def create_research_job(
    db: AsyncSession,
    *,
    case_id: UUID | None = None,
    job_type: str,
    trigger_type: str,
    budget_class: str,
    worker_adapter: str | None = None,
    prompt_version: str | None = None,
    query_plans: (
        list[dict[str, Any]] | None
    ) = None,
) -> ResearchJob:
    """Create a research job with query plans."""
    job = ResearchJob(
        case_id=case_id,
        job_type=job_type,
        trigger_type=trigger_type,
        budget_class=budget_class,
        status="queued",
        worker_adapter=worker_adapter,
        prompt_version=prompt_version,
    )
    db.add(job)
    await db.flush()

    for qp in query_plans or []:
        plan = ResearchQueryPlan(
            job_id=job.job_id,
            query_kind=qp["query_kind"],
            query_text=qp["query_text"],
            max_docs=qp.get("max_docs", 20),
            source_filter_json=qp.get(
                "source_filter_json", {}
            ),
            status="planned",
        )
        db.add(plan)

    await db.flush()
    await emit_event(
        db,
        event_type="created",
        aggregate_type="research_job",
        aggregate_id=str(job.job_id),
        payload={
            "job_type": job_type,
            "trigger_type": trigger_type,
            "case_id": (
                str(case_id) if case_id else None
            ),
        },
    )
    await db.commit()
    await db.refresh(job)
    return job


async def list_research_jobs(
    db: AsyncSession,
    *,
    status: str | None = None,
    case_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ResearchJob], int]:
    """List jobs with optional filters."""
    stmt = select(ResearchJob)
    if status:
        stmt = stmt.where(
            ResearchJob.status == status,
        )
    if case_id:
        stmt = stmt.where(
            ResearchJob.case_id == case_id,
        )

    from sqlalchemy import func
    cnt_stmt = select(
        func.count()
    ).select_from(ResearchJob)
    if status:
        cnt_stmt = cnt_stmt.where(
            ResearchJob.status == status,
        )
    if case_id:
        cnt_stmt = cnt_stmt.where(
            ResearchJob.case_id == case_id,
        )
    total = (
        await db.execute(cnt_stmt)
    ).scalar_one()

    result = await db.execute(
        stmt.order_by(
            ResearchJob.created_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


# -----------------------------------------------------------
# Symbol Dossier
# -----------------------------------------------------------
async def get_symbol_dossier(
    db: AsyncSession,
    symbol: str,
    market_code: str | None = None,
) -> SymbolDossierSnapshot | None:
    """Get latest dossier snapshot for a symbol."""
    stmt = (
        select(SymbolDossierSnapshot)
        .where(
            SymbolDossierSnapshot.symbol
            == symbol,
        )
        .order_by(
            SymbolDossierSnapshot.asof.desc(),
        )
        .limit(1)
    )
    if market_code:
        stmt = stmt.where(
            SymbolDossierSnapshot.market_code
            == market_code,
        )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# -----------------------------------------------------------
# Candidates
# -----------------------------------------------------------
async def list_candidates(
    db: AsyncSession,
    market_code: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CandidateSymbol], int]:
    """List candidate symbols with filters."""
    stmt = select(CandidateSymbol)
    if market_code:
        stmt = stmt.where(
            CandidateSymbol.market_code
            == market_code,
        )
    if status:
        stmt = stmt.where(
            CandidateSymbol.status == status,
        )

    from sqlalchemy import func
    cnt_stmt = select(
        func.count()
    ).select_from(CandidateSymbol)
    if market_code:
        cnt_stmt = cnt_stmt.where(
            CandidateSymbol.market_code
            == market_code,
        )
    if status:
        cnt_stmt = cnt_stmt.where(
            CandidateSymbol.status == status,
        )
    total = (
        await db.execute(cnt_stmt)
    ).scalar_one()

    result = await db.execute(
        stmt.order_by(
            CandidateSymbol.discovery_score.desc(),
            CandidateSymbol.last_seen_at.desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total


async def promote_candidate(
    db: AsyncSession,
    candidate_id: UUID,
    promotion_level: str,
    note: str | None = None,
) -> CandidateSymbol:
    """Promote a candidate symbol."""
    result = await db.execute(
        select(CandidateSymbol).where(
            CandidateSymbol.candidate_id
            == candidate_id,
        )
    )
    candidate = result.scalar_one()
    now = datetime.now(tz=UTC)

    candidate.status = "promoted"
    candidate.promoted_at = now
    candidate.decision_note = note
    candidate.promotion_score = (
        candidate.discovery_score
    )

    await db.flush()
    await emit_event(
        db,
        event_type="promoted",
        aggregate_type="candidate_symbol",
        aggregate_id=str(candidate_id),
        payload={
            "symbol": candidate.symbol,
            "market_code": candidate.market_code,
            "promotion_level": promotion_level,
        },
    )
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def reject_candidate(
    db: AsyncSession,
    candidate_id: UUID,
    reason: str | None = None,
) -> CandidateSymbol:
    """Reject a candidate symbol."""
    result = await db.execute(
        select(CandidateSymbol).where(
            CandidateSymbol.candidate_id
            == candidate_id,
        )
    )
    candidate = result.scalar_one()
    now = datetime.now(tz=UTC)

    candidate.status = "rejected"
    candidate.rejected_at = now
    candidate.decision_note = reason

    await db.flush()
    await emit_event(
        db,
        event_type="rejected",
        aggregate_type="candidate_symbol",
        aggregate_id=str(candidate_id),
        payload={
            "symbol": candidate.symbol,
            "market_code": candidate.market_code,
            "reason": reason or "",
        },
    )
    await db.commit()
    await db.refresh(candidate)
    return candidate


async def snooze_candidate(
    db: AsyncSession,
    candidate_id: UUID,
    until: datetime | None = None,
) -> CandidateSymbol:
    """Snooze a candidate symbol review.

    Keeps candidate in current status but marks
    last_seen_at to delay re-surfacing.
    """
    result = await db.execute(
        select(CandidateSymbol).where(
            CandidateSymbol.candidate_id
            == candidate_id,
        )
    )
    candidate = result.scalar_one()

    if until:
        candidate.last_seen_at = until
    else:
        candidate.last_seen_at = datetime.now(
            tz=UTC,
        )

    await db.commit()
    await db.refresh(candidate)
    return candidate


# -----------------------------------------------------------
# Refresh (creates a deepening job for case)
# -----------------------------------------------------------
async def refresh_case(
    db: AsyncSession,
    case_id: UUID,
) -> ResearchJob:
    """Enqueue a refresh/deepening job for case.

    Updates the case status to 'enriching' and
    creates a brief_refresh job.
    """
    case_result = await db.execute(
        select(ResearchCase).where(
            ResearchCase.case_id == case_id,
        )
    )
    case = case_result.scalar_one()
    case.status = "enriching"
    case.updated_at = datetime.now(tz=UTC)

    job = ResearchJob(
        case_id=case_id,
        job_type="brief_refresh",
        trigger_type="operator",
        budget_class="medium",
        status="queued",
    )
    db.add(job)
    await db.flush()

    await emit_event(
        db,
        event_type="updated",
        aggregate_type="research_case",
        aggregate_id=str(case_id),
        payload={
            "status": "enriching",
            "refresh_job_id": str(job.job_id),
        },
    )
    await db.commit()
    await db.refresh(job)
    return job


# -----------------------------------------------------------
# Analogs (historical evidence search)
# -----------------------------------------------------------
async def search_analogs(
    db: AsyncSession,
    *,
    symbol: str | None = None,
    event_type: str | None = None,
    verdict: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ResearchEvidence], int]:
    """Search historical analog evidence.

    Filters evidence records that serve as
    historical context (evidence_role=historical).
    """
    stmt = select(ResearchEvidence).where(
        ResearchEvidence.evidence_role
        == "historical",
    )
    if symbol:
        stmt = stmt.where(
            ResearchEvidence.symbol == symbol,
        )
    if event_type:
        stmt = stmt.where(
            ResearchEvidence.event_type
            == event_type,
        )
    if verdict:
        stmt = stmt.where(
            ResearchEvidence.metadata_json[
                "verdict"
            ].astext
            == verdict,
        )

    from sqlalchemy import func
    cnt_stmt = select(
        func.count()
    ).select_from(ResearchEvidence).where(
        ResearchEvidence.evidence_role
        == "historical",
    )
    if symbol:
        cnt_stmt = cnt_stmt.where(
            ResearchEvidence.symbol == symbol,
        )
    if event_type:
        cnt_stmt = cnt_stmt.where(
            ResearchEvidence.event_type
            == event_type,
        )
    if verdict:
        cnt_stmt = cnt_stmt.where(
            ResearchEvidence.metadata_json[
                "verdict"
            ].astext
            == verdict,
        )
    total = (
        await db.execute(cnt_stmt)
    ).scalar_one()

    result = await db.execute(
        stmt.order_by(
            ResearchEvidence.relevance_score.desc()
            .nulls_last(),
            ResearchEvidence.published_at.desc()
            .nulls_last(),
        )
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all(), total

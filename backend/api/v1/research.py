"""Research Scout API endpoints.

13 endpoints for research cases, jobs, symbol
dossiers, candidate symbols, and analog search.
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.research import (
    CandidateSymbolList,
    CandidateSymbolRead,
    PromoteCandidateRequest,
    RejectCandidateRequest,
    ResearchAnalogRead,
    ResearchCaseCreate,
    ResearchCaseList,
    ResearchCaseRead,
    ResearchJobCreate,
    ResearchJobList,
    ResearchJobRead,
    ResearchQueryPlanRead,
    ResearchScopeRead,
    SnoozeCandidateRequest,
    SymbolDossierRead,
)
from backend.services.research import (
    create_research_case,
    create_research_job,
    get_research_case,
    get_symbol_dossier,
    list_candidates,
    list_research_cases,
    list_research_jobs,
    promote_candidate,
    refresh_case,
    reject_candidate,
    search_analogs,
    snooze_candidate,
)

router = APIRouter(
    prefix="/research",
    tags=["research"],
)


# -----------------------------------------------------------
# Helpers
# -----------------------------------------------------------

def _case_to_read(c) -> ResearchCaseRead:
    """Convert ORM case to read schema."""
    scopes = []
    if hasattr(c, "scopes") and c.scopes:
        scopes = [
            ResearchScopeRead(
                scope_id=s.scope_id,
                case_id=s.case_id,
                scope_type=s.scope_type,
                scope_key=s.scope_key,
                scope_role=s.scope_role,
                metadata_json=s.metadata_json,
                created_at=s.created_at,
            )
            for s in c.scopes
        ]
    return ResearchCaseRead(
        case_id=c.case_id,
        case_type=c.case_type,
        market_code=c.market_code,
        primary_symbol=c.primary_symbol,
        benchmark_symbol=c.benchmark_symbol,
        title=c.title,
        status=c.status,
        priority=c.priority,
        trigger_reason=c.trigger_reason,
        current_hypothesis_summary=(
            c.current_hypothesis_summary
        ),
        current_question_summary=(
            c.current_question_summary
        ),
        trace_id=c.trace_id,
        correlation_id=c.correlation_id,
        created_at=c.created_at,
        updated_at=c.updated_at,
        first_seen_at=c.first_seen_at,
        last_updated_at=c.last_updated_at,
        scopes=scopes,
    )


def _job_to_read(j) -> ResearchJobRead:
    """Convert ORM job to read schema."""
    plans = []
    if hasattr(j, "query_plans") and j.query_plans:
        plans = [
            ResearchQueryPlanRead(
                plan_id=p.plan_id,
                job_id=p.job_id,
                query_kind=p.query_kind,
                source_filter_json=(
                    p.source_filter_json
                ),
                query_text=p.query_text,
                time_window_start=(
                    p.time_window_start
                ),
                time_window_end=(
                    p.time_window_end
                ),
                max_docs=p.max_docs,
                status=p.status,
                created_at=p.created_at,
            )
            for p in j.query_plans
        ]
    return ResearchJobRead(
        job_id=j.job_id,
        case_id=j.case_id,
        job_type=j.job_type,
        trigger_type=j.trigger_type,
        budget_class=j.budget_class,
        status=j.status,
        worker_adapter=j.worker_adapter,
        prompt_version=j.prompt_version,
        input_hash=j.input_hash,
        result_summary=j.result_summary,
        trace_id=j.trace_id,
        correlation_id=j.correlation_id,
        scheduled_at=j.scheduled_at,
        started_at=j.started_at,
        finished_at=j.finished_at,
        next_run_at=j.next_run_at,
        created_at=j.created_at,
        query_plans=plans,
    )


def _candidate_to_read(
    c,
) -> CandidateSymbolRead:
    """Convert ORM candidate to read schema."""
    return CandidateSymbolRead(
        candidate_id=c.candidate_id,
        market_code=c.market_code,
        symbol=c.symbol,
        discovered_from_case_id=(
            c.discovered_from_case_id
        ),
        discovered_from_event_ref=(
            c.discovered_from_event_ref
        ),
        relation_to_watchlist=(
            c.relation_to_watchlist
        ),
        candidate_reason_codes=(
            c.candidate_reason_codes
        ),
        discovery_score=c.discovery_score,
        promotion_score=c.promotion_score,
        status=c.status,
        first_seen_at=c.first_seen_at,
        last_seen_at=c.last_seen_at,
        promoted_at=c.promoted_at,
        rejected_at=c.rejected_at,
        decision_note=c.decision_note,
        trace_id=c.trace_id,
        correlation_id=c.correlation_id,
        created_at=c.created_at,
    )


# -----------------------------------------------------------
# Cases
# -----------------------------------------------------------

@router.get(
    "/cases",
    response_model=ResearchCaseList,
    summary="List research cases",
)
async def list_cases_endpoint(
    market_code: str | None = Query(
        default=None,
    ),
    status: str | None = Query(default=None),
    primary_symbol: str | None = Query(
        default=None,
    ),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ResearchCaseList:
    """List research cases with filters."""
    items, total = await list_research_cases(
        db,
        market_code=market_code,
        status=status,
        primary_symbol=primary_symbol,
        limit=limit,
        offset=offset,
    )
    return ResearchCaseList(
        items=[_case_to_read(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/cases",
    response_model=ResearchCaseRead,
    status_code=201,
    summary="Create a research case",
)
async def create_case_endpoint(
    body: ResearchCaseCreate,
    db: AsyncSession = Depends(get_db),
) -> ResearchCaseRead:
    """Create a new research case."""
    scopes = [
        s.model_dump() for s in body.scopes
    ]
    case = await create_research_case(
        db,
        case_type=body.case_type,
        market_code=body.market_code,
        title=body.title,
        primary_symbol=body.primary_symbol,
        benchmark_symbol=body.benchmark_symbol,
        trigger_reason=body.trigger_reason,
        scopes=scopes,
    )
    return _case_to_read(case)


@router.get(
    "/cases/{case_id}",
    response_model=ResearchCaseRead,
    summary="Get research case detail",
)
async def get_case_endpoint(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResearchCaseRead:
    """Get a single research case by ID."""
    case = await get_research_case(db, case_id)
    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Research case not found",
        )
    return _case_to_read(case)


@router.post(
    "/cases/{case_id}/refresh",
    response_model=ResearchJobRead,
    status_code=202,
    summary="Enqueue refresh job for case",
)
async def refresh_case_endpoint(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResearchJobRead:
    """Enqueue a refresh/deepening job."""
    case = await get_research_case(db, case_id)
    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Research case not found",
        )
    job = await refresh_case(db, case_id)
    return _job_to_read(job)


# -----------------------------------------------------------
# Jobs
# -----------------------------------------------------------

@router.get(
    "/jobs",
    response_model=ResearchJobList,
    summary="List research jobs",
)
async def list_jobs_endpoint(
    status: str | None = Query(default=None),
    case_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ResearchJobList:
    """List research jobs with filters."""
    items, total = await list_research_jobs(
        db,
        status=status,
        case_id=case_id,
        limit=limit,
        offset=offset,
    )
    return ResearchJobList(
        items=[_job_to_read(j) for j in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/jobs",
    response_model=ResearchJobRead,
    status_code=202,
    summary="Create a research job",
)
async def create_job_endpoint(
    body: ResearchJobCreate,
    db: AsyncSession = Depends(get_db),
) -> ResearchJobRead:
    """Create a new research job."""
    plans = [
        qp.model_dump()
        for qp in body.query_plans
    ]
    job = await create_research_job(
        db,
        case_id=body.case_id,
        job_type=body.job_type,
        trigger_type=body.trigger_type,
        budget_class=body.budget_class,
        worker_adapter=body.worker_adapter,
        prompt_version=body.prompt_version,
        query_plans=plans,
    )
    return _job_to_read(job)


# -----------------------------------------------------------
# Symbol Dossier
# -----------------------------------------------------------

@router.get(
    "/symbols/{symbol}/dossier",
    response_model=SymbolDossierRead | None,
    summary="Get latest symbol dossier",
)
async def get_dossier_endpoint(
    symbol: str,
    market_code: str | None = Query(
        default=None,
    ),
    db: AsyncSession = Depends(get_db),
) -> SymbolDossierRead | None:
    """Get latest dossier snapshot for symbol."""
    snap = await get_symbol_dossier(
        db, symbol, market_code,
    )
    if snap is None:
        return None
    return SymbolDossierRead(
        snapshot_id=snap.snapshot_id,
        market_code=snap.market_code,
        symbol=snap.symbol,
        asof=snap.asof,
        watch_status=snap.watch_status,
        benchmark_symbol=snap.benchmark_symbol,
        current_thesis=snap.current_thesis,
        payload_json=snap.payload_json,
        quality_score=snap.quality_score,
        coverage_score=snap.coverage_score,
        research_depth_score=(
            snap.research_depth_score
        ),
        freshness_class=snap.freshness_class,
        source_case_id=snap.source_case_id,
        created_at=snap.created_at,
    )


# -----------------------------------------------------------
# Candidates
# -----------------------------------------------------------

@router.get(
    "/candidates",
    response_model=CandidateSymbolList,
    summary="List candidate symbols",
)
async def list_candidates_endpoint(
    market_code: str | None = Query(
        default=None,
    ),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> CandidateSymbolList:
    """List candidate symbols with filters."""
    items, total = await list_candidates(
        db,
        market_code=market_code,
        status=status,
        limit=limit,
        offset=offset,
    )
    return CandidateSymbolList(
        items=[
            _candidate_to_read(c)
            for c in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/candidates/{candidate_id}/promote",
    response_model=CandidateSymbolRead,
    summary="Promote candidate symbol",
)
async def promote_candidate_endpoint(
    candidate_id: UUID,
    body: PromoteCandidateRequest,
    db: AsyncSession = Depends(get_db),
) -> CandidateSymbolRead:
    """Promote a candidate symbol."""
    try:
        c = await promote_candidate(
            db,
            candidate_id,
            promotion_level=body.promotion_level,
            note=body.note,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e
    return _candidate_to_read(c)


@router.post(
    "/candidates/{candidate_id}/reject",
    response_model=CandidateSymbolRead,
    summary="Reject candidate symbol",
)
async def reject_candidate_endpoint(
    candidate_id: UUID,
    body: RejectCandidateRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> CandidateSymbolRead:
    """Reject a candidate symbol."""
    reason = body.reason if body else None
    try:
        c = await reject_candidate(
            db, candidate_id, reason=reason,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e
    return _candidate_to_read(c)


@router.post(
    "/candidates/{candidate_id}/snooze",
    response_model=CandidateSymbolRead,
    summary="Snooze candidate symbol review",
)
async def snooze_candidate_endpoint(
    candidate_id: UUID,
    body: SnoozeCandidateRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> CandidateSymbolRead:
    """Snooze a candidate symbol review."""
    until = body.until if body else None
    try:
        c = await snooze_candidate(
            db, candidate_id, until=until,
        )
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        ) from e
    return _candidate_to_read(c)


# -----------------------------------------------------------
# Analogs
# -----------------------------------------------------------

@router.get(
    "/analogs",
    response_model=list[ResearchAnalogRead],
    summary="Search historical analogs",
)
async def list_analogs_endpoint(
    symbol: str | None = Query(default=None),
    event_type: str | None = Query(
        default=None,
    ),
    verdict: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ResearchAnalogRead]:
    """Search historical analog evidence."""
    items, _ = await search_analogs(
        db,
        symbol=symbol,
        event_type=event_type,
        verdict=verdict,
        limit=limit,
        offset=offset,
    )
    return [
        ResearchAnalogRead(
            evidence_id=e.evidence_id,
            case_id=e.case_id,
            source_type=e.source_type,
            evidence_role=e.evidence_role,
            symbol=e.symbol,
            event_type=e.event_type,
            published_at=e.published_at,
            relevance_score=e.relevance_score,
            novelty_score=e.novelty_score,
            summary=e.summary,
            metadata_json=e.metadata_json,
            created_at=e.created_at,
        )
        for e in items
    ]

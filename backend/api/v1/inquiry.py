"""Human Inquiry Orchestration API endpoints.

14+ endpoints covering the full inquiry lifecycle:
tray, cases, tasks, responses, resolutions,
presence, and metrics.

Auth levels per spec section 18.17:
  viewer   - read-only
  operator - claim, snooze, submit, reformat
  trader   - accept, reject
  admin    - supersede, expire
"""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.inquiry import (
    InquiryCase,
    InquiryTask,
)
from backend.schemas.inquiry import (
    InquiryAcceptRequest,
    InquiryCaseCreate,
    InquiryCaseList,
    InquiryCaseRead,
    InquiryMetricsRead,
    InquiryPresenceUpdate,
    InquiryRejectRequest,
    InquiryResolutionRead,
    InquiryResponseCreate,
    InquiryResponseRead,
    InquirySnoozeRequest,
    InquirySpawnTaskRequest,
    InquiryTaskList,
    InquiryTaskRead,
    InquiryTrayItem,
)
from backend.services.inquiry import (
    accept_inquiry_response,
    claim_task,
    expire_task,
    get_metrics,
    get_tray,
    reject_inquiry_response,
    snooze_task,
    spawn_inquiry_task,
    submit_inquiry_response,
    supersede_task,
    update_presence,
)

router = APIRouter(
    prefix="/inquiry",
    tags=["inquiry"],
)

# A placeholder user_id for operations that
# need one.  In production this comes from
# the auth middleware.
_PLACEHOLDER_USER = UUID(
    "00000000-0000-0000-0000-000000000001"
)


# ---------------------------------------------------------------
# Read APIs
# ---------------------------------------------------------------

@router.get(
    "/tray",
    response_model=list[InquiryTrayItem],
    summary="Get current inquiry tray",
)
async def inquiry_tray(
    db: AsyncSession = Depends(get_db),
) -> list[InquiryTrayItem]:
    """Return tray items sorted by priority."""
    raw = await get_tray(db)
    return [
        InquiryTrayItem(
            task_id=r["task_id"],
            case_id=r["case_id"],
            inquiry_kind=r["inquiry_kind"],
            market_profile_code=(
                r["market_profile_code"]
            ),
            primary_symbol=r["primary_symbol"],
            task_status=r["task_status"],
            priority_score=r["priority_score"],
            sla_class=r["sla_class"],
            deadline_at=r["deadline_at"],
            question_title=r["question_title"],
            time_bucket=r["time_bucket"],
        )
        for r in raw
    ]


@router.get(
    "/cases",
    response_model=InquiryCaseList,
    summary="List inquiry cases",
)
async def list_cases(
    case_status: str | None = Query(
        default=None,
    ),
    inquiry_kind: str | None = Query(
        default=None,
    ),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InquiryCaseList:
    """List inquiry cases with filters."""
    stmt = select(InquiryCase)
    cnt = select(func.count()).select_from(
        InquiryCase,
    )

    if case_status:
        stmt = stmt.where(
            InquiryCase.case_status == case_status,
        )
        cnt = cnt.where(
            InquiryCase.case_status == case_status,
        )
    if inquiry_kind:
        stmt = stmt.where(
            InquiryCase.inquiry_kind == inquiry_kind,
        )
        cnt = cnt.where(
            InquiryCase.inquiry_kind == inquiry_kind,
        )

    total = (await db.execute(cnt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(
            InquiryCase.priority_score.desc(),
            InquiryCase.opened_at.desc(),
        )
    )
    items = [
        InquiryCaseRead(
            inquiry_case_id=c.inquiry_case_id,
            market_profile_code=(
                c.market_profile_code
            ),
            linked_entity_type=(
                c.linked_entity_type
            ),
            linked_entity_id=c.linked_entity_id,
            inquiry_kind=c.inquiry_kind,
            dedupe_key=c.dedupe_key,
            title=c.title,
            benchmark_symbol=c.benchmark_symbol,
            primary_symbol=c.primary_symbol,
            horizon_code=c.horizon_code,
            priority_score=c.priority_score,
            urgency_class=c.urgency_class,
            case_status=c.case_status,
            opened_at=c.opened_at,
            updated_at=c.updated_at,
            metadata_json=c.metadata_json,
        )
        for c in result.scalars().all()
    ]
    return InquiryCaseList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/cases",
    response_model=InquiryCaseRead,
    status_code=201,
    summary="Create inquiry case",
)
async def create_case(
    body: InquiryCaseCreate,
    db: AsyncSession = Depends(get_db),
) -> InquiryCaseRead:
    """Create a new inquiry case."""
    from backend.services.inquiry import (
        create_inquiry_case,
    )
    case = await create_inquiry_case(
        db, **body.model_dump()
    )
    return InquiryCaseRead(
        inquiry_case_id=case.inquiry_case_id,
        market_profile_code=case.market_profile_code,
        linked_entity_type=case.linked_entity_type,
        linked_entity_id=case.linked_entity_id,
        inquiry_kind=case.inquiry_kind,
        dedupe_key=case.dedupe_key,
        title=case.title,
        benchmark_symbol=case.benchmark_symbol,
        primary_symbol=case.primary_symbol,
        horizon_code=case.horizon_code,
        priority_score=case.priority_score,
        urgency_class=case.urgency_class,
        case_status=case.case_status,
        opened_at=case.opened_at,
        updated_at=case.updated_at,
        metadata_json=case.metadata_json,
    )


@router.get(
    "/cases/{case_id}",
    response_model=InquiryCaseRead,
    summary="Get inquiry case dossier",
)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryCaseRead:
    """Get a single inquiry case by ID."""
    result = await db.execute(
        select(InquiryCase).where(
            InquiryCase.inquiry_case_id == case_id,
        )
    )
    c = result.scalar_one_or_none()
    if c is None:
        raise HTTPException(
            status_code=404,
            detail="Inquiry case not found",
        )
    return InquiryCaseRead(
        inquiry_case_id=c.inquiry_case_id,
        market_profile_code=(
            c.market_profile_code
        ),
        linked_entity_type=c.linked_entity_type,
        linked_entity_id=c.linked_entity_id,
        inquiry_kind=c.inquiry_kind,
        dedupe_key=c.dedupe_key,
        title=c.title,
        benchmark_symbol=c.benchmark_symbol,
        primary_symbol=c.primary_symbol,
        horizon_code=c.horizon_code,
        priority_score=c.priority_score,
        urgency_class=c.urgency_class,
        case_status=c.case_status,
        opened_at=c.opened_at,
        updated_at=c.updated_at,
        metadata_json=c.metadata_json,
    )


@router.get(
    "/tasks",
    response_model=InquiryTaskList,
    summary="List inquiry tasks",
)
async def list_tasks(
    task_status: str | None = Query(
        default=None,
    ),
    sla_class: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskList:
    """List inquiry tasks with filters."""
    stmt = select(InquiryTask)
    cnt = select(func.count()).select_from(
        InquiryTask,
    )

    if task_status:
        stmt = stmt.where(
            InquiryTask.task_status == task_status,
        )
        cnt = cnt.where(
            InquiryTask.task_status == task_status,
        )
    if sla_class:
        stmt = stmt.where(
            InquiryTask.sla_class == sla_class,
        )
        cnt = cnt.where(
            InquiryTask.sla_class == sla_class,
        )

    total = (await db.execute(cnt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset)
        .limit(limit)
        .order_by(
            InquiryTask.priority_score.desc(),
            InquiryTask.deadline_at.asc(),
        )
    )
    items = [
        InquiryTaskRead(
            inquiry_task_id=t.inquiry_task_id,
            inquiry_case_id=t.inquiry_case_id,
            revision_no=t.revision_no,
            prompt_task_id=t.prompt_task_id,
            task_status=t.task_status,
            priority_score=t.priority_score,
            sla_class=t.sla_class,
            deadline_at=t.deadline_at,
            claim_expires_at=t.claim_expires_at,
            prompt_pack_hash=t.prompt_pack_hash,
            evidence_bundle_hash=(
                t.evidence_bundle_hash
            ),
            question_title=t.question_title,
            question_text=t.question_text,
            required_schema_name=(
                t.required_schema_name
            ),
            required_schema_version=(
                t.required_schema_version
            ),
            bounded_evidence_json=(
                t.bounded_evidence_json
            ),
            acceptance_rules_json=(
                t.acceptance_rules_json
            ),
            supersedes_inquiry_task_id=(
                t.supersedes_inquiry_task_id
            ),
            primary_response_id=(
                t.primary_response_id
            ),
            created_by=t.created_by,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in result.scalars().all()
    ]
    return InquiryTaskList(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=InquiryTaskRead,
    summary="Get inquiry task",
)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Get a single inquiry task by ID."""
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    t = result.scalar_one_or_none()
    if t is None:
        raise HTTPException(
            status_code=404,
            detail="Inquiry task not found",
        )
    return InquiryTaskRead(
        inquiry_task_id=t.inquiry_task_id,
        inquiry_case_id=t.inquiry_case_id,
        revision_no=t.revision_no,
        prompt_task_id=t.prompt_task_id,
        task_status=t.task_status,
        priority_score=t.priority_score,
        sla_class=t.sla_class,
        deadline_at=t.deadline_at,
        claim_expires_at=t.claim_expires_at,
        prompt_pack_hash=t.prompt_pack_hash,
        evidence_bundle_hash=(
            t.evidence_bundle_hash
        ),
        question_title=t.question_title,
        question_text=t.question_text,
        required_schema_name=(
            t.required_schema_name
        ),
        required_schema_version=(
            t.required_schema_version
        ),
        bounded_evidence_json=(
            t.bounded_evidence_json
        ),
        acceptance_rules_json=(
            t.acceptance_rules_json
        ),
        supersedes_inquiry_task_id=(
            t.supersedes_inquiry_task_id
        ),
        primary_response_id=t.primary_response_id,
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get(
    "/metrics",
    response_model=InquiryMetricsRead,
    summary="Get inquiry metrics",
)
async def inquiry_metrics(
    db: AsyncSession = Depends(get_db),
) -> InquiryMetricsRead:
    """Return aggregated inquiry metrics."""
    data = await get_metrics(db)
    return InquiryMetricsRead(
        open_count=data["open_count"],
        due_soon_count=data["due_soon_count"],
        overdue_count=data["overdue_count"],
        supersede_rate=data["supersede_rate"],
        response_latency_p50_sec=(
            data["response_latency_p50_sec"]
        ),
        response_latency_p95_sec=(
            data["response_latency_p95_sec"]
        ),
        accept_rate=data["accept_rate"],
        late_response_rate=(
            data["late_response_rate"]
        ),
        manual_uplift_score_delta=(
            data["manual_uplift_score_delta"]
        ),
    )


# ---------------------------------------------------------------
# Action APIs
# ---------------------------------------------------------------

@router.post(
    "/cases/{case_id}/spawn-task",
    response_model=InquiryTaskRead,
    status_code=202,
    summary="Spawn or revise task for case",
)
async def spawn_task_endpoint(
    case_id: UUID,
    body: InquirySpawnTaskRequest,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Spawn a new task, superseding active ones."""
    task = await spawn_inquiry_task(
        db,
        case_id=case_id,
        question_title=body.question_title,
        question_text=body.question_text,
        deadline_at=body.deadline_at,
        sla_class=body.sla_class,
        bounded_evidence_json=(
            body.bounded_evidence_json
        ),
        acceptance_rules_json=(
            body.acceptance_rules_json
        ),
        required_schema_name=(
            body.required_schema_name
        ),
        required_schema_version=(
            body.required_schema_version
        ),
    )
    return InquiryTaskRead(
        inquiry_task_id=task.inquiry_task_id,
        inquiry_case_id=task.inquiry_case_id,
        revision_no=task.revision_no,
        prompt_task_id=task.prompt_task_id,
        task_status=task.task_status,
        priority_score=task.priority_score,
        sla_class=task.sla_class,
        deadline_at=task.deadline_at,
        claim_expires_at=task.claim_expires_at,
        prompt_pack_hash=task.prompt_pack_hash,
        evidence_bundle_hash=(
            task.evidence_bundle_hash
        ),
        question_title=task.question_title,
        question_text=task.question_text,
        required_schema_name=(
            task.required_schema_name
        ),
        required_schema_version=(
            task.required_schema_version
        ),
        bounded_evidence_json=(
            task.bounded_evidence_json
        ),
        acceptance_rules_json=(
            task.acceptance_rules_json
        ),
        supersedes_inquiry_task_id=(
            task.supersedes_inquiry_task_id
        ),
        primary_response_id=(
            task.primary_response_id
        ),
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post(
    "/tasks/{task_id}/claim",
    response_model=InquiryTaskRead,
    summary="Claim inquiry task",
)
async def claim_task_endpoint(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Claim a task for the current operator."""
    try:
        t = await claim_task(
            db,
            task_id=task_id,
            user_id=_PLACEHOLDER_USER,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _task_to_read(t)


@router.post(
    "/tasks/{task_id}/snooze",
    response_model=InquiryTaskRead,
    summary="Snooze inquiry task",
)
async def snooze_task_endpoint(
    task_id: UUID,
    body: InquirySnoozeRequest,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Snooze a task until a given time."""
    try:
        t = await snooze_task(
            db,
            task_id=task_id,
            snooze_until=body.snooze_until,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _task_to_read(t)


@router.post(
    "/tasks/{task_id}/submit-response",
    response_model=InquiryResponseRead,
    status_code=202,
    summary=(
        "Submit direct or external-LLM response"
    ),
)
async def submit_response_endpoint(
    task_id: UUID,
    body: InquiryResponseCreate,
    db: AsyncSession = Depends(get_db),
) -> InquiryResponseRead:
    """Submit a response to an inquiry task."""
    try:
        resp = await submit_inquiry_response(
            db,
            task_id=task_id,
            response_channel=body.response_channel,
            raw_response=body.raw_response,
            model_name_user_entered=(
                body.model_name_user_entered
            ),
            notes=body.notes,
            submitted_by=_PLACEHOLDER_USER,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return InquiryResponseRead(
        inquiry_response_id=(
            resp.inquiry_response_id
        ),
        inquiry_task_id=resp.inquiry_task_id,
        submitted_by=resp.submitted_by,
        response_channel=resp.response_channel,
        model_name_user_entered=(
            resp.model_name_user_entered
        ),
        response_status=resp.response_status,
        submitted_at=resp.submitted_at,
        raw_response=resp.raw_response,
        parsed_json=resp.parsed_json,
        schema_valid=resp.schema_valid,
        parser_version=resp.parser_version,
        evidence_refs_json=(
            resp.evidence_refs_json
        ),
        notes=resp.notes,
    )


@router.post(
    "/tasks/{task_id}/request-reformat",
    response_model=InquiryTaskRead,
    status_code=202,
    summary="Request reformat prompt",
)
async def request_reformat_endpoint(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Request a reformat for invalid response.

    Transitions the task back to
    ``awaiting_response`` so the operator can
    resubmit.
    """
    result = await db.execute(
        select(InquiryTask).where(
            InquiryTask.inquiry_task_id == task_id,
        )
    )
    t = result.scalar_one_or_none()
    if t is None:
        raise HTTPException(
            status_code=404,
            detail="Inquiry task not found",
        )

    reformattable = ("submitted", "parsed")
    if t.task_status not in reformattable:
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot request reformat: "
                f"status is '{t.task_status}'"
            ),
        )
    t.task_status = "awaiting_response"
    await db.commit()
    await db.refresh(t)
    return _task_to_read(t)


@router.post(
    "/tasks/{task_id}/accept",
    response_model=InquiryResolutionRead,
    summary="Accept response into scoring",
)
async def accept_endpoint(
    task_id: UUID,
    body: InquiryAcceptRequest,
    db: AsyncSession = Depends(get_db),
) -> InquiryResolutionRead:
    """Accept a response for trade scoring."""
    try:
        res = await accept_inquiry_response(
            db,
            task_id=task_id,
            response_id=body.response_id,
            weight=body.effective_weight,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return InquiryResolutionRead(
        inquiry_resolution_id=(
            res.inquiry_resolution_id
        ),
        inquiry_task_id=res.inquiry_task_id,
        inquiry_response_id=(
            res.inquiry_response_id
        ),
        resolution_status=res.resolution_status,
        effective_weight=res.effective_weight,
        used_for_decision=res.used_for_decision,
        affects_decision_id=(
            res.affects_decision_id
        ),
        resolution_reason_codes=(
            res.resolution_reason_codes
        ),
        resolved_by=res.resolved_by,
        resolved_at=res.resolved_at,
        notes=res.notes,
    )


@router.post(
    "/tasks/{task_id}/reject",
    response_model=InquiryResolutionRead,
    summary="Reject response",
)
async def reject_endpoint(
    task_id: UUID,
    body: InquiryRejectRequest,
    db: AsyncSession = Depends(get_db),
) -> InquiryResolutionRead:
    """Reject a response."""
    try:
        res = await reject_inquiry_response(
            db,
            task_id=task_id,
            response_id=body.response_id,
            reason=body.reason,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return InquiryResolutionRead(
        inquiry_resolution_id=(
            res.inquiry_resolution_id
        ),
        inquiry_task_id=res.inquiry_task_id,
        inquiry_response_id=(
            res.inquiry_response_id
        ),
        resolution_status=res.resolution_status,
        effective_weight=res.effective_weight,
        used_for_decision=res.used_for_decision,
        affects_decision_id=(
            res.affects_decision_id
        ),
        resolution_reason_codes=(
            res.resolution_reason_codes
        ),
        resolved_by=res.resolved_by,
        resolved_at=res.resolved_at,
        notes=res.notes,
    )


@router.post(
    "/tasks/{task_id}/supersede",
    response_model=InquiryTaskRead,
    status_code=202,
    summary="Supersede task",
)
async def supersede_endpoint(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Supersede a task with a new revision."""
    try:
        t = await supersede_task(
            db, task_id=task_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _task_to_read(t)


@router.post(
    "/tasks/{task_id}/expire",
    response_model=InquiryTaskRead,
    summary="Expire a task",
)
async def expire_endpoint(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InquiryTaskRead:
    """Manually expire a task."""
    try:
        t = await expire_task(
            db, task_id=task_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=409, detail=str(e),
        ) from e
    return _task_to_read(t)


@router.post(
    "/presence",
    summary="Update operator presence",
    status_code=200,
)
async def presence_endpoint(
    body: InquiryPresenceUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update operator presence / availability."""
    p = await update_presence(
        db,
        user_id=_PLACEHOLDER_USER,
        availability_state=body.availability_state,
        focus_mode=body.focus_mode,
        can_receive_push=body.can_receive_push,
        can_receive_urgent=(
            body.can_receive_urgent
        ),
    )
    return {"status": "ok", "updated_at": str(
        p.updated_at,
    )}


# ---------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------

def _task_to_read(
    t: InquiryTask,
) -> InquiryTaskRead:
    """Convert ORM task to read schema.

    Uses explicit attribute access to avoid
    SQLAlchemy lazy-load issues.
    """
    return InquiryTaskRead(
        inquiry_task_id=t.inquiry_task_id,
        inquiry_case_id=t.inquiry_case_id,
        revision_no=t.revision_no,
        prompt_task_id=t.prompt_task_id,
        task_status=t.task_status,
        priority_score=t.priority_score,
        sla_class=t.sla_class,
        deadline_at=t.deadline_at,
        claim_expires_at=t.claim_expires_at,
        prompt_pack_hash=t.prompt_pack_hash,
        evidence_bundle_hash=(
            t.evidence_bundle_hash
        ),
        question_title=t.question_title,
        question_text=t.question_text,
        required_schema_name=(
            t.required_schema_name
        ),
        required_schema_version=(
            t.required_schema_version
        ),
        bounded_evidence_json=(
            t.bounded_evidence_json
        ),
        acceptance_rules_json=(
            t.acceptance_rules_json
        ),
        supersedes_inquiry_task_id=(
            t.supersedes_inquiry_task_id
        ),
        primary_response_id=(
            t.primary_response_id
        ),
        created_by=t.created_by,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )

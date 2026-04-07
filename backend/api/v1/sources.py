"""Source registry API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.sources import (
    SourceBundle,
    SourceCandidate,
    SourceEndpoint,
    SourceRegistry,
)
from backend.schemas.sources import (
    SourceBundleCreate,
    SourceBundleRead,
    SourceCandidateList,
    SourceCandidateRead,
    SourceEndpointCreate,
    SourceEndpointRead,
    SourceRegistryCreate,
    SourceRegistryList,
    SourceRegistryRead,
    SourceRegistryUpdate,
)

router = APIRouter(tags=["sources"])


# --- Source Registry CRUD ---

@router.get("/source-registry", response_model=SourceRegistryList)
async def list_sources(
    status: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    trust_tier: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SourceRegistryList:
    stmt = select(SourceRegistry)
    count_stmt = select(func.count()).select_from(SourceRegistry)
    if status:
        stmt = stmt.where(SourceRegistry.status == status)
        count_stmt = count_stmt.where(SourceRegistry.status == status)
    if source_type:
        stmt = stmt.where(SourceRegistry.source_type == source_type)
        count_stmt = count_stmt.where(SourceRegistry.source_type == source_type)
    if trust_tier:
        stmt = stmt.where(SourceRegistry.trust_tier == trust_tier)
        count_stmt = count_stmt.where(SourceRegistry.trust_tier == trust_tier)
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset).limit(limit).order_by(SourceRegistry.source_code)
    )
    items = [SourceRegistryRead.model_validate(r) for r in result.scalars().all()]
    return SourceRegistryList(items=items, total=total, limit=limit, offset=offset)


@router.get("/source-registry/{source_code}", response_model=SourceRegistryRead)
async def get_source(
    source_code: str,
    db: AsyncSession = Depends(get_db),
) -> SourceRegistryRead:
    result = await db.execute(
        select(SourceRegistry).where(SourceRegistry.source_code == source_code)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_code}' not found")
    return SourceRegistryRead.model_validate(source)


@router.post("/source-registry", response_model=SourceRegistryRead, status_code=201)
async def create_source(
    body: SourceRegistryCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceRegistryRead:
    source = SourceRegistry(**body.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return SourceRegistryRead.model_validate(source)


@router.patch("/source-registry/{source_code}", response_model=SourceRegistryRead)
async def update_source(
    source_code: str,
    body: SourceRegistryUpdate,
    db: AsyncSession = Depends(get_db),
) -> SourceRegistryRead:
    result = await db.execute(
        select(SourceRegistry).where(SourceRegistry.source_code == source_code)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_code}' not found")
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    await db.commit()
    await db.refresh(source)
    return SourceRegistryRead.model_validate(source)


# --- Source Endpoints ---

@router.get("/source-registry/{source_code}/endpoints", response_model=list[SourceEndpointRead])
async def list_source_endpoints(
    source_code: str,
    db: AsyncSession = Depends(get_db),
) -> list[SourceEndpointRead]:
    src = await db.execute(
        select(SourceRegistry.source_id).where(SourceRegistry.source_code == source_code)
    )
    source_id = src.scalar_one_or_none()
    if source_id is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_code}' not found")
    result = await db.execute(
        select(SourceEndpoint).where(SourceEndpoint.source_id == source_id)
    )
    return [SourceEndpointRead.model_validate(r) for r in result.scalars().all()]


@router.post(
    "/source-registry/{source_code}/endpoints",
    response_model=SourceEndpointRead,
    status_code=201,
)
async def create_source_endpoint(
    source_code: str,
    body: SourceEndpointCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceEndpointRead:
    src = await db.execute(
        select(SourceRegistry.source_id).where(SourceRegistry.source_code == source_code)
    )
    source_id = src.scalar_one_or_none()
    if source_id is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_code}' not found")
    endpoint = SourceEndpoint(**{**body.model_dump(), "source_id": source_id})
    db.add(endpoint)
    await db.commit()
    await db.refresh(endpoint)
    return SourceEndpointRead.model_validate(endpoint)


# --- Source Bundles ---

@router.get("/source-bundles", response_model=list[SourceBundleRead])
async def list_source_bundles(
    market_code: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[SourceBundleRead]:
    stmt = select(SourceBundle)
    if market_code:
        from backend.models.core import MarketProfile
        sub = select(MarketProfile.market_profile_id).where(
            MarketProfile.market_code == market_code
        )
        stmt = stmt.where(SourceBundle.market_profile_id.in_(sub))
    result = await db.execute(stmt.order_by(SourceBundle.bundle_code))
    return [SourceBundleRead.model_validate(r) for r in result.scalars().all()]


@router.post("/source-bundles", response_model=SourceBundleRead, status_code=201)
async def create_source_bundle(
    body: SourceBundleCreate,
    db: AsyncSession = Depends(get_db),
) -> SourceBundleRead:
    bundle = SourceBundle(**body.model_dump())
    db.add(bundle)
    await db.commit()
    await db.refresh(bundle)
    return SourceBundleRead.model_validate(bundle)


# --- Source Candidates ---

@router.get("/source-candidates", response_model=SourceCandidateList)
async def list_source_candidates(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> SourceCandidateList:
    stmt = select(SourceCandidate)
    count_stmt = select(func.count()).select_from(SourceCandidate)
    if status:
        stmt = stmt.where(SourceCandidate.status == status)
        count_stmt = count_stmt.where(SourceCandidate.status == status)
    total = (await db.execute(count_stmt)).scalar_one()
    order = SourceCandidate.created_at.desc()
    result = await db.execute(stmt.offset(offset).limit(limit).order_by(order))
    items = [SourceCandidateRead.model_validate(r) for r in result.scalars().all()]
    return SourceCandidateList(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/source-candidates/{candidate_id}/approve-provisional",
    response_model=SourceCandidateRead,
)
async def approve_provisional(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceCandidateRead:
    result = await db.execute(
        select(SourceCandidate).where(SourceCandidate.source_candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Source candidate not found")
    if candidate.status != "candidate":
        msg = f"Cannot approve: current status is '{candidate.status}'"
        raise HTTPException(status_code=409, detail=msg)
    candidate.status = "provisional"
    await db.commit()
    await db.refresh(candidate)
    return SourceCandidateRead.model_validate(candidate)


@router.post(
    "/source-candidates/{candidate_id}/promote",
    response_model=SourceCandidateRead,
)
async def promote_candidate(
    candidate_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SourceCandidateRead:
    result = await db.execute(
        select(SourceCandidate).where(SourceCandidate.source_candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=404, detail="Source candidate not found")
    if candidate.status != "validated":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot promote: current status is '{candidate.status}', must be 'validated'",
        )
    candidate.status = "production"
    await db.commit()
    await db.refresh(candidate)
    return SourceCandidateRead.model_validate(candidate)

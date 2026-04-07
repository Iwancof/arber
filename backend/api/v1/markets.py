"""Market profiles and instruments API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.core import Instrument, MarketProfile
from backend.schemas.markets import (
    InstrumentCreate,
    InstrumentList,
    InstrumentRead,
    MarketProfileCreate,
    MarketProfileList,
    MarketProfileRead,
)

router = APIRouter(tags=["markets"])


@router.get("/markets", response_model=MarketProfileList)
async def list_markets(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    active: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> MarketProfileList:
    stmt = select(MarketProfile)
    count_stmt = select(func.count()).select_from(MarketProfile)
    if active is not None:
        stmt = stmt.where(MarketProfile.active == active)
        count_stmt = count_stmt.where(MarketProfile.active == active)
    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(stmt.offset(offset).limit(limit).order_by(MarketProfile.market_code))
    items = [MarketProfileRead.model_validate(r) for r in result.scalars().all()]
    return MarketProfileList(items=items, total=total, limit=limit, offset=offset)


@router.get("/markets/{market_code}", response_model=MarketProfileRead)
async def get_market(
    market_code: str,
    db: AsyncSession = Depends(get_db),
) -> MarketProfileRead:
    stmt = select(MarketProfile).where(MarketProfile.market_code == market_code)
    result = await db.execute(stmt)
    market = result.scalar_one_or_none()
    if market is None:
        raise HTTPException(status_code=404, detail=f"Market '{market_code}' not found")
    return MarketProfileRead.model_validate(market)


@router.post("/markets", response_model=MarketProfileRead, status_code=201)
async def create_market(
    body: MarketProfileCreate,
    db: AsyncSession = Depends(get_db),
) -> MarketProfileRead:
    market = MarketProfile(**body.model_dump())
    db.add(market)
    await db.commit()
    await db.refresh(market)
    return MarketProfileRead.model_validate(market)


@router.get("/instruments", response_model=InstrumentList)
async def list_instruments(
    market_code: str | None = Query(default=None),
    symbol: str | None = Query(default=None),
    instrument_type: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InstrumentList:
    stmt = select(Instrument)
    count_stmt = select(func.count()).select_from(Instrument)

    if market_code:
        sub = select(MarketProfile.market_profile_id).where(
            MarketProfile.market_code == market_code
        )
        stmt = stmt.where(Instrument.market_profile_id.in_(sub))
        count_stmt = count_stmt.where(Instrument.market_profile_id.in_(sub))
    if symbol:
        stmt = stmt.where(Instrument.symbol.ilike(f"%{symbol}%"))
        count_stmt = count_stmt.where(Instrument.symbol.ilike(f"%{symbol}%"))
    if instrument_type:
        stmt = stmt.where(Instrument.instrument_type == instrument_type)
        count_stmt = count_stmt.where(Instrument.instrument_type == instrument_type)
    if active is not None:
        stmt = stmt.where(Instrument.active == active)
        count_stmt = count_stmt.where(Instrument.active == active)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(stmt.offset(offset).limit(limit).order_by(Instrument.symbol))
    items = [InstrumentRead.model_validate(r) for r in result.scalars().all()]
    return InstrumentList(items=items, total=total, limit=limit, offset=offset)


@router.get("/instruments/{instrument_id}", response_model=InstrumentRead)
async def get_instrument(
    instrument_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InstrumentRead:
    result = await db.execute(
        select(Instrument).where(Instrument.instrument_id == instrument_id)
    )
    instrument = result.scalar_one_or_none()
    if instrument is None:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return InstrumentRead.model_validate(instrument)


@router.post("/instruments", response_model=InstrumentRead, status_code=201)
async def create_instrument(
    body: InstrumentCreate,
    db: AsyncSession = Depends(get_db),
) -> InstrumentRead:
    instrument = Instrument(**body.model_dump())
    db.add(instrument)
    await db.commit()
    await db.refresh(instrument)
    return InstrumentRead.model_validate(instrument)

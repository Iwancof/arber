from fastapi import APIRouter

from backend.api.v1.dossier import router as dossier_router
from backend.api.v1.events import router as events_router
from backend.api.v1.forecasts import router as forecasts_router
from backend.api.v1.health import router as health_router
from backend.api.v1.ingest import router as ingest_router
from backend.api.v1.markets import router as markets_router
from backend.api.v1.overlays import router as overlays_router
from backend.api.v1.sources import router as sources_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(markets_router)
api_v1_router.include_router(sources_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(forecasts_router)
api_v1_router.include_router(dossier_router)
api_v1_router.include_router(overlays_router)

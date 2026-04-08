from fastapi import APIRouter

from backend.api.v1.dossier import router as dossier_router
from backend.api.v1.events import router as events_router
from backend.api.v1.execution import router as execution_router
from backend.api.v1.extensions import router as extensions_router
from backend.api.v1.forecasts import router as forecasts_router
from backend.api.v1.health import router as health_router
from backend.api.v1.ingest import router as ingest_router
from backend.api.v1.inquiry import router as inquiry_router
from backend.api.v1.markets import router as markets_router
from backend.api.v1.ops_chat import router as ops_chat_router
from backend.api.v1.overlays import router as overlays_router
from backend.api.v1.postmortems import router as postmortems_router
from backend.api.v1.prompts import router as prompts_router
from backend.api.v1.replay import router as replay_router
from backend.api.v1.research import router as research_router
from backend.api.v1.sources import router as sources_router
from backend.api.v1.ui import router as ui_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(markets_router)
api_v1_router.include_router(sources_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(ingest_router)
api_v1_router.include_router(forecasts_router)
api_v1_router.include_router(dossier_router)
api_v1_router.include_router(overlays_router)
api_v1_router.include_router(postmortems_router)
api_v1_router.include_router(prompts_router)
api_v1_router.include_router(replay_router)
api_v1_router.include_router(execution_router)
api_v1_router.include_router(extensions_router)
api_v1_router.include_router(inquiry_router)
api_v1_router.include_router(ops_chat_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(ui_router)

from fastapi import APIRouter

from app.api.v1.articles import router as articles_router
from app.api.v1.calendar import router as calendar_router
from app.api.v1.formats import router as formats_router
from app.api.v1.health import router as health_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.settings import router as settings_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/v1", tags=["health"])
api_router.include_router(articles_router, prefix="/v1/articles", tags=["articles"])
api_router.include_router(formats_router, prefix="/v1/formats", tags=["formats"])
api_router.include_router(pipeline_router, prefix="/v1/pipeline", tags=["pipeline"])
api_router.include_router(settings_router, prefix="/v1/settings", tags=["settings"])
api_router.include_router(calendar_router, prefix="/v1/calendar", tags=["calendar"])
api_router.include_router(webhooks_router, prefix="/v1/webhooks", tags=["webhooks"])

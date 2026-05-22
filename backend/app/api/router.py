from fastapi import APIRouter

from app.api.v1.articles import router as articles_router
from app.api.v1.formats import router as formats_router
from app.api.v1.health import router as health_router
from app.api.v1.pipeline import router as pipeline_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/v1", tags=["health"])
api_router.include_router(articles_router, prefix="/v1/articles", tags=["articles"])
api_router.include_router(formats_router, prefix="/v1/formats", tags=["formats"])
api_router.include_router(pipeline_router, prefix="/v1/pipeline", tags=["pipeline"])

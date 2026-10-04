from fastapi import APIRouter
from app.api.v1.endpoints import forecast, stations, health, models_registry

router = APIRouter(prefix="/api/v1")

router.include_router(forecast.router)
router.include_router(stations.router)
router.include_router(health.router)
router.include_router(models_registry.router)

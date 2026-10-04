from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db
from app.models.schemas_response import HealthResponse
from app.services.earth2studio_service import earth2_service

router = APIRouter(tags=["System Health & Diagnostics"])

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Diagnostic global de santé du microservice Tabiria-Nvua Engine :
    - Disponibilité CUDA / GPU
    - Mémoire GPU allouée
    - Connexion à la base de données
    - État des data sources (ERA5 / S3 / Copernicus CDS)
    - Modèles chargés
    """
    cuda_status = earth2_service.get_cuda_status()
    data_sources = await earth2_service.check_data_sources()
    
    # Test de connectivité réelle à la base de données
    db_connected = False
    try:
        await db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False
    
    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.VERSION,
        cuda_available=cuda_status["cuda_available"],
        cuda_device_count=cuda_status["cuda_device_count"],
        current_device_name=cuda_status["current_device_name"],
        gpu_memory_allocated_mb=cuda_status["gpu_memory_allocated_mb"],
        active_models=cuda_status["active_models"],
        database_connected=db_connected,
        data_sources=data_sources
    )

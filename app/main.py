from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import router as api_v1_router
from app.db.session import init_db
from app.services.earth2studio_service import earth2_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire de cycle de vie (Lifespan) FastAPI :
    - Initialisation des tables de la base de données.
    - Warmup et préchargement des modèles Earth2Studio dans la mémoire GPU.
    """
    logger.info("=== Démarrage de Tabiria-Nvua Engine (GeoCongo AI) ===")
    await init_db()
    await earth2_service.initialize_models()
    yield
    logger.info("=== Arrêt de Tabiria-Nvua Engine ===")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Microservice backend de prévision météorologique extrême et d'alerte climatique propulsé par NVIDIA Earth2Studio & FastAPI.",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes API v1
app.include_router(api_v1_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "module": settings.MODULE_SLUG,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

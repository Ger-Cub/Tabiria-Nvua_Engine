from typing import List
from fastapi import APIRouter
from app.models.schemas_response import ModelInfo
from app.services.earth2studio_service import earth2_service

router = APIRouter(prefix="/models", tags=["Earth2Studio Models Registry"])

@router.get("", response_model=List[ModelInfo])
async def list_models():
    """
    Catalogue complet des modèles d'IA météorologiques préchargés et supportés par Tabiria-Nvua Engine.
    """
    loaded = earth2_service.loaded_models
    
    models_metadata = [
        ModelInfo(
            name="FourCastNet",
            description="Modèle mondial FNO basé sur Fourier pour prévisions rapides à haute résolution spatiale.",
            resolution="0.25° (~25 km)",
            supported_variables=["total_precipitation", "temperature_2m", "wind_u10m", "wind_v10m", "surface_pressure"],
            status=loaded.get("FourCastNet", {}).get("status", "ready")
        ),
        ModelInfo(
            name="GraphCast",
            description="Modèle de prévision météorologique mondial basé sur les Graph Neural Networks (GNN) de DeepMind.",
            resolution="0.25° (~25 km)",
            supported_variables=["total_precipitation", "temperature_2m", "geopotential", "wind_u10m", "wind_v10m"],
            status=loaded.get("GraphCast", {}).get("status", "ready")
        ),
        ModelInfo(
            name="Pangu-Weather",
            description="Modèle 3D Transformer de haute précision pour prévisions synoptiques et extrêmes.",
            resolution="0.25° (~25 km)",
            supported_variables=["total_precipitation", "temperature_2m", "mean_sea_level_pressure"],
            status=loaded.get("Pangu-Weather", {}).get("status", "ready")
        ),
        ModelInfo(
            name="DLWP",
            description="Deep Learning Weather Prediction basé sur une discrétisation sphérique HEALPix.",
            resolution="1.0° (~100 km)",
            supported_variables=["temperature_2m", "total_precipitation"],
            status=loaded.get("DLWP", {}).get("status", "ready")
        )
    ]
    return models_metadata

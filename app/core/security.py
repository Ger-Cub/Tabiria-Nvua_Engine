from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)

def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Vérifie la validité de la clé d'API passée dans les en-têtes HTTP (X-API-Key).
    """
    if not api_key or api_key not in settings.VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé API invalide ou manquante pour Tabiria-Nvua Engine."
        )
    return api_key

def verify_station_key(secret_key: str) -> bool:
    """
    Vérifie la clé secrète transmise par une station météo locale ou une passerelle IoT.
    """
    if not secret_key or (secret_key != settings.STATION_SECRET_KEY and secret_key not in settings.VALID_API_KEYS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé secrète de station IoT non autorisée."
        )
    return True

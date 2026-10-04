import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Security, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.security import verify_station_key, verify_api_key
from app.db.session import get_db
from app.models.station_orm import WeatherStation, StationTelemetry
from app.models.schemas_request import StationIngestionPayload
from app.models.schemas_response import StationIngestionResponse, StationSummary
from app.services.station_assimilator import StationAssimilator

router = APIRouter(prefix="/stations", tags=["IoT Weather Stations & Telemetry"])
logger = logging.getLogger("nvua_engine.stations_api")

@router.post("/ingest", response_model=StationIngestionResponse)
async def ingest_station_metrics(
    payload: StationIngestionPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint d'ingestion directe pour les stations météorologiques physiques connectées (IoT / LoRaWAN).
    - Authentifie la clé secrète de la station.
    - Exécute le contrôle qualité physique (QC) et la détection d'alertes locales.
    - Persiste les mesures en base de données.
    """
    # 1. Vérification de la clé secrète
    verify_station_key(payload.secret_key)
    
    # 2. Validation & Contrôle Qualité
    payload_dict = payload.model_dump()
    is_valid, reason, quality_flags = StationAssimilator.validate_and_qc(payload_dict)
    
    if not is_valid:
        logger.error(f"Rejet de la station {payload.station_id}: {reason}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Contrôle qualité échoué pour la station {payload.station_id}: {reason}"
        )

    # 3. Persistance de la station (Upsert)
    stmt = select(WeatherStation).where(WeatherStation.station_id == payload.station_id)
    result = await db.execute(stmt)
    station = result.scalar_one_or_none()

    clean_ts_str = payload.timestamp.replace("Z", "+00:00")
    parsed_timestamp = datetime.fromisoformat(clean_ts_str)

    if not station:
        station = WeatherStation(
            station_id=payload.station_id,
            name=f"Station {payload.station_id}",
            latitude=payload.location.latitude,
            longitude=payload.location.longitude,
            elevation_m=payload.location.elevation_m,
            is_active=True,
            last_seen=parsed_timestamp
        )
        db.add(station)
    else:
        station.latitude = payload.location.latitude
        station.longitude = payload.location.longitude
        station.elevation_m = payload.location.elevation_m
        station.last_seen = parsed_timestamp
        station.is_active = True

    # 4. Enregistrement de la télémétrie
    metrics = payload.metrics
    telemetry = StationTelemetry(
        station_id=payload.station_id,
        timestamp=parsed_timestamp,
        temperature_c=metrics.temperature_c,
        humidity_pct=metrics.humidity_pct,
        pressure_hpa=metrics.pressure_hpa,
        precipitation_mm_last_hour=metrics.precipitation_mm_last_hour or 0.0,
        precipitation_intensity_mm_h=metrics.precipitation_intensity_mm_h or 0.0,
        wind_speed_ms=metrics.wind_speed_ms,
        wind_direction_deg=metrics.wind_direction_deg,
        solar_radiation_w_m2=metrics.solar_radiation_w_m2,
        quality_flags=quality_flags
    )
    db.add(telemetry)
    await db.commit()

    logger.info(f"Télémesure de la station {payload.station_id} persistée avec succès.")

    return StationIngestionResponse(
        status="success",
        message="Télémesure de station validée et enregistrée en base de données.",
        station_id=payload.station_id,
        timestamp=payload.timestamp,
        quality_flags=quality_flags
    )

@router.get("", response_model=List[StationSummary], dependencies=[Security(verify_api_key)])
async def list_stations(db: AsyncSession = Depends(get_db)):
    """
    Retourne la liste de toutes les stations météorologiques enregistrées et leur dernier état de santé.
    """
    stmt = select(WeatherStation)
    result = await db.execute(stmt)
    stations = result.scalars().all()

    summaries = []
    for st in stations:
        # Récupérer la dernière télémétrie
        tel_stmt = (
            select(StationTelemetry)
            .where(StationTelemetry.station_id == st.station_id)
            .order_by(desc(StationTelemetry.timestamp))
            .limit(1)
        )
        tel_res = await db.execute(tel_stmt)
        last_tel = tel_res.scalar_one_or_none()

        last_metrics = None
        if last_tel:
            last_metrics = {
                "temperature_c": last_tel.temperature_c,
                "humidity_pct": last_tel.humidity_pct,
                "pressure_hpa": last_tel.pressure_hpa,
                "precipitation_mm_last_hour": last_tel.precipitation_mm_last_hour,
                "wind_speed_ms": last_tel.wind_speed_ms,
                "wind_direction_deg": last_tel.wind_direction_deg
            }

        summaries.append(StationSummary(
            station_id=st.station_id,
            name=st.name,
            latitude=st.latitude,
            longitude=st.longitude,
            elevation_m=st.elevation_m,
            is_active=st.is_active,
            last_seen=st.last_seen.isoformat() if st.last_seen else None,
            last_metrics=last_metrics
        ))

    return summaries


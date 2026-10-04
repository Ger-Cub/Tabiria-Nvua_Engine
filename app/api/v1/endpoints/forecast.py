from fastapi import APIRouter, HTTPException, Security, Depends, status
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.config import settings
from app.core.security import verify_api_key
from app.db.session import get_db
from app.models.station_orm import WeatherStation, StationTelemetry
from app.models.schemas_request import PointForecastRequest, BBoxForecastRequest
from app.models.schemas_response import PointForecastResponse, ForecastStep, BBoxGeoJSONResponse, BBoxFeature
from app.services.earth2studio_service import earth2_service
from app.services.station_assimilator import StationAssimilator

router = APIRouter(prefix="/forecast", tags=["Forecast & Climate Intelligence"])

@router.post("/point", response_model=PointForecastResponse, dependencies=[Security(verify_api_key)])
async def get_point_forecast(
    payload: PointForecastRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Calcule une prévision météorologique ciblée pour une coordonnée unique (ex: mine, ville, barrage),
    avec assimilation des stations physiques locales enregistrées en base de données.
    """
    bias_correction = None
    if payload.use_local_station_correction:
        # Récupération des stations enregistrées en BDD
        stmt = select(WeatherStation).where(WeatherStation.is_active == True)
        result = await db.execute(stmt)
        stations = result.scalars().all()

        station_data_list = []
        for st in stations:
            # Récupérer la dernière métrique disponible
            tel_stmt = (
                select(StationTelemetry)
                .where(StationTelemetry.station_id == st.station_id)
                .order_by(desc(StationTelemetry.timestamp))
                .limit(1)
            )
            tel_res = await db.execute(tel_stmt)
            last_tel = tel_res.scalar_one_or_none()

            metrics = {}
            if last_tel:
                metrics = {
                    "temperature_c": last_tel.temperature_c,
                    "precipitation_mm_last_hour": last_tel.precipitation_mm_last_hour,
                    "pressure_hpa": last_tel.pressure_hpa
                }

            station_data_list.append({
                "station_id": st.station_id,
                "latitude": st.latitude,
                "longitude": st.longitude,
                "metrics": metrics
            })

        if station_data_list:
            bias_correction = StationAssimilator.compute_local_bias_correction(
                station_data_list, payload.latitude, payload.longitude
            )

    raw_steps = await earth2_service.run_point_forecast(
        latitude=payload.latitude,
        longitude=payload.longitude,
        variables=payload.variables,
        horizon_hours=payload.forecast_horizon_hours,
        model_name=payload.model_name,
        station_bias_correction=bias_correction
    )

    steps = [ForecastStep(**s) for s in raw_steps]
    
    summary_alerts = []
    for s in steps:
        if s.alert_triggered and s.alert_reason and s.alert_reason not in summary_alerts:
            summary_alerts.append(s.alert_reason)

    model_used = payload.model_name if payload.model_name else settings.DEFAULT_FORECAST_MODEL

    return PointForecastResponse(
        latitude=payload.latitude,
        longitude=payload.longitude,
        model_used=model_used,
        generated_at=datetime.now(timezone.utc).isoformat(),
        forecast_horizon_hours=payload.forecast_horizon_hours,
        steps=steps,
        station_correction_applied=bool(payload.use_local_station_correction and bias_correction),
        summary_alerts=summary_alerts
    )

@router.post("/bbox", response_model=BBoxGeoJSONResponse, dependencies=[Security(verify_api_key)])
async def get_bbox_forecast(payload: BBoxForecastRequest):
    """
    Génère une grille spatio-temporelle de prévision pour une emprise BBox [xmin, ymin, xmax, ymax],
    formatée en GeoJSON FeatureCollection pour intégration SIG (QGIS/ArcGIS).
    """
    if len(payload.bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La BBox doit contenir exactement 4 coordonnées [xmin, ymin, xmax, ymax]."
        )

    raw_features = await earth2_service.run_bbox_forecast(
        bbox=payload.bbox,
        variables=payload.variables,
        horizon_hours=payload.forecast_horizon_hours,
        model_name=payload.model_name
    )

    features = [BBoxFeature(**f) for f in raw_features]
    model_used = payload.model_name if payload.model_name else settings.DEFAULT_FORECAST_MODEL

    return BBoxGeoJSONResponse(
        type="FeatureCollection",
        features=features,
        metadata={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_used": model_used,
            "forecast_horizon_hours": payload.forecast_horizon_hours,
            "bbox": payload.bbox,
            "variables": payload.variables
        }
    )

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, confloat

class StationLocation(BaseModel):
    latitude: confloat(ge=-90.0, le=90.0) = Field(..., description="Latitude de la station en WGS84")
    longitude: confloat(ge=-180.0, le=180.0) = Field(..., description="Longitude de la station en WGS84")
    elevation_m: Optional[float] = Field(default=None, description="Altitude de la station en mètres")

class StationMetrics(BaseModel):
    temperature_c: Optional[confloat(ge=-50.0, le=70.0)] = Field(None, description="Température de l'air en °C")
    humidity_pct: Optional[confloat(ge=0.0, le=100.0)] = Field(None, description="Humidité relative en %")
    pressure_hpa: Optional[confloat(ge=800.0, le=1100.0)] = Field(None, description="Pression atmosphérique en hPa")
    precipitation_mm_last_hour: Optional[confloat(ge=0.0)] = Field(0.0, description="Précipitations cumulées sur la dernière heure en mm")
    precipitation_intensity_mm_h: Optional[confloat(ge=0.0)] = Field(0.0, description="Intensité des précipitations en mm/h")
    wind_speed_ms: Optional[confloat(ge=0.0, le=150.0)] = Field(None, description="Vitesse du vent en m/s")
    wind_direction_deg: Optional[confloat(ge=0.0, le=360.0)] = Field(None, description="Direction du vent en degrés")
    solar_radiation_w_m2: Optional[confloat(ge=0.0, le=1500.0)] = Field(None, description="Rayonnement solaire en W/m²")

class StationIngestionPayload(BaseModel):
    station_id: str = Field(..., description="Identifiant unique de la station météo locale")
    secret_key: str = Field(..., description="Clé secrète d'authentification de la station")
    timestamp: str = Field(..., description="Horodatage ISO 8601 UTC de la mesure")
    location: StationLocation
    metrics: StationMetrics

class PointForecastRequest(BaseModel):
    latitude: confloat(ge=-90.0, le=90.0) = Field(..., description="Latitude cible en WGS84")
    longitude: confloat(ge=-180.0, le=180.0) = Field(..., description="Longitude cible en WGS84")
    variables: List[str] = Field(
        default=["total_precipitation", "temperature_2m", "wind_u10m", "wind_v10m"],
        description="Variables météorologiques à prédire"
    )
    forecast_horizon_hours: conint(ge=6, le=240) = Field(72, description="Horizon de prévision en heures")
    use_local_station_correction: bool = Field(True, description="Appliquer ou non la correction par stations locales proches")
    model_name: Optional[str] = Field(None, description="Nom du modèle Earth2Studio (ex: FourCastNet, GraphCast)")

class BBoxForecastRequest(BaseModel):
    bbox: List[float] = Field(..., description="Emprise spatiale [xmin, ymin, xmax, ymax] en WGS84")
    variables: List[str] = Field(
        default=["total_precipitation"],
        description="Variables météorologiques pour la grille"
    )
    forecast_horizon_hours: conint(ge=6, le=120) = Field(24, description="Horizon de prévision en heures")
    output_format: str = Field("geojson", description="Format de sortie spatial (geojson, netcdf, json)")
    model_name: Optional[str] = Field(None, description="Nom du modèle Earth2Studio")

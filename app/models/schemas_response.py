from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class StationIngestionResponse(BaseModel):
    status: str = Field("success", description="Statut de l'ingestion")
    message: str = Field(..., description="Message descriptif")
    station_id: str
    timestamp: str
    quality_flags: Dict[str, Any] = Field(default_factory=dict, description="Résultats du contrôle qualité et drapeaux d'alerte")

class StationSummary(BaseModel):
    station_id: str
    name: str
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    is_active: bool
    last_seen: Optional[str] = None
    last_metrics: Optional[Dict[str, Any]] = None

class ForecastStep(BaseModel):
    time_offset_hours: int
    timestamp: str
    values: Dict[str, float]
    alert_triggered: bool = False
    alert_reason: Optional[str] = None
    alert_severity: Optional[str] = None

class PointForecastResponse(BaseModel):
    latitude: float
    longitude: float
    model_used: str
    generated_at: str
    forecast_horizon_hours: int
    steps: List[ForecastStep]
    station_correction_applied: bool
    summary_alerts: List[str] = Field(default_factory=list)

class BBoxFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class BBoxGeoJSONResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[BBoxFeature]
    metadata: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    version: str
    cuda_available: bool
    cuda_device_count: int
    current_device_name: Optional[str] = None
    gpu_memory_allocated_mb: float = 0.0
    active_models: List[str]
    database_connected: bool
    data_sources: Dict[str, str] = Field(default_factory=dict)

class ModelInfo(BaseModel):
    name: str
    description: str
    resolution: str
    supported_variables: List[str]
    status: str

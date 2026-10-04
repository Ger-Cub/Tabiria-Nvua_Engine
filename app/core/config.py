import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tabiria-Nvua Engine - geocongoai AI Weather & Climate Intelligence"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(default="tabiria-nvua_Engine_geocongoai_super_secret_key_2026", env="SECRET_KEY")
    API_KEY_HEADER: str = "X-API-Key"
    STATION_SECRET_KEY: str = Field(default="nvua_station_token_xxx", env="STATION_SECRET_KEY")
    VALID_API_KEYS: List[str] = ["geocongoai_key_master_2026", "nvua_station_token_xxx", "demo_key"]
    
    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./tabiria-nvua_Engine.db", env="DATABASE_URL")
    
    # GPU / Compute Settings
    USE_GPU_IF_AVAILABLE: bool = Field(default=True, env="USE_GPU_IF_AVAILABLE")
    DEFAULT_CUDA_DEVICE: int = Field(default=0, env="DEFAULT_CUDA_DEVICE")
    MODEL_CACHE_DIR: str = Field(default="./cache/earth2studio", env="MODEL_CACHE_DIR")
    
    # Earth2Studio & Data Sources
    DEFAULT_FORECAST_MODEL: str = Field(default="FourCastNet", env="DEFAULT_FORECAST_MODEL")
    SUPPORTED_MODELS: List[str] = ["FourCastNet", "GraphCast", "Pangu-Weather", "DLWP"]
    ERA5_DATASET_BUCKET: str = Field(default="s3://era5-pds/zarr/", env="ERA5_DATASET_BUCKET")
    
    # Alert Thresholds
    ALERT_PRECIP_INTENSITY_MM_H: float = Field(default=10.0, env="ALERT_PRECIP_INTENSITY_MM_H")
    ALERT_PRECIP_24H_MM: float = Field(default=50.0, env="ALERT_PRECIP_24H_MM")
    ALERT_WIND_GUST_MS: float = Field(default=20.0, env="ALERT_WIND_GUST_MS")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"

settings = Settings()

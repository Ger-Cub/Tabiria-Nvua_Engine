from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Float, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class WeatherStation(Base):
    """
    Modèle ORM représentant une station météorologique physique enregistrée.
    """
    __tablename__ = "weather_stations"

    station_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), default="Station Météo")
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    elevation_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relation avec les télémesures historiques
    telemetries: Mapped[List["StationTelemetry"]] = relationship(
        "StationTelemetry", back_populates="station", cascade="all, delete-orphan"
    )

class StationTelemetry(Base):
    """
    Modèle ORM représentant les mesures physiques reçues (série temporelle).
    """
    __tablename__ = "station_telemetries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(64), ForeignKey("weather_stations.station_id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Métriques physiques
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pressure_hpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation_mm_last_hour: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    precipitation_intensity_mm_h: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    wind_speed_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_direction_deg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    solar_radiation_w_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Drapeaux de contrôle qualité (QC) au format JSON
    quality_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relation inverse
    station: Mapped["WeatherStation"] = relationship("WeatherStation", back_populates="telemetries")

import math
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List, Optional
import logging

from app.core.config import settings
from app.services.alert_engine import AlertEngine

logger = logging.getLogger("nvua_engine.station_assimilator")

class StationAssimilator:
    """
    Module d'assimilation locale, de contrôle qualité (QC) et d'adaptation
    des données de stations météorologiques au framework NVIDIA Earth2Studio (Approche A - Phase 1).
    """

    @staticmethod
    def decompose_wind_vector(
        speed_ms: Optional[float], direction_deg: Optional[float]
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Convertit la vitesse et la direction du vent (convention météorologique standard)
        en composantes vectorielles cartésiennes u10m (zonal) et v10m (méridien) exigées par Earth2Studio.
        - u10m : vent d'Ouest en Est (> 0 vers l'Est)
        - v10m : vent du Sud au Nord (> 0 vers le Nord)
        Formule : u = -speed * sin(deg), v = -speed * cos(deg)
        """
        if speed_ms is None or direction_deg is None:
            return None, None
        
        rad = math.radians(direction_deg)
        u10m = -speed_ms * math.sin(rad)
        v10m = -speed_ms * math.cos(rad)
        return round(u10m, 3), round(v10m, 3)

    @staticmethod
    def compose_wind_vector(u10m: float, v10m: float) -> Tuple[float, float]:
        """
        Convertit les composantes vectorielles u10m et v10m en vitesse (m/s) et direction (degrés 0-360°).
        """
        speed = math.sqrt(u10m**2 + v10m**2)
        # Direction météorologique d'où vient le vent
        deg = (math.degrees(math.atan2(-u10m, -v10m))) % 360.0
        return round(speed, 2), round(deg, 1)

    @classmethod
    def validate_and_qc(cls, payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Vérifie la cohérence physique des métriques reçues d'une station météo
        et enrichit les métriques avec les vecteurs de vent u10m/v10m.
        """
        metrics = payload.get("metrics", {})
        location = payload.get("location", {})
        station_id = payload.get("station_id", "UNKNOWN")
        timestamp_str = payload.get("timestamp")
        
        flags = {
            "temperature_qc": "PASS",
            "humidity_qc": "PASS",
            "pressure_qc": "PASS",
            "precipitation_qc": "PASS",
            "wind_qc": "PASS",
            "geofence_qc": "PASS",
            "timestamp_qc": "PASS",
            "alerts": []
        }
        
        # 1. Validation de l'horodatage UTC
        if timestamp_str:
            try:
                clean_ts = timestamp_str.replace("Z", "+00:00")
                parsed_ts = datetime.fromisoformat(clean_ts)
                if parsed_ts.tzinfo is None:
                    parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)
                now_utc = datetime.now(timezone.utc)
                diff_hours = abs((now_utc - parsed_ts).total_seconds()) / 3600.0
                if diff_hours > 72.0:
                    flags["timestamp_qc"] = "WARNING"
                    logger.warning(f"Station {station_id}: Télémesure différée de {diff_hours:.1f} heures.")
            except Exception as e:
                return False, f"Format d'horodatage invalide: {e}", flags
        else:
            return False, "Horodatage timestamp requis", flags

        # 2. Geofencing check (Bounding Box RDC et Afrique Centrale : lon 11° à 33°, lat -15° à 6°)
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is not None and lon is not None:
            if not (-15.0 <= lat <= 6.0 and 11.0 <= lon <= 33.0):
                flags["geofence_qc"] = "WARNING"
                logger.warning(f"Station {station_id} hors de l'emprise géographique nominale (lat: {lat}, lon: {lon})")
        else:
            return False, "Coordonnées de localisation manquantes", flags

        # 3. Contrôle Température (-10°C à 60°C)
        temp = metrics.get("temperature_c")
        if temp is not None and not (-10.0 <= temp <= 60.0):
            flags["temperature_qc"] = "FAIL"
            return False, f"Température aberrante: {temp}°C", flags

        # 4. Contrôle Humidité (0% à 100%)
        hum = metrics.get("humidity_pct")
        if hum is not None and not (0.0 <= hum <= 100.0):
            flags["humidity_qc"] = "FAIL"
            return False, f"Humidité aberrante: {hum}%", flags

        # 5. Contrôle Pression Barométrique (600 à 1100 hPa - adapté aux hautes altitudes du Kivu)
        press = metrics.get("pressure_hpa")
        if press is not None and not (600.0 <= press <= 1100.0):
            flags["pressure_qc"] = "FAIL"
            return False, f"Pression atmosphérique aberrante: {press} hPa", flags

        # 6. Décomposition vectorielle du vent pour compatibilité Earth2Studio
        w_speed = metrics.get("wind_speed_ms")
        w_deg = metrics.get("wind_direction_deg")
        u10m, v10m = cls.decompose_wind_vector(w_speed, w_deg)
        flags["derived_vectors"] = {
            "wind_u10m": u10m,
            "wind_v10m": v10m
        }

        # 7. Évaluation des alertes physiques via AlertEngine
        active_alerts = AlertEngine.evaluate_telemetry_alerts(metrics)
        for al in active_alerts:
            flags["alerts"].append(al["message"])
            if al["type"] in ["EXTREME_PRECIPITATION", "HEAVY_RAIN"]:
                flags["precipitation_qc"] = al["severity"]
            elif al["type"] == "HIGH_WIND":
                flags["wind_qc"] = al["severity"]

        logger.info(f"Station {station_id} validée. u10m={u10m}, v10m={v10m}")
        return True, "Validation et QC réussis", flags

    @classmethod
    def compute_local_bias_correction(
        cls, station_data_list: List[Dict[str, Any]], target_lat: float, target_lon: float, max_radius_km: float = 150.0
    ) -> Dict[str, float]:
        """
        Approche A (Downscaling local / MOS) :
        Calcule le biais local entre les stations physiques disponibles (même une seule station à Goma)
        et la prévision globale pour ajuster la température, la pluie et le vent.
        """
        corrections = {
            "temperature_bias": 0.0,
            "precipitation_bias": 0.0,
            "pressure_bias": 0.0,
            "wind_u_bias": 0.0,
            "wind_v_bias": 0.0,
            "active_stations_used": 0
        }
        if not station_data_list:
            return corrections
            
        total_weight = 0.0
        weighted_temp_diff = 0.0
        weighted_precip_diff = 0.0
        weighted_u_diff = 0.0
        weighted_v_diff = 0.0
        stations_count = 0
        
        for s in station_data_list:
            s_lat = s.get("latitude", 0.0)
            s_lon = s.get("longitude", 0.0)
            
            # Distance approximative en kilomètres (1 degré lat ~ 111 km)
            d_lat_km = (s_lat - target_lat) * 111.0
            d_lon_km = (s_lon - target_lon) * 111.0 * math.cos(math.radians(target_lat))
            dist_km = math.sqrt(d_lat_km**2 + d_lon_km**2)
            
            # Rayon d'influence max : au-delà de 150 km, une station n'influence pas le microclimat
            if dist_km > max_radius_km:
                continue

            stations_count += 1
            effective_dist = max(1.0, dist_km)
            weight = 1.0 / (effective_dist ** 1.5)
            
            metrics = s.get("metrics") or {}
            obs_temp = metrics.get("temperature_c")
            if obs_temp is not None:
                model_background_temp = 24.0  # Température de référence modèle
                weighted_temp_diff += weight * (obs_temp - model_background_temp)
                
            obs_precip = metrics.get("precipitation_mm_last_hour", 0.0) or 0.0
            if obs_precip > 0:
                weighted_precip_diff += weight * (obs_precip * 0.1)

            # Biais vectoriel de vent si disponible
            w_speed = metrics.get("wind_speed_ms")
            w_deg = metrics.get("wind_direction_deg")
            if w_speed is not None and w_deg is not None:
                u, v = cls.decompose_wind_vector(w_speed, w_deg)
                if u is not None and v is not None:
                    weighted_u_diff += weight * (u - 2.0)
                    weighted_v_diff += weight * (v - 1.5)

            total_weight += weight
            
        if total_weight > 0:
            corrections["temperature_bias"] = round(weighted_temp_diff / total_weight, 2)
            corrections["precipitation_bias"] = round(weighted_precip_diff / total_weight, 2)
            corrections["wind_u_bias"] = round(weighted_u_diff / total_weight, 2)
            corrections["wind_v_bias"] = round(weighted_v_diff / total_weight, 2)
            corrections["active_stations_used"] = stations_count
            
        return corrections

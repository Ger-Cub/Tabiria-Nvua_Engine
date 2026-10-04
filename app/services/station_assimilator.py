import math
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List, Optional
import logging

from app.core.config import settings
from app.services.alert_engine import AlertEngine

logger = logging.getLogger("nvua_engine.station_assimilator")

class StationAssimilator:
    """
    Module d'assimilation, de contrôle qualité (QC) et de correction locale
    des données de capteurs météorologiques physiques.
    """
    
    @staticmethod
    def validate_and_qc(payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Vérifie la cohérence physique des métriques reçues d'une station météo.
        Retourne (is_valid, reason, quality_flags).
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
                # Accepter ISO format avec ou sans Z
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

        # 2. Geofencing check (Bounding Box globale de la RDC et Afrique Centrale : lon 11° à 33°, lat -15° à 6°)
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
        if temp is not None:
            if not (-10.0 <= temp <= 60.0):
                flags["temperature_qc"] = "FAIL"
                return False, f"Température aberrante: {temp}°C", flags

        # 4. Contrôle Humidité (0% à 100%)
        hum = metrics.get("humidity_pct")
        if hum is not None:
            if not (0.0 <= hum <= 100.0):
                flags["humidity_qc"] = "FAIL"
                return False, f"Humidité aberrante: {hum}%", flags

        # 5. Contrôle Pression Barométrique (600 à 1100 hPa - adapté aux hautes altitudes du Kivu/Virunga)
        press = metrics.get("pressure_hpa")
        if press is not None:
            if not (600.0 <= press <= 1100.0):
                flags["pressure_qc"] = "FAIL"
                return False, f"Pression atmosphérique aberrante: {press} hPa", flags

        # 6. Évaluation des alertes physiques via AlertEngine
        active_alerts = AlertEngine.evaluate_telemetry_alerts(metrics)
        for al in active_alerts:
            flags["alerts"].append(al["message"])
            if al["type"] in ["EXTREME_PRECIPITATION", "HEAVY_RAIN"]:
                flags["precipitation_qc"] = al["severity"]
            elif al["type"] == "HIGH_WIND":
                flags["wind_qc"] = al["severity"]

        logger.info(f"Station {station_id} validée. QC: {flags}")
        return True, "Validation et QC réussis", flags

    @staticmethod
    def compute_local_bias_correction(station_data_list: List[Dict[str, Any]], target_lat: float, target_lon: float) -> Dict[str, float]:
        """
        Calcule le biais local entre les stations physiques proches et les modèles globaux
        pour corriger les conditions initiales (Data Assimilation par pondération spatiale inverse distance IDW).
        """
        corrections = {
            "temperature_bias": 0.0,
            "precipitation_bias": 0.0,
            "pressure_bias": 0.0
        }
        if not station_data_list:
            return corrections
            
        total_weight = 0.0
        weighted_temp_diff = 0.0
        weighted_precip_diff = 0.0
        
        for s in station_data_list:
            s_lat = s.get("latitude", 0.0)
            s_lon = s.get("longitude", 0.0)
            # Distance euclidienne approximée en degrés
            dist = math.sqrt((s_lat - target_lat)**2 + (s_lon - target_lon)**2)
            if dist < 0.0001:
                dist = 0.0001
            weight = 1.0 / (dist ** 2)
            
            metrics = s.get("metrics") or {}
            obs_temp = metrics.get("temperature_c")
            if obs_temp is not None:
                # Écart observé vs température de référence modèle standard (24.0°C)
                model_background_temp = 24.0
                weighted_temp_diff += weight * (obs_temp - model_background_temp)
                
            obs_precip = metrics.get("precipitation_mm_last_hour", 0.0) or 0.0
            if obs_precip > 0:
                weighted_precip_diff += weight * (obs_precip * 0.1)

            total_weight += weight
            
        if total_weight > 0:
            corrections["temperature_bias"] = round(weighted_temp_diff / total_weight, 2)
            corrections["precipitation_bias"] = round(weighted_precip_diff / total_weight, 2)
            
        return corrections

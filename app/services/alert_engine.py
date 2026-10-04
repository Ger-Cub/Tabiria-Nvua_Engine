from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings

class AlertEngine:
    """
    Moteur de détection et de classification des alertes aux risques météorologiques extrêmes :
    - Précipitations torrentielles (crues éclairs, glissements de terrain dans les zones minières/urbaines)
    - Rafales de vent destructrices
    - Chutes brutales de pression barométrique (cellules orageuses convectives)
    """

    @classmethod
    def evaluate_telemetry_alerts(cls, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Évalue les métriques physiques reçues en temps réel d'une station IoT.
        """
        alerts = []
        
        # 1. Précipitation horaire
        precip_last_hour = metrics.get("precipitation_mm_last_hour") or 0.0
        if precip_last_hour >= settings.ALERT_PRECIP_24H_MM:
            alerts.append({
                "type": "EXTREME_PRECIPITATION",
                "severity": "CRITICAL",
                "message": f"Cumul horaire catastrophique détecté ({precip_last_hour} mm). Risque imminent d'inondation éclair.",
                "threshold": settings.ALERT_PRECIP_24H_MM,
                "current_value": precip_last_hour
            })
        elif precip_last_hour >= settings.ALERT_PRECIP_INTENSITY_MM_H:
            alerts.append({
                "type": "HEAVY_RAIN",
                "severity": "WARNING",
                "message": f"Forte précipitation en cours ({precip_last_hour} mm/h). Vigilance renforcée.",
                "threshold": settings.ALERT_PRECIP_INTENSITY_MM_H,
                "current_value": precip_last_hour
            })

        # 2. Vitesse du vent
        wind_speed = metrics.get("wind_speed_ms")
        if wind_speed and wind_speed >= settings.ALERT_WIND_GUST_MS:
            alerts.append({
                "type": "HIGH_WIND",
                "severity": "WARNING",
                "message": f"Vents violents détectés ({wind_speed} m/s). Risque pour les toitures et infrastructures minières.",
                "threshold": settings.ALERT_WIND_GUST_MS,
                "current_value": wind_speed
            })

        return alerts

    @classmethod
    def evaluate_forecast_step(cls, values: Dict[str, float]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Évalue les valeurs de prévision pour un pas de temps donné.
        Retourne (is_alert, alert_reason, severity).
        """
        precip = values.get("total_precipitation", 0.0)
        wind_u = values.get("wind_u10m", 0.0)
        wind_v = values.get("wind_v10m", 0.0)
        wind_mag = (wind_u**2 + wind_v**2)**0.5 if (wind_u or wind_v) else values.get("wind_speed", 0.0)

        if precip >= settings.ALERT_PRECIP_INTENSITY_MM_H * 2:
            return True, f"Précipitation extrême prévue ({precip:.1f} mm)", "CRITICAL"
        elif precip >= settings.ALERT_PRECIP_INTENSITY_MM_H:
            return True, f"Précipitation intense prévue ({precip:.1f} mm)", "WARNING"
        elif wind_mag >= settings.ALERT_WIND_GUST_MS:
            return True, f"Vents violents prévus ({wind_mag:.1f} m/s)", "WARNING"

        return False, None, None

from typing import Tuple

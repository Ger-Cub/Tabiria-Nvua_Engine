import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger("nvua_engine.spatial_exporter")

class SpatialExporter:
    """
    Service d'exportation et de conversion spatio-temporelle :
    - GeoJSON FeatureCollection (SIG web, Leaflet, Mapbox, QGIS)
    - NetCDF4 / Xarray (modélisation climatique, archives scientifiques)
    - Séries temporelles tabulaires (CSV / JSON)
    """

    @staticmethod
    def to_geojson_grid(
        lats: np.ndarray,
        lons: np.ndarray,
        values: np.ndarray,
        variable_name: str = "total_precipitation",
        horizon_hours: int = 24,
        alert_threshold: float = 10.0
    ) -> Dict[str, Any]:
        """
        Convertit une grille régulière 2D (lat/lon) en GeoJSON FeatureCollection.
        """
        features = []
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                val = float(values[i, j])
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(float(lon), 4), round(float(lat), 4)]
                    },
                    "properties": {
                        "latitude": round(float(lat), 4),
                        "longitude": round(float(lon), 4),
                        variable_name: round(val, 2),
                        "forecast_horizon_hours": horizon_hours,
                        "alert": bool(val >= alert_threshold)
                    }
                })

        return {
            "type": "FeatureCollection",
            "features": features
        }

    @staticmethod
    def export_to_netcdf(
        lats: np.ndarray,
        lons: np.ndarray,
        times: List[str],
        data_dict: Dict[str, np.ndarray],
        output_filepath: str
    ) -> Optional[str]:
        """
        Exporte les données de prévision multidimensionnelles vers un fichier NetCDF4 via Xarray.
        """
        try:
            import xarray as xr
            
            coords = {
                "latitude": lats,
                "longitude": lons,
                "time": times
            }
            
            data_vars = {}
            for var_name, array in data_dict.items():
                data_vars[var_name] = (["latitude", "longitude", "time"], array)

            ds = xr.Dataset(data_vars=data_vars, coords=coords)
            ds.attrs["title"] = "Tabiria-Nvua Engine Climate & Extreme Weather Forecast"
            ds.attrs["source"] = "NVIDIA Earth2Studio & GeoCongo AI Assimilator"
            ds.attrs["institution"] = "GeoCongo AI"
            
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            ds.to_netcdf(output_filepath)
            logger.info(f"Fichier NetCDF généré avec succès: {output_filepath}")
            return output_filepath
        except Exception as e:
            logger.error(f"Erreur lors de l'exportation NetCDF: {e}")
            return None

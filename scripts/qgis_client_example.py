# Script d'intégration pour QGIS (tabiria_nvua_qgis_client.py)
# Ce script peut être exécuté dans la console Python de QGIS pour interroger
# l'API Tabiria-Nvua Engine et charger la couche GeoJSON des prévisions de précipitations.

import json
import urllib.request
import urllib.error
try:
    from qgis.core import QgsVectorLayer, QgsProject, QgsMessageLog, Qgis
    IN_QGIS = True
except ImportError:
    IN_QGIS = False

API_URL = "http://127.0.0.1:8000/api/v1/forecast/bbox"
API_KEY = "geocongo_key_master_2026"

def load_vula_forecast_layer_into_qgis():
    payload = {
        "bbox": [28.5, -2.5, 30.0, -1.0],
        "variables": ["total_precipitation"],
        "forecast_horizon_hours": 24,
        "output_format": "geojson",
        "model_name": "FourCastNet"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            geojson_data = json.loads(response_body)
            
            # Écriture temporaire du GeoJSON sur disque
            temp_geojson_path = "/tmp/tabiria_nvua_forecast_layer.geojson"
            with open(temp_geojson_path, "w", encoding="utf-8") as f:
                json.dump(geojson_data, f, indent=2)
                
            print(f"Succès : Fichier GeoJSON sauvegardé dans {temp_geojson_path}")
            print(f"Nombre d'entités reçues : {len(geojson_data.get('features', []))}")

            # Chargement de la couche vecteur dans QGIS si exécuté depuis QGIS
            if IN_QGIS:
                layer_name = "Tabiria-Nvua Engine - Précipitations (24h)"
                vlayer = QgsVectorLayer(temp_geojson_path, layer_name, "ogr")
                
                if vlayer.isValid():
                    QgsProject.instance().addMapLayer(vlayer)
                    QgsMessageLog.logMessage(f"Couche {layer_name} ajoutée avec succès dans QGIS.", "TabiriaNvua", Qgis.Info)
                    print(f"Succès : Couche '{layer_name}' chargée dans QGIS !")
                else:
                    print("Erreur : La couche GeoJSON générée n'est pas valide dans QGIS.")
            else:
                print("Note : Exécution hors de QGIS. Pour visualiser sur la carte, exécutez ce script dans la console Python de QGIS.")
                
    except urllib.error.URLError as e:
        print(f"Erreur de connexion à l'API Tabiria-Nvua Engine : {e.reason}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    load_vula_forecast_layer_into_qgis()

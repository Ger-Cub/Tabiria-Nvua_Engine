import json
import httpx

API_URL = "http://127.0.0.1:8000/api/v1"
API_KEY = "geocongo_key_master_2026"
HEADERS = {"X-API-Key": API_KEY}

def test_health():
    print("\n--- 1. Test Health ---")
    response = httpx.get(f"{API_URL}/health", headers=HEADERS)
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))

def test_models():
    print("\n--- 2. Test Models Registry ---")
    response = httpx.get(f"{API_URL}/models", headers=HEADERS)
    print("Status:", response.status_code)
    print(f"Modèles disponibles ({len(response.json())}):", [m["name"] for m in response.json()])

def test_station_ingest():
    print("\n--- 3. Test Station Ingest ---")
    payload = {
        "station_id": "STATION-GOMA-01",
        "secret_key": "vula_station_token_xxx",
        "timestamp": "2026-10-04T12:00:00Z",
        "location": {"latitude": -1.6585, "longitude": 29.2230, "elevation_m": 1530},
        "metrics": {
            "temperature_c": 24.5,
            "humidity_pct": 82.0,
            "pressure_hpa": 860.0,
            "precipitation_mm_last_hour": 14.2,
            "wind_speed_ms": 5.4,
            "wind_direction_deg": 180
        }
    }
    response = httpx.post(f"{API_URL}/stations/ingest", json=payload)
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))

def test_list_stations():
    print("\n--- 4. Test List Stations ---")
    response = httpx.get(f"{API_URL}/stations", headers=HEADERS)
    print("Status:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))

def test_point_forecast():
    print("\n--- 5. Test Point Forecast (avec assimilation locale) ---")
    payload = {
        "latitude": -1.6585,
        "longitude": 29.2230,
        "variables": ["total_precipitation", "temperature_2m", "wind_u10m", "wind_v10m"],
        "forecast_horizon_hours": 24,
        "use_local_station_correction": True,
        "model_name": "FourCastNet"
    }
    response = httpx.post(f"{API_URL}/forecast/point", json=payload, headers=HEADERS)
    print("Status:", response.status_code)
    data = response.json()
    print("Modèle utilisé:", data.get("model_used"))
    print("Correction station appliquée:", data.get("station_correction_applied"))
    print("Alertes détectées:", data.get("summary_alerts"))
    print("Nombre de pas de prévision:", len(data.get("steps", [])))

def test_bbox_forecast():
    print("\n--- 6. Test BBox Forecast (GeoJSON) ---")
    payload = {
        "bbox": [28.5, -2.5, 30.0, -1.0],
        "variables": ["total_precipitation"],
        "forecast_horizon_hours": 24,
        "output_format": "geojson",
        "model_name": "FourCastNet"
    }
    response = httpx.post(f"{API_URL}/forecast/bbox", json=payload, headers=HEADERS)
    print("Status:", response.status_code)
    data = response.json()
    print("Type:", data.get("type"))
    print("Nombre d'entités GeoJSON:", len(data.get("features", [])))

if __name__ == "__main__":
    print("=== Suite de Tests d'Intégration Client - Tabiria-Nvua Engine ===")
    try:
        test_health()
        test_models()
        test_station_ingest()
        test_list_stations()
        test_point_forecast()
        test_bbox_forecast()
    except Exception as e:
        print("\n[!] Erreur lors des tests (le serveur FastAPI est-il démarré ?):", e)

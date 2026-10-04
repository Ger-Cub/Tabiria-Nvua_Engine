import pytest
from httpx import AsyncClient

API_KEY = "geocongo_key_master_2026"
HEADERS = {"X-API-Key": API_KEY}

@pytest.mark.asyncio
async def test_station_ingest_invalid_secret(async_client: AsyncClient):
    payload = {
        "station_id": "STATION-GOMA-01",
        "secret_key": "wrong_key",
        "timestamp": "2026-10-04T12:00:00Z",
        "location": {"latitude": -1.6585, "longitude": 29.2230},
        "metrics": {"temperature_c": 24.0}
    }
    response = await async_client.post("/api/v1/stations/ingest", json=payload)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_station_ingest_aberrant_temp_rejected(async_client: AsyncClient):
    payload = {
        "station_id": "STATION-GOMA-01",
        "secret_key": "vula_station_token_xxx",
        "timestamp": "2026-10-04T12:00:00Z",
        "location": {"latitude": -1.6585, "longitude": 29.2230},
        "metrics": {"temperature_c": 95.0}  # Température aberrante (>60°C)
    }
    response = await async_client.post("/api/v1/stations/ingest", json=payload)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_station_ingest_and_list_success(async_client: AsyncClient):
    payload = {
        "station_id": "STATION-KIBALI-01",
        "secret_key": "vula_station_token_xxx",
        "timestamp": "2026-10-04T12:00:00Z",
        "location": {"latitude": 3.12, "longitude": 29.58, "elevation_m": 850.0},
        "metrics": {
            "temperature_c": 28.5,
            "humidity_pct": 75.0,
            "pressure_hpa": 980.0,
            "precipitation_mm_last_hour": 16.5,
            "precipitation_intensity_mm_h": 16.5,
            "wind_speed_ms": 7.2,
            "wind_direction_deg": 90.0
        }
    }
    response = await async_client.post("/api/v1/stations/ingest", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["station_id"] == "STATION-KIBALI-01"
    assert data["quality_flags"]["temperature_qc"] == "PASS"

    # Vérification que la station apparaît dans la liste des stations
    list_resp = await async_client.get("/api/v1/stations", headers=HEADERS)
    assert list_resp.status_code == 200
    stations = list_resp.json()
    station_ids = [s["station_id"] for s in stations]
    assert "STATION-KIBALI-01" in station_ids

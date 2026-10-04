import pytest
from httpx import AsyncClient

API_KEY = "geocongo_key_master_2026"
HEADERS = {"X-API-Key": API_KEY}

@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "cuda_available" in data
    assert "active_models" in data

@pytest.mark.asyncio
async def test_models_registry_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 4
    model_names = [m["name"] for m in models]
    assert "FourCastNet" in model_names
    assert "GraphCast" in model_names

@pytest.mark.asyncio
async def test_point_forecast_unauthorized(async_client: AsyncClient):
    payload = {
        "latitude": -1.6585,
        "longitude": 29.2230,
        "variables": ["total_precipitation"],
        "forecast_horizon_hours": 24
    }
    response = await async_client.post("/api/v1/forecast/point", json=payload)
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_point_forecast_success(async_client: AsyncClient):
    payload = {
        "latitude": -1.6585,
        "longitude": 29.2230,
        "variables": ["total_precipitation", "temperature_2m"],
        "forecast_horizon_hours": 24,
        "use_local_station_correction": True,
        "model_name": "FourCastNet"
    }
    response = await async_client.post("/api/v1/forecast/point", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == -1.6585
    assert data["longitude"] == 29.2230
    assert len(data["steps"]) > 0
    assert "total_precipitation" in data["steps"][0]["values"]

@pytest.mark.asyncio
async def test_bbox_forecast_geojson(async_client: AsyncClient):
    payload = {
        "bbox": [28.5, -2.5, 30.0, -1.0],
        "variables": ["total_precipitation"],
        "forecast_horizon_hours": 24,
        "output_format": "geojson"
    }
    response = await async_client.post("/api/v1/forecast/bbox", json=payload, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert "coordinates" in data["features"][0]["geometry"]

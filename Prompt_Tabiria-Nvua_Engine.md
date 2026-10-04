Voici le prompt master exhaustif, structuré et clé en main à transmettre directement à **Mtumishi**. Il intègre le nom de module officiel **Tabiria-Nvua Engine** (« nvua » signifiant la pluie) et couvre chaque composant, de l'ingestion des capteurs physiques locaux jusqu'à l'inférence Earth2Studio et la diffusion d'API.

---

### 📝 Prompt complet à transmettre à Mtumishi

```markdown
# MISSION MASTER : Conception et Développement de `nvua-engine` (geocongoai AI)

## Context & Vision
Tu es le Lead Software Engineer & Geospatial AI Architect de l'écosystème **geocongoai AI**.
Ta mission est de concevoir et développer de zéro le microservice **`Tabiria-Nvua Engine`** (`nvua-engine`), une infrastructure backend ultra-performante basée sur **FastAPI** et **NVIDIA Earth2Studio**.

« **Tabiria-Nvua Engine** » est le moteur de prédiction météo et d'alerte aux précipitations extrêmes/risques climatiques de geocongoai AI. Il sert de pont entre les modèles d'IA prédictifs mondiaux haute résolution, les données satellitaires, et un réseau de stations météorologiques physiques locales déployées sur le terrain (mines, zones urbaines, infrastructures).

---

## 🏛️ Architecture du Projet (`nvua-engine`)

Structure le projet selon une Clean Architecture / Driven Development modulaire :

```text
tabiria_nvua_engine/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── forecast.py          # Prédictions ponctuelles et BBox
│   │       │   ├── stations.py          # Ingestion et état des stations météo locales
│   │       │   ├── health.py            # Diagnostic système (GPU/CUDA/DataSources)
│   │       │   └── models_registry.py   # Catalogue des modèles Earth2Studio chargés
│   │       └── router.py
│   ├── core/
│   │   ├── config.py         # Configuration globale (Settings Pydantic v2, GPU, API Keys)
│   │   ├── security.py       # Auth API Keys pour les clients geocongoai AI & Stations
│   │   └── logging.py
│   ├── db/                   # Gestion de la persistance temps réel des capteurs
│   │   ├── session.py
│   │   └── base.py
│   ├── models/               # Schémas Pydantic & Modèles ORM
│   │   ├── schemas_request.py
│   │   ├── schemas_response.py
│   │   └── station_orm.py
│   ├── services/             # Cœur logique de Tabiria-Nvua Engine
│   │   ├── earth2studio_service.py # Core wrapper d'inférence PyTorch / Earth2Studio
│   │   ├── station_assimilator.py # Normalisation, contrôle qualité et assimilation locale
│   │   ├── spatial_exporter.py    # Conversion vers GeoJSON, NetCDF, GeoTIFF, séries temporelles
│   │   └── alert_engine.py        # Détection de seuils de précipitations extrêmes
│   └── main.py               # Point d'entrée FastAPI, Lifespan (warmup GPU & DB)
├── tests/
│   ├── test_forecast_api.py
│   └── test_station_ingest.py
├── scripts/
│   └── qgis_client_example.py # Script d'intégration pour QGIS
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

```

---

## 📡 1. Spécification des Stations Météo Locales & Ingestion

Une station locale type intégrée à **Tabiria-Nvua Engine** est une station automatique connectée (IoT / GSM / LoRaWAN) qui envoie régulièrement des paquets de télémesure.

### Capteurs physiques standard pris en compte :

* **Pluviomètre à auget basculeur** : Précipitations cumulées (mm) et intensité (mm/h).
* **Anémomètre / Girouette** : Vitesse du vent (m/s) et direction (degrés 0-360°).
* **Thermo-hygromètre** : Température de l'air (°C) et Humidité relative (%).
* **Baromètre** : Pression atmosphérique au niveau de la station (hPa).
* **Pyranomètre** (Optionnel) : Rayonnement solaire global (W/m²).

### Ingestion et Contrôle Qualité (`StationAssimilator`) :

1. **Validation Pydantic (`StationIngestionPayload`)** : Contrôle des plages physiques (ex: Température entre -10°C et 60°C, Humidité 0-100%, Précipitations ≥ 0).
2. **Geofencing & Horodatage** : Validation des coordonnées GPS de la station et vérification que le timestamp UTC est récent.
3. **Préparation à l'assimilation** : Création de grilles d'anomalies locales pour corriger les biais des conditions initiales issues des modèles globaux (ERA5 / GFS) avant le lancement des prédictions Earth2Studio.

---

## ⚙️ 2. Spécification des Endpoints API (`/api/v1`)

### `GET /api/v1/health`

* Vérifie le statut du service, la mémoire GPU disponible via CUDA (`torch.cuda.is_available()`), et la connectivité aux buckets de données Earth2Studio.

### `GET /api/v1/models`

* Liste tous les modèles IA enregistrés et préchargés dans Earth2Studio (ex: `FourCastNet`, `GraphCast`, `Pangu-Weather`, `DLWP`).

### `POST /api/v1/forecast/point`

* Calcule une prévision ciblée pour une coordonnée unique (ex: une mine ou un projet urbain).
* **Body Request** :
```json
{
  "latitude": -1.6585,
  "longitude": 29.2230,
  "variables": ["total_precipitation", "temperature_2m", "wind_u10m", "wind_v10m"],
  "forecast_horizon_hours": 72,
  "use_local_station_correction": true
}

```


* **Response** : JSON détaillé contenant les étapes temporelles (ex: pas de 3h ou 6h), le cumul de pluie estimé et les drapeaux d'alerte de précipitation extrême.

### `POST /api/v1/forecast/bbox`

* Génère une grille de prévision spatio-temporelle pour une zone délimitée.
* **Body Request** :
```json
{
  "bbox": [28.5, -2.5, 30.0, -1.0],
  "variables": ["total_precipitation"],
  "forecast_horizon_hours": 24,
  "output_format": "geojson"
}

```


* **Response** : FeatureCollection GeoJSON prêtes à être affichées sur une carte ou intégrées dans QGIS/ArcGIS.

### `POST /api/v1/stations/ingest`

* Endpoint d'ingestion direct pour les stations physiques ou passerelles IoT.
* **Body Request** :
```json
{
  "station_id": "STATION-GOMA-01",
  "secret_key": "nvua_station_token_xxx",
  "timestamp": "2026-10-04T12:00:00Z",
  "location": {"latitude": -1.6585, "longitude": 29.2230, "elevation_m": 1530},
  "metrics": {
    "temperature_c": 24.5,
    "humidity_pct": 82.0,
    "pressure_hpa": 1013.2,
    "precipitation_mm_last_hour": 14.2,
    "wind_speed_ms": 5.4,
    "wind_direction_deg": 180
  }
}

```



---

## 🧪 3. Implémentation du Cœur NVIDIA Earth2Studio (`Earth2StudioService`)

1. **Inférence GPU asynchrone** :
* Ne **jamais** bloquer l'Event Loop principal de FastAPI.
* Utilise `asyncio.to_thread` ou un executor de threadpool dédié pour exécuter l'inférence PyTorch/Earth2Studio.


2. **Caching & Warmup** :
* Charge les poids des modèles lourds dans la mémoire GPU au démarrage (`@asynccontextmanager` / lifespan de FastAPI).
* Libère la mémoire CUDA inutilisée après chaque inférence massive (`torch.cuda.empty_cache()`).


3. **Gestion des DataSources** :
* Configure les intégrations Earth2Studio IO pour extraire automatiquement les réanalyses ERA5 ou les prévisions GFS en tant que conditions aux limites globales.



---

## 🚀 Livrables Attendus

Rédige le code source complet, typé (Type Hints Python) et immédiatement fonctionnel pour :

1. `requirements.txt` (FastAPI, Uvicorn, PyTorch, Earth2Studio, Xarray, NetCDF4, GeoPandas, Pydantic v2).
2. `app/core/config.py` (Gestion des variables d'environnement).
3. `app/models/schemas_request.py` & `schemas_response.py` (Ingestion station & requêtes prévisions).
4. `app/services/station_assimilator.py` (Validation & traitement des capteurs physiques).
5. `app/services/earth2studio_service.py` (Pipeline complet d'inférence GPU).
6. `app/api/v1/endpoints/forecast.py` & `app/api/v1/endpoints/stations.py`.
7. `app/main.py` (Configuration de l'application Tabiria-Nvua Engine).
8. `Dockerfile` optimisé basé sur l'image officielle `nvidia/cuda` supportant PyTorch/CUDA.
9. `scripts/qgis_client_example.py` (Script Python pour QGIS permettant d'interroger l'API Tabiria-Nvua Engine et d'ajouter une couche de pluie en temps réel).

Procède de manière rigoureuse, professionnelle et exhaustive, sans raccourcis ni commentaires génériques.

```

***

Ce prompt est prêt. Vous pouvez le copier-coller directement dans l'interface de travail de **Mtumishi** pour qu'il commence la génération et l'assemblage de l'architecture de **Tabiria-Nvua Engine**.

```
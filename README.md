# 🌧️ Tabiria-Nvua Engine (`nvua-engine`)
> **GeoCongo AI** — Moteur de Prévision Météorologique Haute Résolution, d'Assimilation IoT et d'Alerte aux Risques Climatiques Extrêmes.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org)
[![NVIDIA Earth2Studio](https://img.shields.io/badge/NVIDIA-Earth2Studio-76B900.svg?logo=nvidia&logoColor=white)](https://github.com/NVIDIA/earth2studio)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

---

## 🌍 Présentation

**Tabiria-Nvua Engine** (« *Nvua* » signifiant *la pluie*) est le microservice d'intelligence météorologique développé pour l'écosystème **GeoCongo AI**. Il combine :
1. **L'IA Météorologique Mondiale** : Inférence haute performance via **NVIDIA Earth2Studio** (modèles *FourCastNet*, *GraphCast*, *Pangu-Weather*, *DLWP*).
2. **L'Assimilation Temps Réel** : Ingestion directe et contrôle qualité (QC) de stations météorologiques physiques connectées (GSM, LoRaWAN, IoT) sur le terrain (mines, concessions agricoles, centres urbains de RDC).
3. **Le Moteur d'Alerte Précipitations Extrêmes** : Détection précoce des risques de crues éclairs, glissements de terrain et tempêtes convectives dans le Bassin du Congo et la région des Grands Lacs.
4. **L'Interopérabilité SIG** : Export direct en GeoJSON, NetCDF4 et rasters pour QGIS, ArcGIS et plateformes web spatiales.

---

## 🏛️ Architecture du Projet

```text
Tabiria-Nvua_Engine/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── forecast.py          # Prédictions ponctuelles et BBox avec assimilation
│   │       │   ├── stations.py          # Ingestion IoT, QC et consultation d'état
│   │       │   ├── health.py            # Diagnostic système (GPU/CUDA/BDD/DataSources)
│   │       │   └── models_registry.py   # Catalogue des modèles Earth2Studio chargés
│   │       └── router.py                # Agrégation des routes API v1
│   ├── core/
│   │   ├── config.py                    # Paramètres globaux (Pydantic v2 Settings)
│   │   ├── security.py                  # Authentification API Keys & Secret Keys IoT
│   │   └── logging.py                   # Configuration standardisée du logging
│   ├── db/
│   │   ├── session.py                   # Moteur async SQLAlchemy & session manager
│   │   └── base.py                      # DeclarativeBase SQLAlchemy 2.0
│   ├── models/
│   │   ├── schemas_request.py           # Schémas de validation Pydantic v2 (Entrées)
│   │   ├── schemas_response.py          # Schémas de réponse typés (Sorties)
│   │   └── station_orm.py               # Modèles ORM (WeatherStation & StationTelemetry)
│   ├── services/
│   │   ├── earth2studio_service.py      # Wrapper d'inférence asynchrone GPU Earth2Studio
│   │   ├── station_assimilator.py       # Contrôle qualité (QC) et correction spatiale IDW
│   │   ├── spatial_exporter.py          # Export multi-formats (GeoJSON, NetCDF4)
│   │   └── alert_engine.py              # Moteur de seuils d'alertes aux risques extrêmes
│   └── main.py                          # Point d'entrée FastAPI & Lifespan
├── tests/
│   ├── conftest.py                      # Fixtures AsyncClient et BDD de test
│   ├── test_forecast_api.py             # Tests des prédictions et diagnostics
│   └── test_station_ingest.py           # Tests de l'ingestion IoT et contrôles qualité
├── scripts/
│   ├── qgis_client_example.py           # Client Python pour intégration directe dans QGIS
│   └── test_client.py                   # Suite de tests d'intégration API
├── Dockerfile                           # Conteneurisation NVIDIA CUDA 12.2 Runtime
├── docker-compose.yml                   # Stack complète (Nvua-Engine + TimescaleDB/PostGIS)
├── requirements.txt                     # Dépendances Python
└── README.md
```

---

## ⚡ Démarrage Rapide

### 1. Installation locale (Environnement Virtuel)

```bash
# Cloner le dépôt
git clone https://github.com/Ger-Cub/Tabiria-Nvua_Engine.git
cd Tabiria-Nvua_Engine

# Créer et activer l'environnement virtuel Python 3.11+
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
```

### 2. Lancer le microservice

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

L'API interactive Swagger UI sera accessible à l'adresse : **http://localhost:8000/docs**

---

## 🐳 Déploiement avec Docker & NVIDIA GPU

Pour exécuter le microservice avec accélération matérielle NVIDIA CUDA et base de données TimescaleDB/PostGIS :

```bash
# Démarrer l'ensemble des services
docker compose up -d --build

# Consulter les journaux
docker compose logs -f nvua-engine
```

---

## 📡 Endpoints API Principaux (`/api/v1`)

| Méthode | Route | Description | Auth Requise |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Diagnostic GPU/CUDA, mémoire allouée et état BDD | Non |
| `GET` | `/api/v1/models` | Catalogue des modèles d'IA chargés (*FourCastNet*, *GraphCast*, etc.) | Non |
| `POST` | `/api/v1/stations/ingest` | Ingestion directe d'une trame de télémesure IoT | `secret_key` |
| `GET` | `/api/v1/stations` | Liste des stations enregistrées et de leur dernier état | `X-API-Key` |
| `POST` | `/api/v1/forecast/point` | Prévision ponctuelle haute résolution avec assimilation locale | `X-API-Key` |
| `POST` | `/api/v1/forecast/bbox` | Grille de prévision spatiale au format GeoJSON FeatureCollection | `X-API-Key` |

---

## 🗺️ Intégration QGIS

Un script prêt à l'emploi est disponible dans `scripts/qgis_client_example.py` :
1. Ouvrez **QGIS**.
2. Allez dans le menu **Extensions** > **Console Python**.
3. Ouvrez et exécutez le script [scripts/qgis_client_example.py](scripts/qgis_client_example.py).
4. La couche de prévision de pluie (24h) est automatiquement ajoutée sur la carte avec ses métadonnées.

---

## 🧪 Exécution des Tests

```bash
pytest -v
```

---

## 🔒 Sécurité & Variables d'Environnement

* `SECRET_KEY` : Clé de chiffrement interne.
* `STATION_SECRET_KEY` : Jeton d'autorisation pour les passerelles de stations physiques.
* `VALID_API_KEYS` : Liste des clés clientes autorisées pour les requêtes de prévisions.
* `ALERT_PRECIP_INTENSITY_MM_H` : Seuil d'alerte pour pluie horaire intense (défaut : 10.0 mm/h).
* `ALERT_PRECIP_24H_MM` : Seuil d'alerte pour cumul journalier critique (défaut : 50.0 mm/24h).

---

## 🏢 Licence & Propriété
Développé par l'équipe **GeoCongo AI** — Tous droits réservés.

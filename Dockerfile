# Multi-stage Dockerfile pour Tabiria-Nvua Engine (nvua-engine)
# Base officielle NVIDIA CUDA Runtime avec support PyTorch GPU et fallback CPU

FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Éviter les invites interactives pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Installation de Python 3.11, pip et dépendances système géospatiales (GDAL, GEOS, NetCDF)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libnetcdf-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Configurer python3.11 comme binaire python par défaut
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

WORKDIR /app

# Installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY app/ ./app/
COPY scripts/ ./scripts/

# Création des dossiers de cache et de données
RUN mkdir -p /app/cache/earth2studio /app/models_cache

# Exposition du port FastAPI
EXPOSE 8000

# Commande de démarrage avec Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Kafka ETL POC - Installation Guide

## Prérequis

- Docker Desktop (inclut Docker + Docker Compose)
- Python 3.8+
- pip

## Installation rapide

```powershell
cd project
.\start.ps1
```

Sans ouvrir 5 terminaux :

```powershell
.\start.ps1 -Headless
```

## Installation manuelle

### 1) Démarrer l'infrastructure
```powershell
docker-compose up -d
```

### 2) Installer les dépendances
```powershell
python -m pip install -r requirements.txt
```

### 3) Initialiser la base et les topics
```powershell
python init_db.py
python create_topics.py
```

### 4) Lancer les composants
```powershell
python producer/producer.py
python worker_python/worker.py
python worker_python/order_validator.py
python worker_python/order_fact_builder.py
python kpi_orders.py
```

### 5) Attendre les données et tester
```powershell
python wait_for_data.py
python full_test.py
```

## Dépendances

- kafka-python-ng 2.2.2
- psycopg[binary] 3.3.2

## Notes

- Les scripts sont compatibles Python 3.8+
- Compatible Windows / Mac / Linux

Pour les détails d’exécution, voir [RUN.md](RUN.md)

# GUIDE DE DÉMARRAGE RAPIDE

## Prérequis

```powershell
# Installer Docker Desktop
# (inclut Docker + Docker Compose)

# Vérifier l'installation
docker --version
docker-compose --version
```

## Étape 1: Lancer tout en une commande

```powershell
cd "C:\Users\Asseu\Desktop\Projet Data\project"
\.\start.ps1
```

Sans ouvrir 5 terminaux :

```powershell
\.\start.ps1 -Headless
```

Ce script démarre l'infrastructure, installe les dépendances, lance les workers, attend les données et exécute le test complet.

En mode headless, les logs sont dans .\logs\*.log.

## Étape 2: Démarrage manuel (optionnel)

```powershell
cd "C:\Users\Asseu\Desktop\Projet Data\project"
docker-compose up -d
python -m pip install -r requirements.txt
python init_db.py
python create_topics.py
```

## Étape 3: Lancer les workers (5 terminaux)

### Terminal 1: Producer (source)
```powershell
python producer/producer.py
```

### Terminal 2: UserETL Worker
```powershell
python worker_python/worker.py
```

### Terminal 3: Order Validator
```powershell
python worker_python/order_validator.py
```

### Terminal 4: Fact Builder (DW)
```powershell
python worker_python/order_fact_builder.py
```

### Terminal 5: Monitor
```powershell
python kpi_orders.py
```

## Résultats attendus

- 100 événements générés
- users insérés dans PostgreSQL
- fact_orders peuplée
- KPIs calculés

## Dépannage

### Kafka ne démarre pas
```powershell
# Vérifier Zookeeper d'abord
docker logs project-zookeeper-1

# Puis Kafka
docker logs project-kafka-1
```

### PostgreSQL connection refused
```powershell
# Vérifier que Postgres tourne
docker ps | grep postgres

# Check password
# User: etl_user
# Pass: etl_password
# DB: etl_db
```

### Pas de messages dans Kafka
```powershell
docker exec project-kafka-1 kafka-topics --bootstrap-server kafka:9092 --list
```

## Structure de fichiers

```
project/
├── docker-compose.yml          # Infrastructure
├── producer/
│   └── producer.py             # Source events
├── worker_python/
│   ├── worker.py               # User ETL
│   ├── order_validator.py      # Order validation
│   └── order_fact_builder.py   # Data Warehouse
├── db/
│   └── schema.sql              # Schéma complet
├── kpi_orders.py               # Dashboard KPI
└── DOCUMENTATION_COMPLETE.md   # Architecture
```

## Documentation

- **DOCUMENTATION_COMPLETE.md**: Architecture, ESB, Talend
- **ARCHITECTURE.md**: Patterns DW et KPI
- **README.md**: Quick reference

## Checklist de validation

- [ ] Docker services UP
- [ ] Kafka topics created
- [ ] PostgreSQL connected
- [ ] 100 events générés
- [ ] Users table peuplée
- [ ] fact_orders peuplée
- [ ] KPIs calculés

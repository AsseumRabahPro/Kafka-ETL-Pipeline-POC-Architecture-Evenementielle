# KAFKA ETL POC - MANIFEST D'ENVOI

## Contenu du projet

### Infrastructure
```
docker-compose.yml              ← Kafka + PostgreSQL + Zookeeper
db/schema.sql                   ← Schéma complet + vues
```

### Code source

#### Producer
```
producer/
└── producer.py                 ← Génère 100 événements
```

#### Workers
```
worker_python/
├── worker.py                   ← ETL utilisateurs
├── order_validator.py          ← Validation métier
└── order_fact_builder.py       ← Data Warehouse
```

#### Scripts de pilotage
```
start.ps1                       ← Commande unique (infra + run + test)
init_db.py                      ← Initialisation base
create_topics.py                ← Création topics Kafka
wait_for_data.py                ← Attente ingestion
full_test.py                    ← Test end-to-end
kpi_orders.py                   ← Dashboard KPI
```

### Documentation (ordre conseillé)
```
README.md
INSTALL.md
QUICKSTART.md
RUN.md
DOCUMENTATION_COMPLETE.md
ARCHITECTURE.md
TROUBLESHOOTING.md
```

### Configuration
```
requirements.txt                ← kafka-python-ng + psycopg
.gitignore                      ← Fichiers Git à ignorer
```

---

## Technologies

- Kafka 7.5.0
- PostgreSQL 15
- Python 3.8+
- Docker Compose
- kafka-python-ng 2.2.2
- psycopg[binary] 3.3.2

---

## Pour démarrer

Commande unique :
```powershell
.\start.ps1
```

---

Date: 2026-02-17
Status: LIVRABLE
Version: 1.0

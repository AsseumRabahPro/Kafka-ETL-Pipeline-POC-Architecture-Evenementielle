# Kafka ETL POC - Proof of Concept

![CI](https://github.com/asseumrabahpro-cmd/Mini-projet-Dev-Data-ASSEUM/actions/workflows/ci.yml/badge.svg)
![Integration Tests](https://github.com/asseumrabahpro-cmd/Mini-projet-Dev-Data-ASSEUM/actions/workflows/integration.yml/badge.svg)

Une architecture événementielle complète démontrant un ETL temps réel avec Kafka, PostgreSQL et des workers Python spécialisés.

## Vue d'ensemble rapide

```
Producer (100 events)
    ↓
Kafka Topics
├─→ UserETLWorker → PostgreSQL (users)
├─→ OrderValidator → Kafka (validated/rejected)
└─→ Fact Builder → PostgreSQL (fact_orders)
    ↓
KPI Dashboard → Analytics
```

## Démarrage rapide (1 commande)

```powershell
.\start.ps1
```

Sans ouvrir 5 terminaux :

```powershell
.\start.ps1 -Headless
```

Ce script :
1) démarre Docker (Kafka, Zookeeper, PostgreSQL)
2) installe les dépendances Python
3) initialise la base
4) crée les topics Kafka
5) lance les workers + KPI
6) attend des données puis exécute le test complet

En mode headless, les logs sont dans .\logs\*.log.

## Démarrage manuel

Voir [RUN.md](RUN.md) pour les étapes détaillées.

## Résultats attendus

- 100 événements générés
- Users insérés dans PostgreSQL
- fact_orders peuplée
- KPIs calculés (orders, revenue, rejection rate)

## Structure

```
project/
├── docker-compose.yml
├── requirements.txt
├── start.ps1
├── init_db.py
├── create_topics.py
├── wait_for_data.py
├── full_test.py
├── db/
│   └── schema.sql
├── producer/
│   └── producer.py
├── worker_python/
│   ├── worker.py
│   ├── order_validator.py
│   └── order_fact_builder.py
├── kpi_orders.py
├── README.md
├── RUN.md
├── INSTALL.md
├── QUICKSTART.md
├── ARCHITECTURE.md
├── DOCUMENTATION_COMPLETE.md
├── TROUBLESHOOTING.md
└── MANIFEST.md
```

## Documentation

- [INSTALL.md](INSTALL.md) - Installation
- [QUICKSTART.md](QUICKSTART.md) - Démarrage rapide
- [RUN.md](RUN.md) - Exécution détaillée
- [DOCUMENTATION_COMPLETE.md](DOCUMENTATION_COMPLETE.md) - Architecture complète
- [ARCHITECTURE.md](ARCHITECTURE.md) - Patterns DW et KPI
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Dépannage

## Stack

- Kafka 7.5.0
- PostgreSQL 15
- Python 3.8+
- Docker Compose
- kafka-python-ng 2.2.2
- psycopg[binary] 3.3.2

---

Prêt à démarrer : exécute [start.ps1](start.ps1)

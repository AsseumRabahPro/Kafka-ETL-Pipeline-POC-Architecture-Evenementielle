# 🏢 Data Warehouse Architecture

## Pattern: Events → Fact Table → BI/Analytics

```
┌─────────────────────────────────────────────────────────────────┐
│                      KAFKA (Streaming Events)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  order.created → [OrderValidator] → order.validated              │
│                                  → order.rejected                │
│                                                                   │
│  [OrderFactBuilder] ← order.validated, order.rejected            │
│         │                                                        │
│         ↓                                                        │
│    ┌─────────────────────────────────────────┐                  │
│    │   POSTGRESQL (Data Warehouse)           │                  │
│    ├─────────────────────────────────────────┤                  │
│    │                                          │                  │
│    │  📊 fact_orders (Fact Table)            │                  │
│    │  ├─ order_id (PK)                       │                  │
│    │  ├─ user_id                             │                  │
│    │  ├─ amount                              │                  │
│    │  ├─ items                               │                  │
│    │  ├─ status (validated/rejected)         │                  │
│    │  ├─ rejection_reason                    │                  │
│    │  ├─ order_date                          │                  │
│    │  └─ processed_at                        │                  │
│    │                                          │                  │
│    │  👥 users (Dimension Table)             │                  │
│    │  ├─ user_id (PK)                        │                  │
│    │  ├─ username                            │                  │
│    │  └─ email                               │                  │
│    └─────────────────────────────────────────┘                  │
│         │                                                        │
│         ↓                                                        │
│    ┌─────────────────────────────────────────┐                  │
│    │  📈 BI / Analytics / Reporting          │                  │
│    │  ├─ KPI Dashboard                       │                  │
│    │  ├─ Orders by Day                       │                  │
│    │  ├─ Revenue Analysis                    │                  │
│    │  ├─ Rejection Rate                      │                  │
│    │  └─ User Analytics                      │                  │
│    └─────────────────────────────────────────┘                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Pourquoi pas consommer directement depuis Kafka en BI?

### ❌ Anti-pattern (Direct Kafka → BI)
```
Kafka → Spark/Tableau → Reports
    ↑
    └─ Dépendance directe aux events
    └─ Pas de historique fiable
    └─ Pas d'agrégations pré-calculées
    └─ Query lente sur raw events
    └─ Risque de perte de données
```

### ✅ Pattern recommandé (Kafka → DW → BI)
```
Kafka → OrderFactBuilder → fact_orders → KPI Dashboard
    ↑                          ↑
    └─ Raw events            └─ Données nettoyées, agrégées
    └─ Transformation            └─ Persistance fiable
    └─ Validation                └─ Performance optimisée
```

## Avantages de cette architecture

### 1. **Séparation de la couche de traitement et BI**
- Kafka = traitement temps réel
- PostgreSQL = Data Warehouse
- BI tools = consomment la DW, pas Kafka

### 2. **Performance des queries BI**
- Indexation optimisée (`order_date`, `status`, `user_id`)
- Agrégations pré-calculées
- Pas de scan des millions d'events bruts

### 3. **Fiabilité et audit**
- Historique complet dans la DW
- Traçabilité des transformations
- Récupération facile en cas de problème

### 4. **Scalabilité indépendante**
```
Kafka ──────────┐
                ├─→ OrderFactBuilder (1 instance)
                ├─→ UserETLWorker (N instances)
                └─→ OrderValidator (N instances)
                       ↓
                  PostgreSQL (Data Warehouse)
                       ↓
                  Tableau/Superset (BI Tools)
```

## Table: fact_orders

```sql
CREATE TABLE fact_orders (
    id SERIAL PRIMARY KEY,
    order_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10, 2),
    items INTEGER,
    status VARCHAR(50),              -- 'validated' ou 'rejected'
    rejection_reason TEXT,            -- Raison du rejet si applicable
    order_date DATE,                  -- Pour partitioning/analytics
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
)
```

## KPIs disponibles

### 1. Nombre de commandes par jour
```sql
SELECT order_date, COUNT(*) as total_orders
FROM fact_orders
GROUP BY order_date
```

### 2. Montant total par jour
```sql
SELECT order_date, SUM(amount) as total_amount
FROM fact_orders
WHERE status = 'validated'
GROUP BY order_date
```

### 3. Taux de rejet
```sql
SELECT 
    order_date,
    100.0 * COUNT(CASE WHEN status='rejected' THEN 1 END) / COUNT(*) as rejection_rate
FROM fact_orders
GROUP BY order_date
```

## Workers impliqués

| Worker | Input | Output | Responsabilité |
|--------|-------|--------|-----------------|
| `producer.py` | Générateur | Kafka (3 topics) | Générer events |
| `worker.py` | user.created | PostgreSQL (users) | ETL utilisateurs |
| `order_validator.py` | order.created | Kafka (2 topics) | Valider commandes |
| `order_fact_builder.py` | validated/rejected | PostgreSQL (fact_orders) | Construire DW |

## Workflow complet

```
1. Producer génère 100 events → Kafka
   └─ order.created: 30 events

2. OrderValidator consomme order.created
   ├─→ Valide les règles métier
   ├─→ Publie 20x order.validated
   └─→ Publie 10x order.rejected

3. OrderFactBuilder consomme validated + rejected
   ├─→ Enrichit les données
   └─→ Insère dans fact_orders (30 lignes)

4. KPI Dashboard consulte fact_orders
   ├─→ Calcule KPIs
   ├─→ Génère rapports
   └─→ Alimente la BI
```

## Lancer l'architecture complète

```powershell
# Terminal 1: Producer (source)
python producer.py

# Terminal 2: User Worker (ETL → DB)
python worker.py

# Terminal 3: Order Validator (Business logic)
python order_validator.py

# Terminal 4: Fact Builder (DW → fact_orders)
python order_fact_builder.py

# Terminal 5: Check KPIs (BI layer)
python kpi_orders.py

# Terminal 6: Check Users
python check_db.py
```

## Résultat attendu

```
✅ 30 ordres dans fact_orders
✅ 20 validés, 10 rejetés
✅ KPI Dashboard montre:
   - Orders per day
   - Revenue analysis
   - Rejection rate
   - Trend analysis
```

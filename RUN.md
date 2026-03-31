# Running the Kafka ETL System

## Quick Start (Automated)

Run everything with a single command:

```powershell
.\start.ps1
```

Run without opening 5 terminals:

```powershell
.\start.ps1 -Headless
```

This script will:
1) start Docker services (Kafka, Zookeeper, PostgreSQL)
2) install Python dependencies
3) initialize the database schema
4) create Kafka topics
5) launch all 5 components in separate terminals
6) wait for data then run the end-to-end test

In headless mode, components run in background and logs are written to .\logs\*.log.

## Manual Start (Step by Step)

### Step 1: Start Infrastructure
```powershell
docker-compose up -d
```

### Step 2: Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Initialize Database
```powershell
python init_db.py
```

### Step 4: Create Kafka Topics
```powershell
python create_topics.py
```

### Step 5: Launch Components (5 separate terminals)

**Terminal 1 - Producer**
```powershell
python producer/producer.py
```

**Terminal 2 - User ETL Worker**
```powershell
python worker_python/worker.py
```

**Terminal 3 - Order Validator**
```powershell
python worker_python/order_validator.py
```

**Terminal 4 - Order Fact Builder**
```powershell
python worker_python/order_fact_builder.py
```

**Terminal 5 - KPI Dashboard**
```powershell
python kpi_orders.py
```

### Step 6: Wait for Data and Test
```powershell
python wait_for_data.py
python full_test.py
```

## Verifying Results

After components run, you'll see:
- Producer: 100 events sent
- Workers: processing confirmations for each event
- KPI Dashboard: 3 KPIs displayed (orders, revenue, rejection rate)

## Stopping Everything

### Stop Docker Services
```powershell
docker-compose down
```

### Stop Individual Components
Close each terminal window where components are running

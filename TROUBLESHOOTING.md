# GUIDE DE DÉPANNAGE

## Problème 1: ModuleNotFoundError

### Solution rapide
```powershell
python -m pip install -r requirements.txt
```

## Problème 2: Connexion PostgreSQL refusée

```powershell
docker ps | findstr postgres
```

Si nécessaire:
```powershell
docker-compose up -d
```

## Problème 3: Kafka indisponible

```powershell
docker ps | findstr kafka
docker logs project-kafka-1
```

Relancer si besoin:
```powershell
docker-compose down
docker-compose up -d
Start-Sleep -Seconds 30
```

## Problème 4: Docker non trouvé

- Vérifier que Docker Desktop est installé et lancé
- Télécharger: https://www.docker.com/products/docker-desktop

## Vérifications rapides

```powershell
docker-compose ps
python -c "import psycopg; psycopg.connect(host='localhost', dbname='etl_db', user='etl_user', password='etl_password').close(); print('PostgreSQL OK')"
python -c "from kafka import KafkaAdminClient; admin = KafkaAdminClient(bootstrap_servers=['localhost:9092']); print(f'Kafka OK - {len(admin.list_topics())} topics'); admin.close()"
```

## Setup complet (1 commande)

```powershell
.\start.ps1
```

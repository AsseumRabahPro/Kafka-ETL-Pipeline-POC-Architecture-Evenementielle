import json
import logging
import time
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import psycopg
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Kafka
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'user.created'
KAFKA_GROUP = 'user-consumer-group'

# Configuration PostgreSQL
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'etl_db'
DB_USER = 'etl_user'
DB_PASSWORD = 'etl_password'

class UserETLWorker:
    def __init__(self):
        """Initialiser le worker avec connexion DB"""
        self.db_conn = None
        self.consumer = None
        self.connect_db()
        self.init_table()
        self.init_consumer()
    
    def connect_db(self):
        """Connexion à PostgreSQL"""
        try:
            self.db_conn = psycopg.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("[OK] Connected to PostgreSQL")
        except psycopg.Error as e:
            logger.error(f"[ERROR] Database connection failed: {e}")
            raise
    
    def init_table(self):
        """Créer la table users si elle n'existe pas"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER UNIQUE NOT NULL,
                    username VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.db_conn.commit()
            cursor.close()
            logger.info("[OK] Users table ready")
        except psycopg.Error as e:
            logger.error(f"[ERROR] Table creation failed: {e}")
            self.db_conn.rollback()
            raise
    
    def init_consumer(self):
        """Initialiser le Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                group_id=KAFKA_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logger.info(f"[OK] Consumer initialized for topic: {KAFKA_TOPIC}")
        except KafkaError as e:
            logger.error(f"[ERROR] Consumer initialization failed: {e}")
            raise
    
    def transform_user_data(self, data):
        """
        Transformer les données utilisateur
        - Normaliser email (lowercase)
        - Normaliser nom (title case)
        """
        transformed = {
            'user_id': data.get('user_id'),
            'username': data.get('username', '').title() if data.get('username') else '',
            'email': data.get('email', '').lower() if data.get('email') else '',
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        }
        return transformed
    
    def insert_user(self, data):
        """Insérer un utilisateur dans la base de données"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, username, email, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    email = EXCLUDED.email,
                    inserted_at = CURRENT_TIMESTAMP
            """, (
                data['user_id'],
                data['username'],
                data['email'],
                data['timestamp']
            ))
            self.db_conn.commit()
            cursor.close()
            logger.info(f"[OK] User {data['user_id']} inserted: {data['username']} ({data['email']})")
        except psycopg.Error as e:
            logger.error(f"[ERROR] Insert failed: {e}")
            self.db_conn.rollback()
    
    def run(self):
        """Lancer le worker"""
        logger.info("[START] Starting User ETL Worker...")
        logger.info(f"[IN] Consuming from topic: {KAFKA_TOPIC}")

        try:
            while True:
                try:
                    for message in self.consumer:
                        try:
                            # Récupérer les données brutes
                            raw_data = message.value
                            logger.info(f"[MSG] Raw message received: {raw_data}")
                            
                            # Transformer les données
                            transformed_data = self.transform_user_data(raw_data)
                            logger.info(f"[TRANSFORM] Transformed: {transformed_data}")
                            
                            # Insérer dans la base de données
                            self.insert_user(transformed_data)
                            
                        except Exception as e:
                            logger.error(f"[ERROR] Error processing message: {e}")
                            continue
                except Exception as e:
                    logger.error(f"[WARN] Consumer error, restarting: {e}")
                    try:
                        if self.consumer:
                            self.consumer.close()
                    except Exception:
                        pass
                    time.sleep(1)
                    self.init_consumer()
        except KeyboardInterrupt:
            logger.info("[PAUSE] Worker stopped by user")
        finally:
            self.close()
    
    def close(self):
        """Fermer les connexions"""
        if self.consumer:
            self.consumer.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("[OK] Worker closed")

if __name__ == '__main__':
    worker = UserETLWorker()
    worker.run()

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
KAFKA_TOPICS = ['order.validated', 'order.rejected']
KAFKA_GROUP = 'order-fact-builder-group'

# Configuration PostgreSQL
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'etl_db'
DB_USER = 'etl_user'
DB_PASSWORD = 'etl_password'

class OrderFactBuilder:
    """
    Construit la table de faits orders à partir des événements Kafka
    
    Pattern Data Warehouse:
    Events (Kafka) → Fact Table (PostgreSQL) → BI/Analytics
    """
    
    def __init__(self):
        """Initialiser le builder"""
        self.db_conn = None
        self.consumer = None
        self.connect_db()
        self.init_fact_table()
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
    
    def init_fact_table(self):
        """
        Créer la table de faits orders
        Structure optimisée pour BI/Analytics
        """
        try:
            cursor = self.db_conn.cursor()
            
            # Table de faits principale
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fact_orders (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    amount DECIMAL(10, 2) NOT NULL,
                    items INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    rejection_reason TEXT,
                    order_date DATE NOT NULL,
                    processed_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fact_orders_status_check CHECK (status IN ('validated', 'rejected'))
                )
            """)
            
            # Index pour optimiser les requêtes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_orders_order_date 
                ON fact_orders(order_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_orders_status 
                ON fact_orders(status)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_fact_orders_user_id 
                ON fact_orders(user_id)
            """)
            
            self.db_conn.commit()
            cursor.close()
            logger.info("[OK] Fact table 'fact_orders' ready")
        except psycopg.Error as e:
            logger.error(f"[ERROR] Table creation failed: {e}")
            self.db_conn.rollback()
            raise
    
    def init_consumer(self):
        """Initialiser le consumer pour consommer validated ET rejected"""
        try:
            self.consumer = KafkaConsumer(
                *KAFKA_TOPICS,
                bootstrap_servers=[KAFKA_BROKER],
                group_id=KAFKA_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logger.info(f"[OK] Consumer initialized for topics: {KAFKA_TOPICS}")
        except KafkaError as e:
            logger.error(f"[ERROR] Consumer initialization failed: {e}")
            raise
    
    def extract_order_date(self, processed_at):
        """Extraire la date de processed_at"""
        try:
            dt = datetime.fromisoformat(processed_at)
            return dt.date()
        except:
            return datetime.now().date()
    
    def insert_fact(self, event_data, topic):
        """Insérer un événement dans la table de faits"""
        try:
            cursor = self.db_conn.cursor()
            
            # Déterminer le statut et la raison de rejet
            status = 'validated' if topic == 'order.validated' else 'rejected'
            rejection_reason = event_data.get('rejection_reason')
            order_date = self.extract_order_date(event_data.get('processed_at', datetime.now().isoformat()))
            
            cursor.execute("""
                INSERT INTO fact_orders 
                (order_id, user_id, amount, items, status, rejection_reason, order_date, processed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (order_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    rejection_reason = EXCLUDED.rejection_reason,
                    processed_at = EXCLUDED.processed_at
            """, (
                event_data.get('order_id'),
                event_data.get('user_id'),
                event_data.get('amount'),
                event_data.get('items'),
                status,
                rejection_reason,
                order_date,
                event_data.get('processed_at', datetime.now().isoformat())
            ))
            
            self.db_conn.commit()
            cursor.close()
            logger.info(f"[OK] Order {event_data.get('order_id')} ({status}): ${event_data.get('amount')} | {event_data.get('items')} items")
        
        except psycopg.Error as e:
            logger.error(f"[ERROR] Insert failed: {e}")
            self.db_conn.rollback()
    
    def run(self):
        """Lancer le builder"""
        logger.info("[START] Starting Order Fact Builder...")
        logger.info(f"[IN] Consuming from topics: {KAFKA_TOPICS}")
        logger.info(f"[STATS] Building fact table: fact_orders\n")

        try:
            while True:
                try:
                    for message in self.consumer:
                        try:
                            event_data = message.value
                            topic = message.topic
                            self.insert_fact(event_data, topic)
                        
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
            logger.info("[PAUSE] Builder stopped by user")
        finally:
            self.close()
    
    def close(self):
        """Fermer les connexions"""
        if self.consumer:
            self.consumer.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("[OK] Builder closed")

if __name__ == '__main__':
    builder = OrderFactBuilder()
    builder.run()

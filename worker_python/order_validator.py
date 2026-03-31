import json
import logging
import time
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Kafka
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC_IN = 'order.created'
KAFKA_TOPIC_VALIDATED = 'order.validated'
KAFKA_TOPIC_REJECTED = 'order.rejected'
KAFKA_GROUP = 'order-validator-group'

class OrderValidator:
    """Classe responsable de la validation des commandes"""
    
    @staticmethod
    def validate(order_data):
        """
        Appliquer les règles métier
        Retourne: (is_valid, error_message)
        """
        errors = []
        
        # Règle 1: Montant > 0
        if order_data.get('amount', 0) <= 0:
            errors.append("Amount must be greater than 0")
        
        # Règle 2: Items > 0
        if order_data.get('items', 0) <= 0:
            errors.append("Order must contain at least 1 item")
        
        # Règle 3: User ID existe
        if not order_data.get('user_id'):
            errors.append("User ID is required")
        
        is_valid = len(errors) == 0
        error_message = ", ".join(errors) if errors else None
        
        return is_valid, error_message

class OrderETLWorker:
    """Worker pour traiter les commandes - Pattern: Consumer -> Validator -> Producer"""
    
    def __init__(self):
        """Initialiser le worker"""
        self.consumer = None
        self.producer = None
        self.init_consumer()
        self.init_producer()
    
    def init_consumer(self):
        """Initialiser le Kafka consumer pour les commandes"""
        try:
            self.consumer = KafkaConsumer(
                KAFKA_TOPIC_IN,
                bootstrap_servers=[KAFKA_BROKER],
                group_id=KAFKA_GROUP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True
            )
            logger.info(f"[OK] Consumer initialized for topic: {KAFKA_TOPIC_IN}")
        except KafkaError as e:
            logger.error(f"[ERROR] Consumer initialization failed: {e}")
            raise
    
    def init_producer(self):
        """Initialiser le Kafka producer pour les événements validés/rejetés"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("[OK] Producer initialized")
        except KafkaError as e:
            logger.error(f"[ERROR] Producer initialization failed: {e}")
            raise
    
    def enrich_order(self, order_data):
        """
        Enrichir les données de la commande
        Ajouter des métadonnées de traitement
        """
        enriched = {
            **order_data,
            'processed_at': datetime.now().isoformat(),
            'processor': 'order-validator'
        }
        return enriched
    
    def publish_event(self, topic, data):
        """Publier un événement sur un topic Kafka"""
        try:
            future = self.producer.send(topic, value=data)
            record_metadata = future.get(timeout=10)
            logger.info(f"[OK] Published to {topic} [partition {record_metadata.partition}] @ offset {record_metadata.offset}")
        except KafkaError as e:
            logger.error(f"[ERROR] Error publishing to {topic}: {e}")
    
    def handle_order(self, order_data):
        """
        Traiter une commande: validation → publication événement
        Démonstration du découplage et traitement asynchrone
        """
        order_id = order_data.get('order_id')
        logger.info(f"[MSG] Processing order: {order_id}")
        logger.info(f"   Amount: ${order_data.get('amount')}, Items: {order_data.get('items')}")
        
        # ÉTAPE 1: Valider selon les règles métier
        is_valid, error_message = OrderValidator.validate(order_data)
        
        # ÉTAPE 2: Enrichir les données
        enriched_order = self.enrich_order(order_data)
        
        # ÉTAPE 3: Publier l'événement approprié (découplage)
        if is_valid:
            logger.info(f"[OK] Order {order_id} VALIDATED")
            self.publish_event(KAFKA_TOPIC_VALIDATED, enriched_order)
        else:
            logger.warning(f"[ERROR] Order {order_id} REJECTED: {error_message}")
            enriched_order['rejection_reason'] = error_message
            self.publish_event(KAFKA_TOPIC_REJECTED, enriched_order)
    
    def run(self):
        """Lancer le worker"""
        logger.info("[START] Starting Order Validator Worker...")
        logger.info(f"[IN] Consuming from: {KAFKA_TOPIC_IN}")
        logger.info(f"[OUT] Publishing validated to: {KAFKA_TOPIC_VALIDATED}")
        logger.info(f"[OUT] Publishing rejected to: {KAFKA_TOPIC_REJECTED}")
        logger.info("")

        try:
            while True:
                try:
                    for message in self.consumer:
                        try:
                            order_data = message.value
                            self.handle_order(order_data)
                        
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
        if self.producer:
            self.producer.flush()
            self.producer.close()
        logger.info("[OK] Worker closed")

if __name__ == '__main__':
    worker = OrderETLWorker()
    worker.run()

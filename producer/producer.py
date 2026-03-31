import json
import random
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuration Kafka
KAFKA_BROKER = 'localhost:9092'

# Topics
TOPICS = ['user.created', 'order.created', 'payment.validated']

# Initialiser le producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def generate_user_event():
    """Génère un événement user.created"""
    return {
        'event_type': 'user.created',
        'user_id': random.randint(1000, 9999),
        'username': f'user_{random.randint(1, 10000)}',
        'email': f'user_{random.randint(1, 10000)}@example.com',
        'timestamp': datetime.now().isoformat()
    }

def generate_order_event():
    """Génère un événement order.created"""
    return {
        'event_type': 'order.created',
        'order_id': random.randint(10000, 99999),
        'user_id': random.randint(1000, 9999),
        'amount': round(random.uniform(10, 500), 2),
        'items': random.randint(1, 10),
        'timestamp': datetime.now().isoformat()
    }

def generate_payment_event():
    """Génère un événement payment.validated"""
    return {
        'event_type': 'payment.validated',
        'payment_id': random.randint(100000, 999999),
        'order_id': random.randint(10000, 99999),
        'user_id': random.randint(1000, 9999),
        'amount': round(random.uniform(10, 500), 2),
        'status': 'success',
        'timestamp': datetime.now().isoformat()
    }

def send_event(topic, data):
    """Envoie un événement à Kafka"""
    try:
        future = producer.send(topic, value=data)
        record_metadata = future.get(timeout=10)
        print(f"[OK] Sent to {record_metadata.topic} [partition {record_metadata.partition}] @ offset {record_metadata.offset}")
    except KafkaError as e:
        print(f"[ERROR] Error sending message: {e}")

# Générateur d'événements
event_generators = [
    ('user.created', generate_user_event),
    ('order.created', generate_order_event),
    ('payment.validated', generate_payment_event)
]

print("[START] Starting Producer...")
print(f"[OUT] Sending 100 events to Kafka broker: {KAFKA_BROKER}\n")

# Envoyer 100 événements
for i in range(100):
    topic, generator = random.choice(event_generators)
    event_data = generator()
    send_event(topic, event_data)
    print(f"[{i+1}/100]")

print("\n[OK] All events sent!")
producer.flush()
producer.close()

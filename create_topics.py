#!/usr/bin/env python3
"""
Create required Kafka topics
"""

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import sys

try:
    admin_client = KafkaAdminClient(bootstrap_servers=['localhost:9092'])
    
    topics = [
        NewTopic(name='user.created', num_partitions=1, replication_factor=1),
        NewTopic(name='order.created', num_partitions=1, replication_factor=1),
        NewTopic(name='payment.validated', num_partitions=1, replication_factor=1),
        NewTopic(name='order.validated', num_partitions=1, replication_factor=1),
        NewTopic(name='order.rejected', num_partitions=1, replication_factor=1),
    ]
    
    print("[START] Creating Kafka topics...")
    
    try:
        admin_client.create_topics(new_topics=topics, validate_only=False)
        print("[OK] Topics created")
    except TopicAlreadyExistsError:
        print("[INFO] Topics already exist")
    except Exception as e:
        err = str(e)
        # kafka-python-ng may raise on already-existing topics even without the exception type
        if "already exists" in err or "TopicExistsException" in err:
            print("[INFO] Topics already exist")
        else:
            print(f"[ERROR] Failed to create topics: {e}")
    
    admin_client.close()
    print("[OK] Kafka topics initialized")
    
except Exception as e:
    print(f"[ERROR] Admin client error: {e}")
    sys.exit(1)

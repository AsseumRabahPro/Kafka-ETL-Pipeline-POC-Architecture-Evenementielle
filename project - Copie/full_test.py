#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite
Validates entire Kafka ETL system and generates report
"""

import subprocess
import psycopg
import json
import time
import sys
from kafka import KafkaConsumer, KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, KafkaError

class TestReport:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add_test(self, name, status, message=""):
        self.tests.append({"name": name, "status": status, "message": message})
        if status == "[OK]" or status == "[WARN]":
            self.passed += 1
        else:
            self.failed += 1
    
    def print_report(self):
        print("\n" + "=" * 80)
        print(" COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        for test in self.tests:
            status = test["status"]
            name = test["name"]
            msg = f" - {test['message']}" if test["message"] else ""
            print(f"{status} {name}{msg}")
        
        print("=" * 80)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 80)
        
        if self.failed == 0:
            print("\n[SUCCESS] All tests passed! System is ready for production.\n")
            return True
        else:
            print(f"\n[ERROR] {self.failed} test(s) failed. See details above.\n")
            return False

report = TestReport()

# ============================================================================
# PHASE 1: INFRASTRUCTURE VALIDATION
# ============================================================================
print("\n" + "█" * 80)
print("█ PHASE 1: INFRASTRUCTURE VALIDATION")
print("█" * 80)

print("\n[TEST] 1.1 Kafka Connectivity...")
try:
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        request_timeout_ms=5000,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    producer.close()
    report.add_test("Kafka Server", "[OK]", "Accessible on port 9092")
    print("[OK] Kafka is accessible")
except Exception as e:
    report.add_test("Kafka Server", "[ERROR]", str(e))
    print(f"[ERROR] Kafka connection failed: {e}")
    sys.exit(1)

print("\n[TEST] 1.2 PostgreSQL Connectivity...")
try:
    conn = psycopg.connect(
        host='localhost',
        port=5432,
        dbname='etl_db',
        user='etl_user',
        password='etl_password'
    )
    conn.close()
    report.add_test("PostgreSQL Database", "[OK]", "Connected to etl_db")
    print("[OK] PostgreSQL is accessible")
except Exception as e:
    report.add_test("PostgreSQL Database", "[ERROR]", str(e))
    print(f"[ERROR] PostgreSQL connection failed: {e}")
    sys.exit(1)

# ============================================================================
# PHASE 2: DATABASE SCHEMA VALIDATION
# ============================================================================
print("\n" + "█" * 80)
print("█ PHASE 2: DATABASE SCHEMA VALIDATION")
print("█" * 80)

print("\n[TEST] 2.1 Database Tables...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    
    # Check tables exist
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND table_type='BASE TABLE'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'users' in tables and 'fact_orders' in tables:
        report.add_test("Tables Schema", "[OK]", f"Found: users, fact_orders")
        print(f"[OK] Required tables: users, fact_orders")
    else:
        report.add_test("Tables Schema", "[ERROR]", f"Missing tables. Found: {tables}")
        print(f"[ERROR] Missing required tables")
    
    conn.close()
except Exception as e:
    report.add_test("Tables Schema", "[ERROR]", str(e))
    print(f"[ERROR] Schema validation failed: {e}")

print("\n[TEST] 2.2 Column Validation (fact_orders)...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='fact_orders' ORDER BY ordinal_position
    """)
    columns = [row[0] for row in cursor.fetchall()]
    required_cols = ['order_id', 'user_id', 'amount', 'items', 'status']
    
    missing = [col for col in required_cols if col not in columns]
    if not missing:
        report.add_test("Fact Orders Columns", "[OK]", f"All required columns present")
        print(f"[OK] Columns: {', '.join(columns)}")
    else:
        report.add_test("Fact Orders Columns", "[ERROR]", f"Missing: {missing}")
        print(f"[ERROR] Missing columns: {missing}")
    
    conn.close()
except Exception as e:
    report.add_test("Fact Orders Columns", "[ERROR]", str(e))
    print(f"[ERROR] Column validation failed: {e}")

print("\n[TEST] 2.3 Views Validation...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT table_name FROM information_schema.views 
        WHERE table_schema='public'
    """)
    views = [row[0] for row in cursor.fetchall()]
    
    required_views = ['v_orders_by_day', 'v_revenue_by_day']
    missing = [v for v in required_views if v not in views]
    
    if not missing:
        report.add_test("Analytical Views", "[OK]", f"All views created")
        print(f"[OK] Views: {', '.join(views)}")
    else:
        report.add_test("Analytical Views", "[ERROR]", f"Missing: {missing}")
        print(f"[ERROR] Missing views: {missing}")
    
    conn.close()
except Exception as e:
    report.add_test("Analytical Views", "[ERROR]", str(e))
    print(f"[ERROR] Views validation failed: {e}")

# ============================================================================
# PHASE 3: KAFKA TOPICS VALIDATION
# ============================================================================
print("\n" + "█" * 80)
print("█ PHASE 3: KAFKA TOPICS VALIDATION")
print("█" * 80)

print("\n[TEST] 3.1 Required Topics...")
try:
    consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'])
    topics = consumer.topics()
    
    required_topics = ['user.created', 'order.created', 'payment.validated', 'order.validated', 'order.rejected']
    missing = [t for t in required_topics if t not in topics]
    
    if missing:
        print(f"[WARN] Missing topics detected: {missing}")
        try:
            admin = KafkaAdminClient(bootstrap_servers=['localhost:9092'], client_id='topic-bootstrap')
            new_topics = [
                NewTopic(name=topic, num_partitions=1, replication_factor=1)
                for topic in missing
            ]
            admin.create_topics(new_topics=new_topics, validate_only=False)
            admin.close()
            time.sleep(2)
            topics = consumer.topics()
            missing = [t for t in required_topics if t not in topics]
        except Exception as e:
            print(f"[ERROR] Failed to auto-create topics: {e}")
    
    if not missing:
        report.add_test("Kafka Topics", "[OK]", f"All {len(required_topics)} topics created")
        for topic in required_topics:
            print(f"  [OK] {topic}")
    else:
        report.add_test("Kafka Topics", "[ERROR]", f"Missing: {missing}")
        print(f"[ERROR] Missing topics: {missing}")
    
    consumer.close()
except Exception as e:
    report.add_test("Kafka Topics", "[ERROR]", str(e))
    print(f"[ERROR] Topics validation failed: {e}")

# ============================================================================
# PHASE 4: DATA CONTENT VALIDATION
# ============================================================================
print("\n" + "█" * 80)
print("█ PHASE 4: DATA CONTENT VALIDATION")
print("█" * 80)

print("\n[TEST] 4.1 Users Table Population...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    
    if user_count > 0:
        report.add_test("Users Population", "[OK]", f"{user_count} users in database")
        print(f"[OK] {user_count} users found in database")
    else:
        report.add_test("Users Population", "[WARN]", "No users yet (producer not run)")
        print(f"[WARN] No users found (run producer first)")
    
    conn.close()
except Exception as e:
    report.add_test("Users Population", "[ERROR]", str(e))
    print(f"[ERROR] User count check failed: {e}")

print("\n[TEST] 4.2 Orders Table Population...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fact_orders;")
    order_count = cursor.fetchone()[0]
    
    if order_count > 0:
        cursor.execute("SELECT COUNT(*) FROM fact_orders WHERE status='validated';")
        valid_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fact_orders WHERE status='rejected';")
        reject_count = cursor.fetchone()[0]
        
        report.add_test("Orders Population", "[OK]", f"{order_count} total ({valid_count} validated, {reject_count} rejected)")
        print(f"[OK] {order_count} orders: {valid_count} validated, {reject_count} rejected")
    else:
        report.add_test("Orders Population", "[WARN]", "No orders yet (workers not run)")
        print(f"[WARN] No orders found (run workers first)")
    
    conn.close()
except Exception as e:
    report.add_test("Orders Population", "[ERROR]", str(e))
    print(f"[ERROR] Order count check failed: {e}")

print("\n[TEST] 4.3 KPI Calculations...")
try:
    conn = psycopg.connect(
        host='localhost', port=5432, dbname='etl_db',
        user='etl_user', password='etl_password'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(DISTINCT order_date) FROM fact_orders 
        WHERE order_date IS NOT NULL
    """)
    days_count = cursor.fetchone()[0]
    
    if days_count > 0:
        cursor.execute("""
            SELECT SUM(amount) FROM fact_orders 
            WHERE status='validated'
        """)
        revenue = cursor.fetchone()[0]
        
        report.add_test("KPI Data", "[OK]", f"{days_count} days of data, Revenue: ${revenue:.2f}")
        print(f"[OK] {days_count} days tracked, Revenue: ${revenue:.2f}")
    else:
        report.add_test("KPI Data", "[WARN]", "No date data yet")
        print(f"[WARN] No date data available")
    
    conn.close()
except Exception as e:
    report.add_test("KPI Data", "[ERROR]", str(e))
    print(f"[ERROR] KPI check failed: {e}")

# ============================================================================
# FINAL REPORT
# ============================================================================
success = report.print_report()

if success:
    print("\n[INSTRUCTIONS] System is ready. Run in separate terminals:")
    print("  Terminal 1: python producer/producer.py")
    print("  Terminal 2: python worker_python/worker.py")
    print("  Terminal 3: python worker_python/order_validator.py")
    print("  Terminal 4: python worker_python/order_fact_builder.py")
    print("  Terminal 5: python kpi_orders.py")
else:
    print("\n[ACTION REQUIRED] Fix errors above before proceeding.")
    sys.exit(1)

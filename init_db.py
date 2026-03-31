#!/usr/bin/env python3
"""
Initialize database schema from db/schema.sql
"""

import psycopg
import sys

try:
    # Connect to PostgreSQL
    conn = psycopg.connect(
        host='localhost',
        port=5432,
        dbname='etl_db',
        user='etl_user',
        password='etl_password'
    )
    cursor = conn.cursor()
    
    print("[START] Database initialization...")
    
    # Drop existing tables to ensure fresh schema
    print("[INFO] Cleaning existing schema...")
    cursor.execute("DROP TABLE IF EXISTS fact_orders CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
    conn.commit()
    
    # Read and execute schema
    with open('db/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor.execute(schema_sql)
    conn.commit()
    
    print("[OK] Database schema initialized successfully")
    print("[OK] Tables: users, fact_orders")
    print("[OK] Views: v_orders_by_day, v_revenue_by_day, v_orders_statistics")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] Database initialization failed: {e}")
    sys.exit(1)

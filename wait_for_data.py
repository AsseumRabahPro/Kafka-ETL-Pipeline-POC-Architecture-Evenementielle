#!/usr/bin/env python3
"""
Wait until data is ingested in users and fact_orders tables.
"""

import time
import psycopg

DB_KWARGS = dict(
    host='localhost',
    port=5432,
    dbname='etl_db',
    user='etl_user',
    password='etl_password'
)

def main():
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            conn = psycopg.connect(**DB_KWARGS)
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM users;')
            users = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM fact_orders;')
            orders = cur.fetchone()[0]
            cur.close()
            conn.close()

            if users > 0 and orders > 0:
                print(f"[OK] Data ready: users={users}, orders={orders}")
                return 0

            print(f"[WAIT] users={users}, orders={orders}")
        except Exception as exc:
            print(f"[WAIT] DB not ready: {exc}")

        time.sleep(5)

    print("[WARN] Timeout waiting for data")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

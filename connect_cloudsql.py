# file: connect_cloudsql.py
import psycopg2
from psycopg2.extras import RealDictCursor

# --- Configuration ---
DB_HOST = "10.63.160.3"
DB_NAME = "whatsub"
DB_USER = "whatsub"
DB_PASS = "WhatSub123!"
DB_PORT = 3306  # 3306 for MySQL

# --- Connect & Query ---
def fetch_users():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM users LIMIT 10;")
        users = cursor.fetchall()

        print("✅ Connection successful. Sample users:")
        for u in users:
            print(u)

    except Exception as e:
        print("❌ Database connection failed:", e)

    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    fetch_users()
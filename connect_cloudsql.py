import psycopg2
from psycopg2.extras import RealDictCursor
import pymysql
import pymysql.cursors

# --- Configuration ---
DB_HOST = "10.63.160.3"
DB_NAME = "whatsub"
DB_USER = "whatsub"
DB_PASS = "WhatSub123!"
DB_PORT = 3306  # 3306 for MySQL

# --- Connect & Query ---
def fetch_users():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            ssl={
                "ca": "../server-ca.pem",
                "cert": "../client-cert.pem",
                "key": "../client-key.pem",
                }
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users LIMIT 10;")
            users = cursor.fetchall()

            print("✅ Connection successful. Sample users:")
            for u in users:
                print(u)

    except Exception as e:
        print("❌ Database connection failed:", e)

    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == "__main__":
    fetch_users()

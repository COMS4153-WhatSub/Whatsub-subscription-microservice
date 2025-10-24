# import psycopg2
# from psycopg2.extras import RealDictCursor
# import pymysql
# import pymysql.cursors
# import os

# # --- Configuration ---
# DB_HOST = "10.63.160.3"
# DB_NAME = "whatsub"
# DB_USER = "whatsub"
# DB_PASS = "WhatSub123!"
# DB_PORT = 3306  # 3306 for MySQL

# # --- Connect & Query ---
# def fetch_users():
#     assert os.path.exists("../client-key.pem"), "Client key file not found."
#     assert os.path.exists("../client-cert.pem"), "Client cert file not found."
#     assert os.path.exists("../server-ca.pem"), "Server CA file not found."
#     try:
#         conn = pymysql.connect(
#             host=DB_HOST,
#             user=DB_USER,
#             password=DB_PASS,
#             database=DB_NAME,
#             port=DB_PORT,
#             cursorclass=pymysql.cursors.DictCursor,
#             ssl={
#                 "ca": "../server-ca.pem",
#                 "cert": "../client-cert.pem",
#                 "key": "../client-key.pem",
#                 }
#         )

#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM users LIMIT 10;")
#             users = cursor.fetchall()

#             print("✅ Connection successful. Sample users:")
#             for u in users:
#                 print(u)

#     except Exception as e:
#         print("❌ Database connection failed:", e)

#     finally:
#         if 'conn' in locals() and conn.open:
#             conn.close()

# if __name__ == "__main__":
#     fetch_users()


from sqlalchemy import create_engine, text
import os

# --- Configuration ---
# DB_HOST = "10.63.160.3"
DB_HOST = "mysql-vm.us-central1.c.testproject-473522.internal"
DB_NAME = "whatsub"
DB_USER = "whatsub"
DB_PASS = "WhatSub123!"
DB_PORT = 3306  # MySQL
SSL_CA = "../server-ca.pem"
SSL_CERT = "../client-cert.pem"
SSL_KEY = "../client-key.pem"

# --- Create SQLAlchemy engine ---
def create_db_engine():
    # Ensure SSL files exist
    for f in [SSL_CA, SSL_CERT, SSL_KEY]:
        assert os.path.exists(f), f"❌ Missing SSL file: {f}"

    # MySQL connection string using PyMySQL driver
    connection_url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        f"?ssl_ca={SSL_CA}&ssl_cert={SSL_CERT}&ssl_key={SSL_KEY}"
    )

    engine = create_engine(
        connection_url,
        echo=False,  # set True for SQL debug output
        pool_pre_ping=True,  # ensures connection validity
    )
    return engine

# --- Fetch and display users ---
def fetch_users():
    try:
        engine = create_db_engine()

        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users LIMIT 10;"))
            users = result.mappings().all()

            print("✅ Connection successful. Sample users:")
            for u in users:
                print(dict(u))

    except Exception as e:
        print("❌ Database connection failed:", e)

if __name__ == "__main__":
    fetch_users()

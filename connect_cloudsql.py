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
    )

    engine = create_engine(
        connection_url,
        echo=False,  # set True for SQL debug output
        pool_pre_ping=True,  # ensures connection validity
        connect_args={
            "ssl": {
                "ca": SSL_CA,
                "cert": SSL_CERT,
                "key": SSL_KEY,
                "check_hostname": False,
            }
        }
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

# subscription-microservice

A simple FastAPI microservice for managing subscriptions.

---

## Local Development Setup

### Prerequisites

- Python 3.9+
- MySQL 5.7+ or MySQL 8.0+
- pip

### Database Setup

1. **Create the local database manually:**
   ```bash
   mysql -u root -p
   ```
   Then run:
   ```sql
   CREATE DATABASE IF NOT EXISTS whatsub_subscriptions_local
       CHARACTER SET utf8mb4
       COLLATE utf8mb4_unicode_ci;
   
   USE whatsub_subscriptions_local;
   
   CREATE TABLE IF NOT EXISTS subscriptions (
       subscription_id INT AUTO_INCREMENT PRIMARY KEY,
       user_id CHAR(36) NOT NULL,
       name VARCHAR(255) NOT NULL,
       url VARCHAR(500),
       account VARCHAR(255),
       billing_type ENUM('monthly', 'quarterly', 'annually') NOT NULL,
       billing_date DATE,
       price DECIMAL(10, 2),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       INDEX idx_user_id (user_id),
       INDEX idx_billing_date (billing_date),
       INDEX idx_billing_type (billing_type)
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

2. **Create a `.env` file** in the project root with your MySQL credentials:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASS=your_mysql_password
   DB_NAME=whatsub_subscriptions_local
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python -m app.main
   ```
   Or:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
   ```

The application will automatically create tables if they don't exist (via SQLAlchemy's `create_all`).

---

## Key Features

### CRUD Operations

- **Create new subscriptions** (POST /subscriptions)
- **Retrieve single subscription by ID** (GET /subscriptions/{sub_id})
- **List all subscriptions**, optionally filtered by user (GET /subscriptions?user_id=...)
- **Update subscription partially** (PATCH /subscriptions/{sub_id})
- **Delete subscriptions** (DELETE /subscriptions/{sub_id})

### Billing

- Supports three billing types: monthly, quarterly, and annually.
- Calculates subscription end date automatically based on billing type.
- Maintains `billing_date` for the first payment.
- Price is either user-specified or assigned a default based on the subscription plan.

### Health Monitoring

- Provides service health information including timestamp, status, IP address, and optional echo values.
- Accessible via `/health` and `/health/{path_echo}` endpoints.
- Designed for integration with monitoring tools or uptime checks.

<!-- ### Statistics & Reporting

- Aggregates subscription data: total subscriptions, total active, count by plan, and count by billing type.
- Endpoint: `GET /subscriptions/stats`
- Supports sending stats to external notification services via `POST /subscriptions/notify_counts`. -->

### Validation & Typing

- Uses Pydantic models for strict type validation:
  - `SubscriptionCreate` for subscription creation requests.
  - `SubscriptionUpdate` for partial updates.
  - `SubscriptionRead` for consistent API responses.
  - `BillingType` enum ensures only valid billing intervals.
- Ensures data integrity, type safety, and clear API contracts.

---
## Data Model

### SubscriptionRead

- **id**: UUID – Unique subscription identifier.
- **user_id**: str – ID of the user owning the subscription.
- **plan**: str – Subscription plan name (e.g., "Basic", "Pro").
- **start_date**: datetime – Subscription start date.
- **end_date**: datetime – Subscription end date, calculated from billing type.
- **billing_date**: datetime – Date of first billing.
- **price**: Decimal – Subscription price.
- **account**: str – Account identifier (default or placeholder).
- **billing_type**: BillingType – One of monthly, quarterly, or annually.

### SubscriptionCreate

- **Required**: user_id, plan, billing_type.
- **Optional**: price (if not provided, default price is applied).

### SubscriptionUpdate

- **Optional fields**: plan, billing_type, end_date, price.

---

## Folder Structure
```
Whatsub-subscription-microservice/
│── main.py # Entry point
│── requirements.txt # Dependencies
│── app/
│ │── init.py
│ │── models.py # Pydantic models
│ │── crud.py # CRUD functions
│ │── routes.py # API routes
│ │── fake_db.py # In-memory DB
│ │── health.py # Health check
```

---

## API Endpoints
- Health Check: GET /health

- Create Subscription: POST /subscriptions

- List Subscriptions for a User: GET /subscriptions?user_id=<uuid>

- Count User Subscriptions: GET /subscriptions/count/{user_id}
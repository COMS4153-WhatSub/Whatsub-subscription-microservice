# subscription-microservice

A simple FastAPI microservice for managing subscriptions.

---

## Folder Structure
```
Whatsub-subscription-microservice\
│── main.py # Entry point
│── requirements.txt
│── app/
│ │── init.py
│ │── models.py # Pydantic models
│ │── crud.py # CRUD functions
│ │── routes.py # API routes
│ │── fake_db.py # DB
│ │── health.py # Health check
```

---

## API Endpoints
- Subscriptions: POST, GET, PUT, DELETE /subscriptions

- Health: GET /health and /health/{path_echo}

- Root: GET /
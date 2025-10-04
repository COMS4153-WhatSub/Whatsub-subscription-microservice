# subscription-microservice

A simple FastAPI microservice for managing subscriptions.

---

## Features
- Create and manage subscriptions  
- Track how many subscriptions a user has  
- Update or cancel subscriptions  
- Health check endpoint  

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
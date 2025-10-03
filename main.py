import os
from fastapi import FastAPI
from app.routes import router

port = int(os.environ.get("FASTAPIPORT", 8000))

app = FastAPI(title="Subscription API", version="0.1.0")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

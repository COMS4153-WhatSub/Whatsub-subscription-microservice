from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.utils.db import session_scope

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/db-health")
async def db_health():
    try:
        with session_scope() as session:
            session.execute(text("SELECT 1"))
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Database health check failed: {str(e)}"}
        )


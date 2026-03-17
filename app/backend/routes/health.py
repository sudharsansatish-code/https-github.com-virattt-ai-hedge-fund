from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging

from sqlalchemy import text
from app.backend.database.connection import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Welcome to AI Hedge Fund API"}


@router.get("/health")
async def health_check():
    """Production-ready health check that verifies database connectivity."""
    db_status = "connected"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as e:
        logger.warning(f"Health check DB failure: {e}")
        db_status = "disconnected"

    status = "ok" if db_status == "connected" else "degraded"
    status_code = 200 if status == "ok" else 503

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "database": db_status,
            "version": "1.0.0",
        },
    )


@router.get("/ping")
async def ping():
    async def event_generator():
        for i in range(5):
            # Create a JSON object for each ping
            data = {"ping": f"ping {i+1}/5", "timestamp": i + 1}

            # Format as SSE
            yield f"data: {json.dumps(data)}\n\n"

            # Wait 1 second
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict

from ..database import get_db
from ..schemas import ErrorResponse, HealthResponse


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Healthcheck Endpoint",
    responses={
        200: {"model": HealthResponse, "description": "Success"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def healthcheck(db: Session = Depends(get_db)) -> Dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database is not connected")

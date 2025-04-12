from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict
import os

from common.object_storage.client import ObjectStorageClient

from ..database import get_db
from ..schemas.interactions import ErrorResponse, HealthResponse

router = APIRouter()

BILL_TEXT_BUCKET_NAME = os.getenv("BILL_TEXT_BUCKET_NAME")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Healthcheck Endpoint",
    responses={
        200: {"model": HealthResponse, "description": "Success"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def healthcheck(
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    # Check database connection
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to access database with error: {e}",
        )

    # Check S3 access
    try:
        s3_client = ObjectStorageClient()
        s3_client.check_connection(BILL_TEXT_BUCKET_NAME)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to access s3 with error: {e}",
        )

    return {"status": "healthy"}

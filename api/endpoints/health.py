from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict
from botocore.exceptions import ClientError
import boto3
import os

from common.object_storage.client import create_storage_client

from ..database import get_db
from ..schemas import ErrorResponse, HealthResponse

router = APIRouter()

BILL_TEXT_BUCKET_NAME = os.getenv("BILL_TEXT_BUCKET_NAME")


def check_s3_access(bucket_name: str) -> bool:
    """
    Verify S3 access by attempting to list objects in the specified bucket.
    """
    try:
        s3_client = boto3.client("s3")
        s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ["NoSuchBucket", "AccessDenied"]:
            return False
        raise e


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
        s3_client = create_storage_client()
        s3_client.check_connection(BILL_TEXT_BUCKET_NAME)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to access s3 with error: {e}",
        )

    return {"status": "healthy"}

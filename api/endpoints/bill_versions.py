from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime

from common.database.referendum import crud, schemas
from common.object_storage.client import ObjectStorageClient
from ..config import settings
from ..database import get_db
from ..schemas import ErrorResponse
from ..security import CredentialsException, get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)
router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_version,
    create_schema=schemas.BillVersion.Base,
    update_schema=schemas.BillVersion.Record,
    response_schema=schemas.BillVersion.Full,
    resource_name="bill_version",
)

CHAT_SESSIONS = {}


@router.get(
    "/{bill_version_id}/text",
    response_model=Dict[str, str | int],
    summary="Get bill text",
    responses={
        200: {"model": Dict[str, str | int], "description": "Bill text successfully retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_text(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    try:
        s3_client = ObjectStorageClient()
        text = s3_client.download_file(
            bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
        ).decode("utf-8")

        return {"bill_version_id": bill_version_id, "hash": bill_version.hash, "text": text}

    except CredentialsException as e:
        raise e
    except Exception as e:
        logger.error(f"Error downloading bill text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving bill text: {str(e)}")


@router.get("/{bill_version_id}/chat/initialize")
async def initialize_chat(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    try:
        s3_client = ObjectStorageClient()
        text = s3_client.download_file(
            bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
        ).decode("utf-8")

        # TODO - fail for bills that are too long

        session_id = 1  # TODO - generate unique ID

        CHAT_SESSIONS[session_id] = {
            "initial_prompt": "You are an expert in the attached bill and you are answering questions from a "
            "concerned citizen",
            "bill_version_id": bill_version_id,
            "text": text,
            "chat_history": [],
            "session_start_time": datetime.now(),
        }

        return CHAT_SESSIONS

    except CredentialsException as e:
        raise e
    except Exception as e:
        logger.error(f"Error downloading bill text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving bill text: {str(e)}")


@router.get("/{bill_version_id}/chat/message")
async def message_chat(
    bill_version_id: int,
    session_id: int,
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    session = CHAT_SESSIONS.get(session_id)
    if not session:
        raise Exception()  # TODO - add message

    # Compose chat

    # Send message

    result = {}

    return result


@router.get("/{bill_version_id}/chat/terminate")
async def terminate_chat(
    bill_version_id: int,
    session_id: int,
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    CHAT_SESSIONS.pop(session_id)

    return


@router.get(
    "/{bill_version_id}/briefing",
    response_model=Dict[str, str | int],
    summary="Get bill briefing",
    responses={
        200: {"model": Dict[str, str | int], "description": "Bill briefing successfully retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
    },
)
async def get_bill_text(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    return {"bill_version_id": bill_version_id, "briefing": bill_version.briefing}

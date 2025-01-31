import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.chat.bill import BillChatSessionManager
from common.chat.service import LLMService, OpenAIException
from common.database.referendum import crud, schemas
from common.object_storage.client import ObjectStorageClient

from ..database import get_db
from ..schemas.interactions import (
    ErrorResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSession,
)
from ..security import CredentialsException, get_current_user_or_verify_system_token
from ..settings import settings
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)
router = APIRouter()
session_manager = BillChatSessionManager(
    max_bill_length=settings.MAX_BILL_LENGTH_WORDS,
    session_timeout_seconds=settings.CHAT_SESSION_TIMEOUT_SECONDS,
)

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_version,
    create_schema=schemas.BillVersion.Base,
    update_schema=schemas.BillVersion.Record,
    response_schema=schemas.BillVersion.Full,
    resource_name="bill_version",
)


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
async def get_bill_briefing(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)
    briefing = None
    if bill_version.briefing:
        briefing = bill_version.briefing
    else:
        s3_client = ObjectStorageClient()
        bill_text = s3_client.download_file(
            bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
        ).decode("utf-8")

        llm_service = LLMService()
        system_prompt = (
            "You are an expert in analyzing legislative bills and communicating them to the public. "
            "Please provide a clear, concise summary of the following bill for the average american citizen. "
            "If there are any notable concerns or ambiguities, mention them. "
            "Keep the summary to 5 lines maximum. "
        )
        text_prompt = f"Bill text: {bill_text}\n\n"
        try:
            briefing = await llm_service.generate_response(system_prompt, text_prompt)
        except OpenAIException as e:
            raise HTTPException(
                status_code=500, detail=f"LLM Service call failed with error: {str(e)}"
            )

        # Save the new briefing to the DB
        crud.bill_version.update(db=db, db_obj=bill_version, obj_in={"briefing": briefing})

    return {"bill_version_id": bill_version_id, "briefing": briefing}


@router.put(
    "/{bill_version_id}/chat",
    response_model=ChatSession,
    summary="Initialize a new chat session",
    responses={
        201: {"model": ChatSession, "description": "Chat session successfully initialized"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def initialize_chat(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    """Initialize a new chat session for a specific bill version."""
    try:
        # Verify bill version exists
        bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)
        if not bill_version:
            raise HTTPException(status_code=404, detail="Bill version not found")

        # Get bill text
        s3_client = ObjectStorageClient()
        text = s3_client.download_file(
            bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
        ).decode("utf-8")

        # Create new session
        session_id = session_manager.create_session(bill_version_id, text)
        return {"session_id": session_id}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error initializing chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing chat session: {str(e)}")


@router.post(
    "/{bill_version_id}/chat",
    response_model=ChatMessageResponse,
    summary="Send a message to the chat session",
    responses={
        200: {"model": ChatMessageResponse, "description": "Message processed successfully"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        429: {"model": ErrorResponse, "description": "Monthly message limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def message_chat(
    bill_version_id: int,
    message_request: ChatMessageRequest,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> ChatMessageResponse:
    """Process a message in an existing chat session."""
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if not current_user.settings:
            current_user.settings = {}

        current_month = datetime.utcnow().date().replace(day=1).isoformat()
        last_reset = current_user.settings.get("message_count_reset_date")
        if not last_reset or last_reset < current_month:
            current_user.settings["message_count"] = 0
            current_user.settings["message_count_reset_date"] = current_month

        current_count = current_user.settings.get("message_count", 0)
        if current_count >= settings.MAX_MESSAGES_PER_MONTH:
            raise HTTPException(status_code=429, detail="Monthly message limit exceeded")
        current_user.settings["message_count"] = current_count + 1
        db.commit()

    try:
        response = session_manager.send_message(message_request.session_id, message_request.message)

        return ChatMessageResponse(response=response, session_id=message_request.session_id)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@router.delete(
    "/{bill_version_id}/chat",
    response_model=Dict[str, str],
    summary="Terminate a chat session",
    responses={
        200: {"description": "Chat session successfully terminated"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def terminate_chat(
    bill_version_id: int,
    session_id: str,
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    """Terminate an existing chat session."""
    try:
        session_manager.terminate_session(session_id)
        return {"message": "Chat session terminated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error terminating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error terminating chat session: {str(e)}")

import logging
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from common.chat.bill import BillChatSessionManager
from common.chat.service import LLMService, OpenAIException
from common.database.referendum import crud, schemas
from common.object_storage.client import ObjectStorageClient
from common.object_storage.schemas import ContentBlock, ContentBlockType, StructuredBillText
from ..database import get_db
from ..schemas.interactions import (
    ErrorResponse,
    ChatMessageRequest,
    ChatMessageResponse,
)
from ..security import get_current_user_or_verify_system_token
from ..settings import settings
from ._core import EndpointGenerator, handle_crud_exceptions, handle_general_exceptions

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
@handle_crud_exceptions("bill_version")
async def get_bill_text(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    s3_client = ObjectStorageClient()
    text = s3_client.download_file(
        bucket=settings.BILL_TEXT_BUCKET_NAME,
        key=f"{bill_version.hash}.txt",
    ).decode("utf-8")

    return {"bill_version_id": bill_version_id, "hash": bill_version.hash, "text": text}


@router.get(
    "/v2/{bill_version_id}/text",
    response_model=StructuredBillText,
    summary="Get bill text",
    responses={
        200: {
            "model": StructuredBillText,
            "description": "Structured bill text successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill_version")
async def get_bill_text(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> StructuredBillText:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    s3_client = ObjectStorageClient()
    try:
        json_data = s3_client.download_file(
            bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.json"
        ).decode("utf-8")

        structured_text = StructuredBillText.model_validate_json(json_data)

    except Exception as e:
        logger.error(f"Error retrieving structured bill text: {str(e)}")
        try:
            plain_text = s3_client.download_file(
                bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
            ).decode("utf-8")

            structured_text = StructuredBillText(
                title=f"Bill Version {bill_version_id}",
                content=[
                    ContentBlock(
                        id="root",
                        type=ContentBlockType.PARAGRAPH,
                        text=plain_text,
                        content=[],
                        indent_level=0,
                        annotations=[],
                    )
                ],
            )
        except Exception as inner_e:
            logger.error(f"Error retrieving plain text fallback: {str(inner_e)}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve bill text in any format"
            )

    return structured_text


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
@handle_crud_exceptions("bill_version")
async def get_bill_briefing(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

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
    response_model=ChatMessageResponse,
    summary="Initialize a new chat session",
    responses={
        201: {"model": ChatMessageResponse, "description": "Chat session successfully initialized"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill_version")
async def initialize_chat(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    """Initialize a new chat session for a specific bill version."""
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)

    # Get bill text
    s3_client = ObjectStorageClient()
    text = s3_client.download_file(
        bucket=settings.BILL_TEXT_BUCKET_NAME, key=f"{bill_version.hash}.txt"
    ).decode("utf-8")

    # Create new session
    session_id = session_manager.create_session(bill_version_id, text)
    return {
        "session_id": session_id,
        "response": "Hi, what can I help you learn about this bill?",
    }


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
@handle_general_exceptions()
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
        settings_update = {
            "message_count": current_count + 1,
            "message_count_reset_date": current_month,
        }
        current_user.settings = {**current_user.settings, **settings_update}
        db.commit()

    response = session_manager.send_message(message_request.session_id, message_request.message)

    return ChatMessageResponse(response=response, session_id=message_request.session_id)


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
    session_manager.terminate_session(session_id)
    return {"message": "Chat session terminated successfully"}

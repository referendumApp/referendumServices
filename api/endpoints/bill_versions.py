from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
from datetime import datetime
import uuid
from pydantic import BaseModel

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


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ChatSession(BaseModel):
    session_id: str
    bill_version_id: int
    initial_prompt: str
    text: str
    chat_history: List[ChatMessage]
    session_start_time: datetime
    last_activity: datetime


@router.get(
    "/{bill_version_id}/chat/initialize",
    response_model=Dict[str, str],
    summary="Initialize a new chat session",
    responses={
        200: {"description": "Chat session successfully initialized"},
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

        # Check bill length
        if len(text.split()) > settings.MAX_BILL_LENGTH_WORDS:
            raise HTTPException(
                status_code=400,
                detail=f"Bill exceeds maximum length of {settings.MAX_BILL_LENGTH_WORDS} words",
            )

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Create new chat session
        current_time = datetime.utcnow()
        CHAT_SESSIONS[session_id] = ChatSession(
            session_id=session_id,
            bill_version_id=bill_version_id,
            initial_prompt=(
                "You are an expert in analyzing legislative bills. "
                "You are helping a concerned citizen understand the following bill. "
                "Please provide clear, accurate information based on the bill's content. "
                "If you're unsure about something, please say so."
            ),
            text=text,
            chat_history=[],
            session_start_time=current_time,
            last_activity=current_time,
        )

        return {"session_id": session_id}

    except CredentialsException as e:
        raise e
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error initializing chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing chat session: {str(e)}")


class ChatMessageRequest(BaseModel):
    message: str
    session_id: str


class ChatMessageResponse(BaseModel):
    response: str
    session_id: str


@router.post(
    "/{bill_version_id}/chat/message",
    response_model=ChatMessageResponse,
    summary="Send a message to the chat session",
    responses={
        200: {"description": "Message processed successfully"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def message_chat(
    bill_version_id: int,
    message_request: ChatMessageRequest,
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> ChatMessageResponse:
    """Process a message in an existing chat session."""
    try:
        # Verify session exists and matches bill version
        session = CHAT_SESSIONS.get(message_request.session_id)
        if not session or session.bill_version_id != bill_version_id:
            raise HTTPException(status_code=404, detail="Chat session not found")

        # Check session expiry
        if (
            datetime.utcnow() - session.last_activity
        ).seconds > settings.CHAT_SESSION_TIMEOUT_SECONDS:
            CHAT_SESSIONS.pop(message_request.session_id)
            raise HTTPException(status_code=404, detail="Chat session has expired")

        # Add user message to history
        current_time = datetime.utcnow()
        session.chat_history.append(
            ChatMessage(role="user", content=message_request.message, timestamp=current_time)
        )

        # Prepare chat context
        messages = [
            {"role": "system", "content": session.initial_prompt},
            {"role": "system", "content": f"Bill text: {session.text}"},
            *[{"role": msg.role, "content": msg.content} for msg in session.chat_history],
        ]

        # TODO: Integrate with your chosen AI service
        # This is a placeholder - replace with actual AI service call
        ai_response = "This is a placeholder response. Replace with actual AI integration."

        # Add AI response to history
        session.chat_history.append(
            ChatMessage(role="assistant", content=ai_response, timestamp=datetime.utcnow())
        )

        # Update last activity
        session.last_activity = current_time

        return ChatMessageResponse(response=ai_response, session_id=message_request.session_id)

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")


@router.delete(
    "/{bill_version_id}/chat/terminate",
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
        session = CHAT_SESSIONS.get(session_id)
        if not session or session.bill_version_id != bill_version_id:
            raise HTTPException(status_code=404, detail="Chat session not found")
        CHAT_SESSIONS.pop(session_id)
        return {"message": "Chat session terminated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error terminating chat session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error terminating chat session: {str(e)}")

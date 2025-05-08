# TODO: Migrate all these endpoints
import boto3
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.chat.service import LLMService
from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DependencyException,
)

from ..settings import settings
from ..database import get_db
from ..schemas.interactions import ErrorResponse
from ..security import (
    get_current_user,
    get_current_user_or_verify_system_token,
    validate_user_or_verify_system_token,
)
from ._core import handle_general_exceptions, handle_crud_exceptions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Comment.Full,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new comment",
    responses={
        201: {
            "model": schemas.Comment.Full,
            "description": "Comment successfully created",
        },
        413: {
            "model": ErrorResponse,
            "description": "Comment exceeds character limit (max 500 characters)",
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("comment")
async def create_comment(
    comment: schemas.Comment.Base,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.Comment:
    if user.id != comment.user_id:
        logger.error(
            f"Unauthorized attempt to create user comment: User {user.id} tried to create comment for user {comment.user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="You can only create your own comments",
        )

    if hasattr(comment, "content") and len(comment.content) > settings.COMMENT_CHAR_LIMIT:
        logger.warning(
            f"Comment creation rejected: content length {len(comment.content)} exceeds limit of {settings.COMMENT_CHAR_LIMIT}"
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Comment cannot exceed {settings.COMMENT_CHAR_LIMIT} characters",
        )

    if settings.ENVIRONMENT != "local":
        llm_service = LLMService(settings.OPENAI_API_KEY)
        moderation_system_prompt = """
        You are a fair and objective content moderator for a political discussion platform designed to foster productive conversations.
    
        Your task is to evaluate comments and classify them as:
        - 'green': unproblematic
        - 'yellow': borderline problematic and require human review. May contain subtle personal attacks, potential misinformation that requires fact-checking, misleading framing of issues, dogwhistles, or excessive partisan rhetoric
        - 'red': Comments that clearly violate community standards and should be blocked. These include hate speech, clear personal attacks, obvious misinformation, incitement to violence, threats, doxxing, or spam.
        Guidelines for evaluation:
        1. Respect diverse political viewpoints 
        2. Focus on the tone and substance rather than the political position
        3. Allow criticism of policies, politicians, and political parties when expressed constructively
        4. Distinguish between passionate debate (allowed) and personal attacks (not allowed)
        5. Identify inflammatory content designed to provoke rather than discuss
    
        Reply with only 'green', 'yellow', or 'red' as your classification.
        """

        evaluation_result = await llm_service.generate_response(
            system_prompt=moderation_system_prompt,
            user_prompt=comment.comment,
        )
        evaluation = evaluation_result.strip().lower()
        logger.info(
            f"Comment moderation: User {user.id} | Result: {evaluation} | Text: {comment.comment[:100]}{('...' if len(comment.comment) > 100 else '')}"
        )

        if evaluation in {"yellow", "red"}:
            user_info = f"User ID: {user.id}"
            if hasattr(user, "username"):
                user_info += f", Username: {user.username}"
            if hasattr(user, "email"):
                user_info += f", Email: {user.email}"

            ses = boto3.client("ses", region_name=settings.AWS_REGION)
            ses.send_email(
                Source="admin@referendumapp.com",
                Destination={"ToAddresses": ["moderation@referendumapp.com"]},
                Message={
                    "Subject": {
                        "Data": f"Moderation Alert: {evaluation.capitalize()} Comment Detected"
                    },
                    "Body": {
                        "Text": {
                            "Data": f"{user_info}\nEvaluation: {evaluation}\nComment: {comment.comment}\n\nTimestamp: {datetime.now().isoformat()}"
                        },
                    },
                },
            )

            logger.info(f"Moderation alert email sent for {evaluation} comment from user {user.id}")

        if evaluation == "red":
            logger.warning(f"Blocked comment from user {user.id}: {comment.comment}")
            raise HTTPException(
                status_code=400,
                detail="This comment was blocked because it doesn't meet our community standards for constructive discussion.",
            )

        if evaluation == "yellow":
            logger.info(f"Flagged comment from user {user.id} for review: {comment.comment}")

    return crud.comment.create(db=db, obj_in=comment)


@router.get(
    "/{comment_id}",
    response_model=schemas.Comment.Full,
    summary="Get a comment",
    responses={
        200: {
            "model": schemas.Comment.Full,
            "description": "Comment successfully retrieved",
        },
        404: {"model": ErrorResponse, "description": "Comment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("comment")
async def read_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    return crud.comment.read(db=db, obj_id=comment_id)


@router.put(
    "/",
    response_model=schemas.Comment.Full,
    summary="Update a comment",
    responses={
        200: {
            "model": schemas.Comment.Full,
            "description": "Comment successfully updated",
        },
        413: {
            "model": ErrorResponse,
            "description": "Comment exceeds character limit (max 500 characters)",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this comment",
        },
        404: {"model": ErrorResponse, "description": "Comment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("comment")
async def update_comment(
    comment: schemas.Comment.Record,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Comment:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != comment.user_id:
            logger.error(
                f"Unauthorized attempt to update user comment: User {current_user.id} tried to update comment {comment.id}"
            )
            raise HTTPException(status_code=403, detail="You can only update your own comments")

    if hasattr(comment, "content") and len(comment.content) > settings.COMMENT_CHAR_LIMIT:
        logger.warning(
            f"Comment update rejected: content length {len(comment.content)} exceeds limit of {settings.COMMENT_CHAR_LIMIT}"
        )
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Comment cannot exceed {settings.COMMENT_CHAR_LIMIT} characters",
        )

    db_comment = crud.comment.read(db=db, obj_id=comment.id)
    return crud.comment.update(db=db, db_obj=db_comment, obj_in=comment)


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    responses={
        204: {"description": "Comment successfully deleted"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can delete comments",
        },
        404: {"model": ErrorResponse, "description": "Comment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("comment")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> None:
    db_comment = crud.comment.read(db=db, obj_id=comment_id)

    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != db_comment.user_id:
            logger.error(
                f"Unauthorized attempt to delete user comment: User {current_user.id} tried to update comment {db_comment.id}"
            )
            raise HTTPException(status_code=403, detail="You can only delete your own comments")

    try:
        crud.comment.delete(db=db, obj_id=comment_id)
        logger.info(f"Successfully deleted comment with ID: {comment_id}")
    except DependencyException:
        logger.error(f"Attempted to delete a comment with replies: {comment_id}")
        raise HTTPException(status_code=403, detail="Comment with replies cannot be deleted")


@router.post(
    "/{comment_id}/endorsement",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Endorse a comment",
    responses={
        204: {"description": "Comment successfully endorsed"},
        404: {"model": ErrorResponse, "description": "Comment not found"},
        409: {"model": ErrorResponse, "description": "Comment already endorsed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def endorse_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        return crud.user.like_comment(db=db, user_id=user.id, comment_id=comment_id)
    except ObjectAlreadyExistsException:
        raise HTTPException(status_code=409, detail="Comment already endorsed")


@router.delete(
    "/{comment_id}/endorsement",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unendorse a comment",
    responses={
        204: {"description": "Comment successfully unendorsed"},
        404: {"model": ErrorResponse, "description": "Comment like not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def unendorse_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        return crud.user.unlike_comment(db=db, user_id=user.id, comment_id=comment_id)
    except ObjectNotFoundException:
        raise HTTPException(status_code=404, detail="Comment endorsement not found")

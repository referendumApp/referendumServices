import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
    DependencyException,
)

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import (
    get_current_user,
    get_current_user_or_verify_system_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Comment,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new comment",
    responses={
        201: {
            "model": schemas.Comment,
            "description": "Comment successfully created"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def create_comment(
    comment: schemas.CommentBase,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.Comment:
    try:
        user_comment = schemas.CommentCreate(
            **comment.model_dump(),
            user_id=user.id,
        )
        return crud.comment.create(db=db, obj_in=user_comment)
    except DatabaseException as e:
        logger.error(f"Database error while creating comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{comment_id}",
    response_model=schemas.Comment,
    summary="Get a comment",
    responses={
        200:
            {
                "model": schemas.Comment,
                "description": "Comment successfully retrieved",
            },
        404: {
            "model": ErrorResponse,
            "description": "Comment not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def read_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    try:
        return crud.comment.read(db=db, obj_id=comment_id)
    except ObjectNotFoundException:
        logger.warning(f"Comment not found for id: {comment_id}")
        raise HTTPException(
            status_code=404, detail=f"Comment not found for id: {comment_id}"
        )
    except DatabaseException as e:
        logger.error(f"Database error while reading comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.Comment,
    summary="Get a comment",
    responses={
        200: {
            "model": schemas.Comment,
            "description": "Comment successfully updated"
        },
        403:
            {
                "model": ErrorResponse,
                "description": "Unauthorized to update this comment",
            },
        404: {
            "model": ErrorResponse,
            "description": "Comment not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def update_comment(
    comment: schemas.Comment,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Comment:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != comment.user_id:
            logger.error(
                f"Unauthorized attempt to update user comment: User {current_user.id} tried to update comment {comment.id}"
            )
            raise HTTPException(
                status_code=403, detail="You can only update your own comments"
            )
    try:
        db_comment = crud.comment.read(db=db, obj_id=comment.id)
        return crud.comment.update(db=db, db_obj=db_comment, obj_in=comment)
    except ObjectNotFoundException:
        logger.warning(f"Attempt to update non-existent comment with id: {comment.id}")
        raise HTTPException(
            status_code=404, detail=f"Comment not found for id: {comment.email}."
        )
    except DatabaseException as e:
        logger.error(f"Database error while updating comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    responses={
        204: {
            "description": "Comment successfully deleted"
        },
        403:
            {
                "model": ErrorResponse,
                "description": "Only system token can delete comments",
            },
        404: {
            "model": ErrorResponse,
            "description": "Comment not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> None:
    try:
        db_comment = crud.comment.read(db=db, obj_id=comment_id)
    except ObjectNotFoundException:
        logger.warning(f"Attempt to delete non-existent comment with ID: {comment_id}")
        raise HTTPException(
            status_code=404, detail=f"Comment not found for ID: {comment_id}."
        )

    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != db_comment.user_id:
            logger.error(
                f"Unauthorized attempt to delete user comment: User {current_user.id} tried to update comment {db_comment.id}"
            )
            raise HTTPException(
                status_code=403, detail="You can only delete your own comments"
            )

    try:
        crud.comment.delete(db=db, obj_id=comment_id)
        logger.info(f"Successfully deleted comment with ID: {comment_id}")
        return
    except DependencyException:
        logger.error(f"Attempted to delete a comment with replies: {comment_id}")
        raise HTTPException(
            status_code=403, detail="Comment with replies cannot be deleted"
        )
    except DatabaseException as e:
        logger.error(f"Database error while deleting comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{comment_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Like a comment",
    responses={
        204: {
            "description": "Comment successfully liked"
        },
        404: {
            "model": ErrorResponse,
            "description": "Comment not found"
        },
        409: {
            "model": ErrorResponse,
            "description": "Comment already liked"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        return crud.user.like_comment(db=db, user_id=user.id, comment_id=comment_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Comment not found for id {comment_id}"
        )
    except ObjectAlreadyExistsException:
        raise HTTPException(status_code=409, detail="Comment already liked")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{comment_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlike a comment",
    responses={
        204: {
            "description": "Comment successfully unliked"
        },
        404: {
            "model": ErrorResponse,
            "description": "Comment like not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        return crud.user.unlike_comment(db=db, user_id=user.id, comment_id=comment_id)
    except ObjectNotFoundException:
        raise HTTPException(status_code=404, detail="Comment like not found")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

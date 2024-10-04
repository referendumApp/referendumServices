from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..schemas import UserCreateInput, ErrorResponse
from ..security import (
    get_current_user_or_verify_system_token,
    get_user_create_with_hashed_password,
    verify_system_token,
)

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new user",
    responses={
        201: {"model": schemas.User, "description": "User successfully created"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can create users",
        },
        409: {"model": ErrorResponse, "description": "Email already registered"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_user(
    user: UserCreateInput,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.User:
    try:
        user_create = get_user_create_with_hashed_password(user)
        return crud.user.create(db=db, obj_in=user_create)
    except ObjectAlreadyExistsException:
        raise HTTPException(
            status_code=409, detail=f"Email already registered: {user.email}"
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Get user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only retrieve your own user information.",
            )
    try:
        return crud.user.read(db=db, obj_id=user_id)
    except ObjectNotFoundException:
        raise HTTPException(status_code=404, detail=f"User not found for id: {user_id}")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.User,
    summary="Update user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully updated",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_user(
    user: UserCreateInput,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.email != user.email:
            raise HTTPException(
                status_code=403, detail="You can only update your own user information."
            )
    try:
        db_user = crud.user.get_user_by_email(db, email=user.email)
        user_create = get_user_create_with_hashed_password(user)
        return crud.user.update(db=db, db_obj=db_user, obj_in=user_create)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"User not found for email: {user.email}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        204: {"description": "User successfully deleted"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can delete users",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> None:
    try:
        return crud.user.delete(db=db, obj_id=user_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"User not found for ID: {user_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{user_id}/topics",
    response_model=List[schemas.Topic],
    summary="Get user's followed topics",
    responses={
        200: {
            "model": List[schemas.Topic],
            "description": "User's topics successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's topics",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_user_topics(
    user_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only get your own user information.",
            )
    try:
        user = crud.user.read(db=db, obj_id=user_id)
        return user.topics
    except ObjectNotFoundException:
        raise HTTPException(status_code=404, detail=f"User not found for id: {user_id}")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{user_id}/follow/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a topic",
    responses={
        204: {"description": "Topic successfully followed"},
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to follow topics for this user",
        },
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def follow_topic(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> None:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only retrieve your own user information.",
            )
    try:
        crud.user.follow_topic(db, user_id, topic_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{user_id}/unfollow/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a topic",
    responses={
        204: {"description": "Topic successfully unfollowed"},
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to unfollow topics for this user",
        },
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def unfollow_topic(
    user_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> None:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own user information.",
            )
    try:
        crud.user.unfollow_topic(db, user_id, topic_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

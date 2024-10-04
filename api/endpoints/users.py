from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..schemas import UserCreateInput
from ..security import (
    get_current_user_or_verify_system_token,
    get_user_create_with_hashed_password,
    verify_system_token,
)

router = APIRouter()


@router.post(
    "/users",
    response_model=schemas.User,
    summary="Add a new user",
    description="Add a new user to the system. This endpoint is restricted to system token authentication only.",
    responses={
        200: {"description": "User successfully created"},
        400: {"description": "Email already registered"},
        403: {"description": "Only system token can create users"},
    },
)
async def add_user(
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


@router.put(
    "/users",
    response_model=schemas.User,
    summary="Update user information",
    description="Update an existing user's information. Users can only update their own information unless authenticated with a system token.",
    responses={
        200: {"description": "User information successfully updated"},
        403: {"description": "Unauthorized to update this user's information"},
        404: {"description": "User not found"},
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


@router.get(
    "/users/{user_id}",
    response_model=schemas.User,
    summary="Get user information",
    description="Retrieve a user's information by their ID. Users can only retrieve their own information unless authenticated with a system token.",
    responses={
        200: {"description": "User information successfully retrieved"},
        403: {"description": "Unauthorized to retrieve this user's information"},
        404: {"description": "User not found"},
    },
)
async def get_user(
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


@router.delete(
    "/users/{user_id}",
    summary="Delete a user",
    description="Delete a user from the system. This endpoint is restricted to system token authentication only.",
    responses={
        200: {"description": "User successfully deleted"},
        403: {"description": "Only system token can delete users"},
        404: {"description": "User not found"},
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


@router.get("/users/{user_id}/topics", response_model=List[schemas.Topic])
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


@router.post("/users/{user_id}/follow/{topic_id}")
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


@router.post("/users/{user_id}/unfollow/{topic_id}")
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

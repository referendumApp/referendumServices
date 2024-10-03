from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.database.referendum import crud, schemas, models

from ..database import get_db
from ..security import get_password_hash, get_current_user_or_verify_system_token

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
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can create users.")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


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
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.email != user.email:
            raise HTTPException(status_code=403, detail="You can only update your own user information.")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        hashed_password = get_password_hash(user.password)
        db_user.hashed_password = hashed_password
        db_user.name = user.name
        return crud.update_user(db=db, db_user=db_user)
    raise HTTPException(status_code=404, detail=f"User not found for email: {user.email}.")


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
    user_id: int, db: Session = Depends(get_db), auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> models.User:
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="You can only retrieve your own user information.")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return db_user


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
    user_id: int, db: Session = Depends(get_db), auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> None:
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can delete users.")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return crud.delete_user(db, user_id=user_id)

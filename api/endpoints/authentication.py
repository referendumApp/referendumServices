from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict

from common.database.referendum import schemas, crud

from ..database import get_db
from ..schemas import ErrorResponse, TokenResponse, UserCreateInput
from ..security import (
    get_password_hash,
    authenticate_user,
    get_user_create_with_hashed_password,
)


router = APIRouter()


@router.post(
    "/signup",
    response_model=schemas.User,
    responses={
        201: {"model": schemas.User, "description": "Successfully created user"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
    summary="User Signup",
    description="Create a new user account with the provided password.",
    status_code=status.HTTP_201_CREATED,
)
async def signup(user: UserCreateInput, db: Session = Depends(get_db)) -> schemas.User:
    db_user = crud.user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_create = get_user_create_with_hashed_password(user)

    return crud.user.create(db=db, obj_in=user_create)


@router.post(
    "/token",
    response_model=TokenResponse,
    responses={
        200: {"model": TokenResponse, "description": "Successful authentication"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
    summary="Login for Access Token",
    description="Authenticate a user and return an access token.",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Dict[str, str]:
    try:
        _ = authenticate_user(db, form_data.username, form_data.password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User tokens are not yet available",
    )
    # access_token = create_access_token(data={"sub": user.email})
    # return {"access_token": access_token, "token_type": "bearer"}

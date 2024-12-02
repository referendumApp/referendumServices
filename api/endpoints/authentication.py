import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from common.database.referendum import crud, schemas
from common.database.referendum.crud import (
    DatabaseException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)

from ..database import get_db
from ..schemas import ErrorResponse, TokenResponse, UserCreateInput
from ..security import (
    SecurityException,
    authenticate_user,
    create_access_token,
    get_user_create_with_hashed_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/signup",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="User Signup",
    responses={
        201: {"model": schemas.User, "description": "Successfully created user"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def signup(user: UserCreateInput, db: Session = Depends(get_db)) -> schemas.User:
    logger.info(f"Signup attempt for email: {user.email}")
    try:
        user_create = get_user_create_with_hashed_password(user)
        created_user = crud.user.create(db=db, obj_in=user_create)
        logger.info(f"User created successfully: {created_user.email}")
        return created_user
    except ObjectAlreadyExistsException:
        logger.warning(f"Signup failed: Email already registered - {user.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "field": "email",
                "message": "Email already registered",
            },
        )
    except DatabaseException as e:
        logger.error(f"Database error during user signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login for Access Token",
    responses={
        200: {"model": TokenResponse, "description": "Successful authentication"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Dict[str, str]:
    logger.info(f"Login attempt for username: {form_data.username}")
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        access_token = create_access_token(data={"sub": user.email})
        logger.info(f"Login successful for user: {user.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except ObjectNotFoundException:
        logger.warning(f"Login failed: User not found - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "field": "username",
                "message": f"User not found - {form_data.username}",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except SecurityException:
        logger.warning(f"Login failed: Incorrect password for user - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "field": "password",
                "message": f"Incorrect password for user - {form_data.username}",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DatabaseException as e:
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )

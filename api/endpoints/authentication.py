import logging
from typing import Dict
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests

from common.database.referendum import crud, schemas
from common.database.referendum.crud import (
    DatabaseException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)

from ..constants import AuthProvider
from ..database import get_db
from ..schemas.users import UserCreateInput, RefreshToken, SocialLoginRequest, SocialLoginResponse, TokenResponse
from ..schemas.interactions import FormErrorResponse, ErrorResponse
from ..security import (
    CredentialsException,
    FormException,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    get_user_create_with_hashed_password,
    get_social_user_create,
    verify_password,
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
        409: {"model": FormErrorResponse, "description": "User already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def signup(user: UserCreateInput, db: Session = Depends(get_db)) -> schemas.User:
    logger.info(f"Signup attempt for email: {user.email}")
    try:
        created_user = crud.user.get_user_by_email(db=db, email=user.email)
        if created_user and created_user.settings.get("deleted"):
            crud.user.update_soft_delete(db=db, user_id=created_user.id, deleted=False)
            if not verify_password(user.password, created_user.hashed_password):
                hashed_password = get_password_hash(user.password)
                crud.user.update_user_password(
                    db=db, user_id=created_user.id, hashed_password=hashed_password
                )
        else:
            user_create = get_user_create_with_hashed_password(user)
            created_user = crud.user.create(db=db, obj_in=user_create)
        logger.info(f"User created successfully: {created_user.email}")
        return created_user
    except ObjectAlreadyExistsException:
        logger.warning(f"Signup failed: Email already registered - {user.email}")
        raise FormException(
            status_code=status.HTTP_409_CONFLICT, field="email", message="Email already registered"
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
        401: {"model": FormErrorResponse, "description": "Unauthorized"},
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
        refresh_token = create_refresh_token(data={"sub": user.email})
        logger.info(f"Login successful for user: {user.email}")
        return {
            "user_id": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except (CredentialsException, ObjectNotFoundException) as e:
        logger.warning(f"Login failed with exception {e} for user: {form_data.username}")
        raise FormException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            field="username",
            message="Username or password not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DatabaseException as e:
        logger.error(f"Database error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
    responses={
        200: {"model": TokenResponse, "description": "Successfully refreshed token"},
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def refresh_access_token(
    refresh_token: RefreshToken, db: Session = Depends(get_db)
) -> Dict[str, str]:
    try:
        token = decode_token(refresh_token.refresh_token)
        if token.get("type") != "refresh":
            raise CredentialsException("Invalid token type")

        email = token.get("sub")
        if email is None:
            raise CredentialsException("Invalid token: missing user identifier")

        user = crud.user.get_user_by_email(db, email)
        if not user:
            raise CredentialsException("Invalid token: user not found")

        access_token = create_access_token(data={"sub": email})
        new_refresh_token = create_refresh_token(data={"sub": email})

        logger.info(f"Token refreshed successfully for user: {email}")
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    except JWTError as e:
        logger.warning(f"Invalid or expired token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except CredentialsException as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except DatabaseException as e:
        logger.error(f"Database error during token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )
    except Exception as e:
        message = f"Failed to refresh token: {str(e)}"
        logger.warning(message)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post(
        f"/{AuthProvider.GOOGLE.value}",
        response_model=TokenResponse,
)  # To-Do: do we need a new type of response to account for differentiating between an email user and social user?
async def google_login(
    user: SocialLoginRequest,
    db: Session = Depends(get_db)
):
    # Verify the social provider token first
    # Find user in our database or create user in our system if they don't exist
    # Create JWT session token and return the token

    # To-Do: handle when verification with authentication server fails
    try:
        id_info = verify_oauth2_token(
            user.id_token,
            requests.Request(),
            os.getenv("GOOGLE_CLOUD_WEB_CLIENT_ID"),
            clock_skew_in_seconds = 60  # Prevents token used too early error by allowing x amount of seconds inconsistency between google and referendum servers's system clock
            )
        # To-Do: Handle when name or email is empty
        google_user_id = id_info.get('sub')

        # Check if user exists based off social provider
        user = crud.user.get_user_by_social_provider(db=db, social_provider_user_id=google_user_id, social_provider_name=AuthProvider.GOOGLE.value)
            # handle case if the user was previously deleted
        
        if not user:
            user_data = {
                'email': id_info.get("email"),
                "name": id_info.get("name"),
                "settings": {
                    "social_provider_user_id": google_user_id, 
                    'social_provider_name': AuthProvider.GOOGLE.value
                }
            }
            user_create = get_social_user_create(user_data)
            user = crud.user.create(db=db, obj_in=user_create)
            logger.info(f"User created from {AuthProvider.GOOGLE.value} successfully: {user.email}")
            # To-Do: We should return a 201 if a user is created via social provider account instead of 200.

        # Return login response
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        logger.info(f"Login successful for user: {user.email}")
        return {
            "user_id": user.id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except DatabaseException as e:
        logger.error(f"Database error during social login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )   

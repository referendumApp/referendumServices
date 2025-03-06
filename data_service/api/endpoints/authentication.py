import logging
from typing import Dict
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from google.oauth2.id_token import verify_oauth2_token
from google.auth.transport import requests

from common.database.referendum import crud, schemas
from common.database.referendum.crud import DatabaseException, ObjectNotFoundException

from ..constants import AuthProvider, PlatformType
from ..database import get_db
from ..schemas.interactions import ErrorResponse, FormErrorResponse
from ..schemas.users import (
    RefreshToken,
    GoogleUserAuthRequest,
    TokenResponse,
    UserCreateInput,
)
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
        existing_user = crud.user.get_user_by_email(db=db, email=user.email)
        if existing_user.settings.get("deleted"):
            logger.info(f"Reactivating soft deleted user for email {user.email}")
            crud.user.update_soft_delete(db=db, user_id=existing_user.id, deleted=False)
            if not verify_password(user.password, existing_user.hashed_password):
                hashed_password = get_password_hash(user.password)
                crud.user.update_user_password(
                    db=db, user_id=existing_user.id, hashed_password=hashed_password
                )
            return existing_user
        else:
            logger.error(f"Signup failed: Email already registered - {user.email}")
            raise FormException(
                status_code=status.HTTP_409_CONFLICT,
                field="email",
                message="Email already registered",
            )
    except ObjectNotFoundException:
        user_create = get_user_create_with_hashed_password(user)
        created_user = crud.user.create(db=db, obj_in=user_create)
        logger.info(f"User created successfully: {created_user.email}")
        return created_user
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
        logger.error(f"Login failed with exception '{e}' for user: {form_data.username}")
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
            "user_id": user.id,
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


def detect_mobile_platform(platform: str) -> PlatformType:
    if PlatformType.ANDROID in platform:
        return PlatformType.ANDROID
    elif PlatformType.IOS in platform:
        return PlatformType.IOS
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")


def verify_google_token(id_token: str, http_request: Request):
    platform = detect_mobile_platform(http_request.headers.get("x-platform", ""))
    try:
        client_id = (
            os.getenv("GOOGLE_CLOUD_IOS_CLIENT_ID")
            if platform == "ios"
            else os.getenv("GOOGLE_CLOUD_ANDROID_CLIENT_ID")
        )
        google_jwt = verify_oauth2_token(
            id_token,
            requests.Request(),
            client_id,
            clock_skew_in_seconds=60,  # Prevents token used too early error by allowing x amount of seconds inconsistency between google and referendum servers's system clock
        )
    except Exception as e:
        logger.error(f"Verifying id token with Google authentication server failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server failed to verify id token with Google.",
        )

    required_fields = {"sub", "email", "name"}
    missing_fields = required_fields - google_jwt.keys()
    if missing_fields:
        logger.error(f"Missing required fields from Google authentication server: {missing_fields}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing required fields from Google authentication server: {', '.join(missing_fields)}",
        )
    return google_jwt


@router.post(
    f"/{AuthProvider.GOOGLE.value}/signup",
    response_model=TokenResponse,
)
async def google_signup(
    user_auth_request: GoogleUserAuthRequest, http_request: Request, db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Creates or links a Referendum user account with a Google account and logs them in.
    """
    id_info = verify_google_token(user_auth_request.id_token, http_request)
    google_user_id = id_info.get("sub")
    user_email = id_info.get("email")
    social_provider_dict = {AuthProvider.GOOGLE.user_id_field: google_user_id}

    try:
        # Find user by email regardless of how they were originally created
        user_with_matching_email = crud.user.get_user_by_email(
            db=db, email=user_email
        )  # Throws ObjectNotFoundException if not found
        # Find user by Google ID connection
        user_linked_to_google_id = crud.user.get_user_by_social_provider(
            db=db,
            social_provider_dict=social_provider_dict,
        )

        # Email matched but not yet linked to this Google ID
        if not user_linked_to_google_id:
            user = user_with_matching_email
            crud.user.update_social_provider(
                db=db, user_id=user.id, social_provider_dict=social_provider_dict
            )
            logger.info(f"Added Google connection to existing user: {user.email}")

        # User already linked to this Google ID
        else:
            user = user_linked_to_google_id
            if user.settings.get("deleted") is True:
                logger.info(f"Reactivating soft deleted user for email {user.email}")
                crud.user.update_soft_delete(db=db, user_id=user.id, deleted=False)
            else:
                logger.error(f"Signup failed: Google account already registered - {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Your Google account is already signed up. Please login instead.",
                )
    except ObjectNotFoundException:
        # No matching user records - create new user with Google credentials
        user_data = {
            "email": user_email,
            "name": id_info.get("name"),
            "settings": social_provider_dict,
        }
        user_create = get_social_user_create(user_data)
        user = crud.user.create(db=db, obj_in=user_create)
        logger.info(f"User created from {AuthProvider.GOOGLE.value} successfully: {user.email}")
    except DatabaseException as e:
        logger.error(f"Database error during social login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error",
        )

    # Generate tokens for the authenticated user
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    logger.info(f"Login successful for user: {user.email}")

    return {
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post(
    f"/{AuthProvider.GOOGLE.value}/login",
    response_model=TokenResponse,
)
async def google_login(
    user_auth_request: GoogleUserAuthRequest, http_request: Request, db: Session = Depends(get_db)
) -> Dict[str, str]:
    id_info = verify_google_token(user_auth_request.id_token, http_request)
    google_user_id = id_info.get("sub")
    social_provider_dict = {AuthProvider.GOOGLE.user_id_field: google_user_id}

    try:
        user = crud.user.get_user_by_social_provider(
            db=db,
            social_provider_dict=social_provider_dict,
        )
        if not user:
            logger.error(
                f"Login failed. User must create an account first. Google token= {id_info}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed. Please create an account first.",
            )
        elif user.settings.get("deleted") is True:
            logger.info(f"Reactivating soft deleted user for email {user.email}")
            crud.user.update_soft_delete(db=db, user_id=user.id, deleted=False)
    except DatabaseException as e:
        logger.error(f"Database error during social login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error",
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    logger.info(f"Login successful for user: {user.email}")

    return {
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

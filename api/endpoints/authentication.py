import boto3
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Dict

from common.database.referendum import schemas, crud, models
from common.database.referendum.crud import (
    DatabaseException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)
from ..config import settings
from ..database import get_db
from ..schemas import (
    ErrorResponse,
    FormErrorResponse,
    RefreshToken,
    TokenResponse,
    UserCreateInput,
    PasswordResetRequest,
    PasswordResetData,
)
from ..security import (
    CredentialsException,
    FormException,
    authenticate_user,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_create_with_hashed_password,
)


logger = logging.getLogger(__name__)

router = APIRouter()

ses = boto3.client("ses", region_name=settings.AWS_REGION)


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
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except FormException as e:
        logger.warning(f"Login failed with exception: {e}")
        raise e
    except ObjectNotFoundException as e:
        logger.warning(f"Login failed with exception {e} for user: {form_data.username}")
        raise FormException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            field="username",
            message=f"User not found - {form_data.username}",
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
        token = await decode_token(refresh_token.refresh_token)
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


def send_password_reset_email(email: str, reset_token: str) -> None:
    """Send password reset email using AWS SES."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    message = MIMEMultipart()
    message["Subject"] = "Password Reset Request"
    message["From"] = settings.SYSTEM_EMAIL
    message["To"] = email

    html_content = f"""
    <html>
        <body>
            <p>A password reset was requested for your account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>If you didn't request this, please ignore this email.</p>
            <p>This link will expire in 30 minutes.</p>
        </body>
    </html>
    """

    message.attach(MIMEText(html_content, "html"))

    try:
        ses.send_raw_email(
            Source=settings.SYSTEM_EMAIL,
            Destinations=[email],
            RawMessage={"Data": message.as_string()},
        )
        logger.info(f"Password reset email sent to: {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        )


@router.post(
    "/request-reset",
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
    responses={
        200: {"description": "Reset email sent if email exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def request_password_reset(
    request: PasswordResetRequest, db: Session = Depends(get_db)
) -> dict:
    """Request a password reset token."""
    try:
        user = crud.user.get_user_by_email(db, request.email)
        if user:
            # Create a special JWT token for password reset
            reset_token = create_access_token(
                data={"sub": user.email, "type": "password_reset"},
                expires_delta=timedelta(minutes=30),
            )
            await send_password_reset_email(user.email, reset_token)

        # Always return success to prevent email enumeration
        logger.info(f"Password reset requested for: {request.email}")
        return {"message": "If the email exists, a password reset link has been sent"}

    except Exception as e:
        logger.error(f"Error in password reset request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password reset request",
        )


@router.post(
    "/reset-password",
    response_model=schemas.User,
    summary="Reset Password",
    responses={
        200: {"model": schemas.User, "description": "Password successfully reset"},
        400: {"model": ErrorResponse, "description": "Invalid token or password"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def reset_password(
    reset_data: PasswordResetData, db: Session = Depends(get_db)
) -> models.User:
    """Reset password using the reset token."""
    try:
        # Verify the reset token
        payload = jwt.decode(reset_data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != "password_reset":
            logger.warning("Invalid token type used for password reset")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        email = payload.get("sub")
        if not email:
            logger.warning("Token missing email claim")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        user = crud.user.get_user_by_email(db, email)
        if not user:
            logger.warning(f"User not found for reset token: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        # Update the password
        hashed_password = get_password_hash(reset_data.new_password)
        user = crud.user.update(db=db, db_obj=user, obj_in={"hashed_password": hashed_password})

        logger.info(f"Password successfully reset for user: {email}")
        return user

    except JWTError:
        logger.warning("Invalid or expired reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
        )
    except Exception as e:
        logger.error(f"Error in password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password reset",
        )

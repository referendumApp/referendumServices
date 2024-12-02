import logging
from datetime import datetime, timedelta
from fastapi import Security, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from common.database.referendum import models, crud, schemas

from api.config import settings
from api.database import get_db
from api.schemas import UserCreateInput

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
api_key_header = APIKeyHeader(name="X-API_Key", auto_error=False)


class CredentialsException(HTTPException):
    def __init__(self, detail: str):
        self.status_code = status.HTTP_401_UNAUTHORIZED
        self.detail = detail
        self.headers = {"WWW-Authenticate": "Bearer"}

        logger.error(self.detail)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def authenticate_user(db: Session, email: str, password: str) -> models.User:
    try:
        user = crud.user.get_user_by_email(db, email)
        if not verify_password(password, user.hashed_password):
            raise CredentialsException(f"Unable to authorize user with email: {email}")
        logger.info(f"Successful login for user: {email}")
        return user
    except crud.DatabaseException as e:
        raise CredentialsException(f"Database error during authentication: {str(e)}")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Access token created for user: {data.get('sub')}")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"Refresh token created for user: {data.get('sub')}")
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    if not token:
        raise CredentialsException("No token provided")

    payload = decode_token(token)
    if not payload:
        raise CredentialsException("Decoded token returned None")

    if payload.get("type") != "access":
        raise CredentialsException("Invalid token type for access token")

    email: str = payload.get("sub")
    if not email:
        raise CredentialsException("Missing email in access token")

    try:
        user = crud.user.get_user_by_email(db, email)
        if not user:
            raise CredentialsException(f"User not found for email: {email}")
        return user
    except Exception as e:
        raise CredentialsException(f"Error retrieving user: {str(e)}")


async def get_current_user_or_verify_system_token(
    api_key: str = Security(api_key_header),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    if api_key:
        if api_key == settings.API_ACCESS_TOKEN:
            logger.info("System token used for authentication")
            return {"is_system": True}
        else:
            raise CredentialsException("Invalid API key provided")
    if token:
        try:
            user = await get_current_user(token, db)
            logger.info(f"User authenticated: {user.email}")
            return {"is_system": False, "user": user}
        except crud.ObjectNotFoundException:
            raise CredentialsException("Could not find user for provided token")
        except crud.DatabaseException as e:
            logger.error(f"Database error during user authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}",
            )
    raise CredentialsException("No valid authentication provided")


async def verify_system_token(api_key: str = Security(api_key_header)):
    if api_key != settings.API_ACCESS_TOKEN:
        logger.warning("Invalid system token used")
        raise HTTPException(status_code=403, detail="Only system token can perform this action.")
    logger.info("System token verified")


def get_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


def get_user_create_with_hashed_password(user: UserCreateInput) -> schemas.UserCreate:
    user_data = user.model_dump()
    password = user_data.pop("password")
    hashed_password = get_password_hash(password)

    return schemas.UserCreate(**user_data, hashed_password=hashed_password)

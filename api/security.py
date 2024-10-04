from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status

from common.database.referendum import models, crud, schemas

from api.config import settings
from api.database import get_db
from api.schemas import TokenData, UserCreateInput

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class SecurityException(Exception):
    """Base exception for security operations"""

    pass


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> models.User:
    try:
        user = crud.user.get_user_by_email(db, email)
        if not verify_password(password, user.hashed_password):
            raise SecurityException(f"Unable to authorize user with email: {email}")
        return user
    except crud.DatabaseException as e:
        raise SecurityException(f"Database error during authentication: {str(e)}")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise CREDENTIALS_EXCEPTION
        token_data = TokenData(email=email)
    except JWTError:
        raise CREDENTIALS_EXCEPTION
    user = crud.user.get_user_by_email(db, token_data.email)
    return user


async def get_current_user_or_verify_system_token(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    if token == settings.API_ACCESS_TOKEN:
        return {"is_system": True}
    try:
        user = await get_current_user(token, db)
        return {"is_system": False, "user": user}
    except crud.ObjectNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not find user for credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except crud.DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


def get_token(token: str = Depends(oauth2_scheme)) -> str:
    return token


def get_user_create_with_hashed_password(user: UserCreateInput) -> schemas.UserCreate:
    user_data = user.model_dump()
    password = user_data.pop("password")
    hashed_password = get_password_hash(password)

    return schemas.UserCreate(**user_data, hashed_password=hashed_password)

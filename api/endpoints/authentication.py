from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Dict

from common.database.referendum import schemas, models, crud

from ..config import settings
from ..database import get_db
from ..schemas import ErrorResponse, TokenResponse, TokenData


# Utilities


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> models.User:
    user = crud.get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise Exception(f"Unable to authorize user with email: {email}")
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = crud.get_user_by_email(db, token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_or_verify_system_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token == settings.API_ACCESS_TOKEN:
        return {"is_system": True}
    try:
        user = await get_current_user(token, db)
        return {"is_system": False, "user": user}
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token(token: str = Depends(oauth2_scheme)):
    return token


# Endpoints


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
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.User:
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


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
        user = authenticate_user(db, form_data.username, form_data.password)
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="User tokens are not yet available")
    # access_token = create_access_token(data={"sub": user.email})
    # return {"access_token": access_token, "token_type": "bearer"}

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..schemas import UserCreateInput, ErrorResponse
from ..security import (
    get_current_user,
    get_current_user_or_verify_system_token,
    get_user_create_with_hashed_password,
    verify_system_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new user",
    responses={
        201: {"model": schemas.User, "description": "User successfully created"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can create users",
        },
        409: {"model": ErrorResponse, "description": "Email already registered"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_user(
    user: UserCreateInput,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.User:
    logger.info(f"Attempting to create new user with email: {user.email}")
    try:
        user_create = get_user_create_with_hashed_password(user)
        created_user = crud.user.create(db=db, obj_in=user_create)
        logger.info(f"Successfully created user with ID: {created_user.id}")
        return created_user
    except ObjectAlreadyExistsException:
        logger.warning(f"Attempt to create user with existing email: {user.email}")
        raise HTTPException(
            status_code=409, detail=f"Email already registered: {user.email}"
        )
    except DatabaseException as e:
        logger.error(f"Database error while creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Get user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    logger.info(f"Attempting to read user information for user ID: {user_id}")
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            logger.warning(
                f"Unauthorized attempt to access user info: User {current_user.id} tried to access User {user_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="You can only retrieve your own user information.",
            )
    try:
        user = crud.user.read(db=db, obj_id=user_id)
        logger.info(f"Successfully retrieved information for user ID: {user_id}")
        return user
    except ObjectNotFoundException:
        logger.warning(f"Attempt to read non-existent user with ID: {user_id}")
        raise HTTPException(status_code=404, detail=f"User not found for id: {user_id}")
    except DatabaseException as e:
        logger.error(f"Database error while reading user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.User,
    summary="Update user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully updated",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_user(
    user: UserCreateInput,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    logger.info(f"Attempting to update user information for email: {user.email}")
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.email != user.email:
            logger.warning(
                f"Unauthorized attempt to update user info: User {current_user.email} tried to update User {user.email}"
            )
            raise HTTPException(
                status_code=403, detail="You can only update your own user information."
            )
    try:
        db_user = crud.user.get_user_by_email(db, email=user.email)
        user_create = get_user_create_with_hashed_password(user)
        updated_user = crud.user.update(db=db, db_obj=db_user, obj_in=user_create)
        logger.info(f"Successfully updated information for user ID: {updated_user.id}")
        return updated_user
    except ObjectNotFoundException:
        logger.warning(f"Attempt to update non-existent user with email: {user.email}")
        raise HTTPException(
            status_code=404, detail=f"User not found for email: {user.email}."
        )
    except DatabaseException as e:
        logger.error(f"Database error while updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        204: {"description": "User successfully deleted"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can delete users",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to delete user with ID: {user_id}")
    try:
        crud.user.delete(db=db, obj_id=user_id)
        logger.info(f"Successfully deleted user with ID: {user_id}")
        return
    except ObjectNotFoundException:
        logger.warning(f"Attempt to delete non-existent user with ID: {user_id}")
        raise HTTPException(
            status_code=404, detail=f"User not found for ID: {user_id}."
        )
    except DatabaseException as e:
        logger.error(f"Database error while deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{user_id}/topics",
    response_model=List[schemas.Topic],
    summary="Get user's followed topics",
    responses={
        200: {
            "model": List[schemas.Topic],
            "description": "User's topics successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's topics",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_user_topics(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Topic]:
    logger.info(f"Attempting to retrieve topics for user ID: {user.id}")
    try:
        topics = crud.user.get_user_topics(db=db, user_id=user.id)
        logger.info(
            f"Successfully retrieved {len(topics)} topics for user ID: {user.id}"
        )
        return topics
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{user_id}/bills",
    response_model=List[schemas.Bill],
    summary="Get user's followed bills",
    responses={
        200: {
            "model": List[schemas.Bill],
            "description": "User's bills successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's bills",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_user_bills(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Bill]:
    logger.info(f"Attempting to retrieve bills for user ID: {user.id}")
    try:
        bills = crud.user.get_user_bills(db=db, user_id=user.id)
        logger.info(f"Successfully retrieved {len(bills)} bills for user ID: {user.id}")
        return bills
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user bills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

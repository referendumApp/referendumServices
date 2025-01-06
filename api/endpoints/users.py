import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..schemas import UserCreateInput, UserUpdateInput, ErrorResponse
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
        logger.warning(f"Attempted to create user with existing email: {user.email}")
        raise HTTPException(status_code=409, detail=f"Email already registered: {user.email}")
    except DatabaseException as e:
        logger.error(f"Database error while creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/admin/{user_id}",
    response_model=schemas.User,
    summary="Get user information with system token",
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
async def admin_read_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(verify_system_token),
) -> models.User:
    try:
        user = crud.user.read(db=db, obj_id=user_id)
        logger.info(f"Successfully retrieved information for user ID: {user_id}")
        return user
    except ObjectNotFoundException:
        logger.warning(f"Attempted to read non-existent user with ID: {user_id}")
        raise HTTPException(status_code=404, detail=f"User not found for id: {user_id}")
    except DatabaseException as e:
        logger.error(f"Database error while reading user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/",
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
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.User:
    try:
        user = crud.user.read(db=db, obj_id=user.id)
        logger.info(f"Successfully retrieved information for user ID: {user.id}")
        return user
    except ObjectNotFoundException:
        logger.warning(f"Attempted to read non-existent user with ID: {user.id}")
        raise HTTPException(status_code=404, detail=f"User not found for id: {user.id}")
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
    user: UserUpdateInput,
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
        raise HTTPException(status_code=404, detail=f"User not found for email: {user.email}.")
    except DatabaseException as e:
        logger.error(f"Database error while updating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/admin/{user_id}",
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
async def admin_delete_user(
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
        raise HTTPException(status_code=404, detail=f"User not found for ID: {user_id}.")
    except DatabaseException as e:
        logger.error(f"Database error while deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/",
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
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"Attempting to delete user with ID: {user.id}")
    try:
        crud.user.delete(db=db, obj_id=user.id)
        logger.info(f"Successfully deleted user with ID: {user.id}")
        return
    except ObjectNotFoundException:
        logger.warning(f"Attempt to delete non-existent user with ID: {user.id}")
        raise HTTPException(status_code=404, detail=f"User not found for ID: {user.id}.")
    except DatabaseException as e:
        logger.error(f"Database error while deleting user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/topics",
    response_model=List[schemas.Topic.Record],
    summary="Get user's followed topics",
    responses={
        200: {
            "model": List[schemas.Topic.Record],
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
    try:
        logger.info(f"Attempting to retrieve topics for user ID: {user.id}")
        topics = crud.user.get_user_topics(db=db, user_id=user.id)
        logger.info(f"Successfully retrieved {len(topics)} topics for user ID: {user.id}")
        return topics
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/bills",
    response_model=List[schemas.Bill.Record],
    summary="Get user's followed bills",
    responses={
        200: {
            "model": List[schemas.Bill.Record],
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


@router.get(
    "/legislators",
    response_model=List[schemas.Legislator.Record],
    summary="Get user's followed legislators",
    responses={
        200: {
            "model": List[schemas.Legislator.Record],
            "description": "User's legislators successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's legislators",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def get_user_legislators(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Legislator]:
    logger.info(f"Attempting to retrieve legislators for user ID: {user.id}")
    try:
        legislators = crud.user.get_user_legislators(db=db, user_id=user.id)
        logger.info(f"Successfully retrieved {len(legislators)} legislators for user ID: {user.id}")
        return legislators
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user legislators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/votes",
    response_model=schemas.UserVote,
    summary="Cast vote",
    responses={
        200: {
            "model": schemas.UserVote,
            "description": "Vote updated successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def cast_vote(
    vote: schemas.UserVoteCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.UserVote:
    try:
        user_vote = schemas.UserVote(**vote.model_dump(), user_id=user.id)
        return crud.user_vote.cast_vote(db=db, vote=user_vote)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/admin/{user_id}/votes",
    response_model=List[schemas.UserVote],
    summary="Get votes for user",
    responses={
        200: {
            "model": List[schemas.UserVote],
            "description": "List of votes retrieved successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def admin_get_user_votes(
    user_id: int,
    bill_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> List[models.UserVote]:
    try:
        return crud.user_vote.get_votes_for_user(db=db, user_id=user_id, bill_id=bill_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/votes",
    response_model=List[schemas.UserVote],
    summary="Get votes for user",
    responses={
        200: {
            "model": List[schemas.UserVote],
            "description": "List of votes retrieved successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_user_votes(
    bill_id: Optional[int] = Query(None, alias="billId"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[models.UserVote]:
    try:
        return crud.user_vote.get_votes_for_user(db=db, user_id=user.id, bill_id=bill_id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/votes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uncast vote",
    responses={
        204: {"description": "Vote deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def uncast_vote(
    bill_id: int = Query(alias="billId"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    try:
        return crud.user_vote.uncast_vote(db=db, bill_id=bill_id, user_id=user.id)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/bills/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a bill",
    responses={
        204: {"description": "Bill successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def follow_bill(
    bill_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to follow bill {bill_id}")
    try:
        crud.user.follow_bill(db=db, user_id=user.id, bill_id=bill_id)
        logger.info(f"User {user.id} successfully followed bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error following bill: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while following bill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/bills/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a bill",
    responses={
        204: {"description": "Bill successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def unfollow_bill(
    bill_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to unfollow bill {bill_id}")
    try:
        crud.user.unfollow_bill(db=db, user_id=user.id, bill_id=bill_id)
        logger.info(f"User {user.id} successfully unfollowed bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error unfollowing bill: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while unfollowing bill: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/legislators/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a legislator",
    responses={
        204: {"description": "Legislator successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def follow_legislator(
    legislator_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to follow legislator {legislator_id}")
    try:
        crud.user.follow_legislator(db=db, user_id=user.id, legislator_id=legislator_id)
        logger.info(f"User {user.id} successfully followed legislator {legislator_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error following legislator: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while following legislator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/legislators/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a legislator",
    responses={
        204: {"description": "Legislator successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def unfollow_legislator(
    legislator_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to unfollow legislator {legislator_id}")
    try:
        crud.user.unfollow_legislator(db=db, user_id=user.id, legislator_id=legislator_id)
        logger.info(f"User {user.id} successfully unfollowed legislator {legislator_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error unfollowing legislator: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while unfollowing legislator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a topic",
    responses={
        204: {"description": "Topic successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def follow_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to follow topic {topic_id}")
    try:
        crud.user.follow_topic(db=db, user_id=user.id, topic_id=topic_id)
        logger.info(f"User {user.id} successfully followed topic {topic_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error following topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while following topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a topic",
    responses={
        204: {"description": "Topic successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def unfollow_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"User {user.id} attempting to unfollow topic {topic_id}")
    try:
        crud.user.unfollow_topic(db=db, user_id=user.id, topic_id=topic_id)
        logger.info(f"User {user.id} successfully unfollowed topic {topic_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error unfollowing topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while unfollowing topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from common.database.referendum import crud, models
from common.database.referendum.crud import ObjectNotFoundException, DatabaseException

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user

# Set up logger for this module
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/bill/{bill_id}",
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
    "/bill/{bill_id}",
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
    "/legislator/{legislator_id}",
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
    "/legislator/{legislator_id}",
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
        crud.user.unfollow_legislator(
            db=db, user_id=user.id, legislator_id=legislator_id
        )
        logger.info(
            f"User {user.id} successfully unfollowed legislator {legislator_id}"
        )
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error unfollowing legislator: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while unfollowing legislator: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/topic/{topic_id}",
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
    "/topic/{topic_id}",
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

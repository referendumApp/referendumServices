from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from common.database.referendum import crud, models
from common.database.referendum.crud import ObjectNotFoundException, DatabaseException

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user

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
    try:
        crud.user.follow_bill(db=db, user_id=user.id, bill_id=bill_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
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
    try:
        crud.user.unfollow_bill(db=db, user_id=user.id, bill_id=bill_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
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
    try:
        crud.user.follow_topic(db=db, user_id=user.id, topic_id=topic_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error following: {str(e)}")
    except DatabaseException as e:
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
    try:
        crud.user.unfollow_topic(db=db, user_id=user.id, topic_id=topic_id)
        return
    except ObjectNotFoundException as e:
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

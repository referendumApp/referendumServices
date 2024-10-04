from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from common.database.referendum import crud, models, schemas
from common.database.referendum.crud import (
    DatabaseException,
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
)

from ..database import get_db
from ..security import get_current_user_or_verify_system_token, verify_system_token
from ..schemas import ErrorResponse


# Create new router for topic-related operations
router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Topic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new topic",
    responses={
        201: {"model": schemas.Topic, "description": "Topic successfully created"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        409: {"model": ErrorResponse, "description": "Topic already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def create_topic(
    topic: schemas.TopicCreate,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Topic:
    try:
        return crud.topic.create(db=db, obj_in=topic)
    except ObjectAlreadyExistsException:
        raise HTTPException(status_code=409, detail="Topic already exists")
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{topic_id}",
    response_model=schemas.Topic,
    summary="Get topic information",
    responses={
        200: {"model": schemas.Topic, "description": "Topic retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def read_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Topic:
    try:
        return crud.topic.read(db=db, obj_id=topic_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Topic not found for ID: {topic_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.Topic,
    summary="Update topic information",
    responses={
        200: {
            "model": schemas.Topic,
            "description": "Topic information successfully updated",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_topic(
    topic: schemas.Topic,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Topic:
    try:
        db_topic = crud.topic.read(db=db, obj_id=topic.id)
        return crud.topic.update(db=db, db_obj=db_topic, obj_in=topic)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Topic not found for ID: {topic.id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a topic",
    responses={
        204: {"description": "Topic successfully deleted"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.topic.delete(db=db, obj_id=topic_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Topic not found for ID: {topic_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/",
    response_model=List[schemas.Topic],
    summary="Get all topics",
    responses={
        200: {
            "model": List[schemas.Topic],
            "description": "Topics successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def read_topics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> List[models.Topic]:
    try:
        return crud.topic.read_all(db=db, skip=skip, limit=limit)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

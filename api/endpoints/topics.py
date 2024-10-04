from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from common.database.referendum import crud, models, schemas

from ..database import get_db


# Create new router for topic-related operations
router = APIRouter()


@router.post("/topics", response_model=schemas.Topic)
def create_new_topic(topic: schemas.TopicCreate, db: Session = Depends(get_db)):
    return crud.create_topic(db, topic)


@router.get("/topics", response_model=List[schemas.Topic])
def read_topics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_topics(db, skip, limit)


@router.post("/users/{user_id}/follow/{topic_id}")
def follow_topic_endpoint(user_id: int, topic_id: int, db: Session = Depends(get_db)):
    if crud.follow_topic(db, user_id, topic_id):
        return {"message": "Topic followed successfully"}
    raise HTTPException(status_code=404, detail="User or topic not found")


@router.post("/users/{user_id}/unfollow/{topic_id}")
def unfollow_topic_endpoint(user_id: int, topic_id: int, db: Session = Depends(get_db)):
    if crud.unfollow_topic(db, user_id, topic_id):
        return {"message": "Topic unfollowed successfully"}
    raise HTTPException(
        status_code=404,
        detail="User or topic not found, or user was not following the topic",
    )


@router.get("/users/{user_id}/topics", response_model=List[schemas.Topic])
def get_user_topics(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return user.topics
    raise HTTPException(status_code=404, detail="User not found")

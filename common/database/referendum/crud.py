from sqlalchemy.orm import Session
from typing import List, Optional, TypeVar, Type, Generic

from common.database.referendum import models, schemas

T = TypeVar("T")


class CRUDBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, obj_in: schemas.BaseModel) -> T:
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: T, obj_in: schemas.BaseModel) -> T:
        obj_data = obj_in.dict(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> None:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()


### TOPICS ###


class CRUDTopic(CRUDBase[models.Topic]):
    def follow_topic(self, db: Session, user_id: int, topic_id: int) -> bool:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if db_user and db_topic:
            db_user.topics.append(db_topic)
            db.commit()
            return True
        return False

    def unfollow_topic(self, db: Session, user_id: int, topic_id: int) -> bool:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if db_user and db_topic and topic in db_user.topics:
            db_user.topics.remove(db_topic)
            db.commit()
            return True
        return False

    def get_user_topics(
        self, db: Session, user_id: int
    ) -> Optional[List[models.Topic]]:
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        return db_user.topics if db_user else None


topic = CRUDTopic(models.Topic)


### USERS ###


class CRUDUser(CRUDBase[models.User]):
    def create_user(
        self, db: Session, user_create: schemas.UserCreate, hashed_password: str
    ) -> models.User:
        db_user = models.User(
            name=user_create.name,
            email=user_create.email,
            hashed_password=hashed_password,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.User]:
        return db.query(models.User).filter(models.User.email == email).first()


user = CRUDUser(models.User)


### BILLS ###


class CRUDBill(CRUDBase[models.Bill]):
    def get_bill_by_legiscan_id(
        self, db: Session, legiscan_id: int
    ) -> Optional[models.Bill]:
        return (
            db.query(models.Bill).filter(models.Bill.legiscan_id == legiscan_id).first()
        )


bill = CRUDBill(models.Bill)

from sqlalchemy.orm import Session
from typing import List, Optional, TypeVar, Type, Generic

from common.database.referendum import models, schemas

T = TypeVar("T")


class CRUDBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, obj_in: schemas.BaseModel) -> T:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def read(self, db: Session, obj_id: int) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == obj_id).first()

    def read_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: T, obj_in: schemas.BaseModel) -> T:
        obj_data = obj_in.model_dump(exclude_unset=True)
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, obj_id: int) -> None:
        obj = db.get(self.model, obj_id)
        if obj:
            db.delete(obj)
            db.commit()


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

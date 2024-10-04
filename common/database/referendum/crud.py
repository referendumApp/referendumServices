from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, TypeVar, Type, Generic

from common.database.referendum import models, schemas

T = TypeVar("T")


class CRUDException(Exception):
    """Base exception for CRUD operations"""

    pass


class ObjectNotFoundException(CRUDException):
    """Raised when an object is not found"""

    pass


class ObjectAlreadyExistsException(CRUDException):
    """Raised when trying to create an object that already exists"""

    pass


class DatabaseException(CRUDException):
    """Raised when a database error occurs"""

    pass


class CRUDBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, obj_in: schemas.BaseModel) -> T:
        try:
            db_obj = self.model(**obj_in.model_dump())
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            raise ObjectAlreadyExistsException("Object already exists")
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def read(self, db: Session, obj_id: int) -> T:
        db_obj = db.query(self.model).filter(self.model.id == obj_id).first()
        if db_obj is None:
            raise ObjectNotFoundException("Object not found")
        return db_obj

    def read_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: T, obj_in: schemas.BaseModel) -> T:
        if db_obj is None:
            raise ObjectNotFoundException("Object not found")
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)
            for key, value in obj_data.items():
                setattr(db_obj, key, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def delete(self, db: Session, obj_id: int) -> None:
        obj = db.get(self.model, obj_id)
        if obj is None:
            raise ObjectNotFoundException("Object not found")
        try:
            db.delete(obj)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")


class CRUDUser(CRUDBase[models.User]):
    def get_user_by_email(self, db: Session, email: str) -> models.User:
        try:
            user = db.query(models.User).filter(models.User.email == email).first()
            if user is None:
                raise ObjectNotFoundException(f"User with email {email} not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")


user = CRUDUser(models.User)


### BILLS ###


class CRUDBill(CRUDBase[models.Bill]):
    def get_bill_by_legiscan_id(self, db: Session, legiscan_id: int) -> models.Bill:
        try:
            bill = (
                db.query(models.Bill)
                .filter(models.Bill.legiscan_id == legiscan_id)
                .first()
            )
            if bill is None:
                raise ObjectNotFoundException(
                    f"Bill with legiscan_id {legiscan_id} not found"
                )
            return bill
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")


bill = CRUDBill(models.Bill)

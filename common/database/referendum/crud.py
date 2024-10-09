from sqlalchemy.orm import Session, noload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, TypeVar, Type, Generic

from common.database.referendum import models, schemas

T = TypeVar("T")


class CRUDException(Exception):
    pass


class ObjectNotFoundException(CRUDException):
    pass


class ObjectAlreadyExistsException(CRUDException):
    pass


class DatabaseException(CRUDException):
    pass


class NullValueException(Exception):
    pass


class BaseCRUD(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def create(self, db: Session, obj_in: schemas.BaseModel) -> T:
        try:
            obj_data = obj_in.model_dump()
            for field, value in obj_data.items():
                if (
                    value is None
                    and self.model.__table__.columns[field].nullable is False
                ):
                    raise NullValueException(
                        f"Null value provided for non-nullable field: {field}"
                    )

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            if "unique constraint" in str(e).lower():
                raise ObjectAlreadyExistsException("Object already exists")
            raise DatabaseException(f"Integrity error: {str(e)}")
        except NullValueException as e:
            db.rollback()
            raise e
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


class BillCRUD(BaseCRUD[models.Bill]):
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


class LegislatorCRUD(BaseCRUD[models.Legislator]):
    pass


class LegislativeBodyCRUD(BaseCRUD[models.LegislativeBody]):
    pass


class PartyCRUD(BaseCRUD[models.Party]):
    pass


class RoleCRUD(BaseCRUD[models.Role]):
    pass


class StateCRUD(BaseCRUD[models.State]):
    pass


class TopicCRUD(BaseCRUD[models.Topic]):
    pass


class UserCRUD(BaseCRUD[models.User]):
    def get_user_by_email(self, db: Session, email: str) -> models.User:
        try:
            user = (
                db.query(models.User)
                # TODO - reenable this to avoid querying all relationships on authentication
                # .options(noload(models.User.topics), noload(models.User.bills))
                .filter(models.User.email == email).first()
            )
            if user is None:
                raise ObjectNotFoundException(f"User with email {email} not found")
            return user
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")

    def follow_topic(self, db: Session, user_id: int, topic_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if not db_topic:
            raise ObjectNotFoundException(f"Topic not found for id: {topic_id}")
        db_user.followed_topics.append(db_topic)
        db.commit()

    def unfollow_topic(self, db: Session, user_id: int, topic_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if not db_topic:
            raise ObjectNotFoundException(f"Topic not found for id: {topic_id}")
        if db_topic not in db_user.followed_topics:
            raise ObjectNotFoundException(
                f"Cannot unfollow, User {user_id} is not following topic {topic_id}"
            )
        db_user.followed_topics.remove(db_topic)
        db.commit()

    def get_user_topics(self, db: Session, user_id: int) -> List[models.Topic]:
        try:
            db_user = db.query(models.User).filter(models.User.id == user_id).first()
            if user is None:
                raise ObjectNotFoundException(f"User not found for id: {user_id}")
            return db_user.followed_topics
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")

    def follow_bill(self, db: Session, user_id: int, bill_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
        if not db_bill:
            raise ObjectNotFoundException(f"Bill not found for id: {bill_id}")
        db_user.followed_bills.append(db_bill)
        db.commit()

    def unfollow_bill(self, db: Session, user_id: int, bill_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
        if not db_bill:
            raise ObjectNotFoundException(f"Bill not found for id: {bill_id}")
        if db_bill not in db_user.followed_bills:
            raise ObjectNotFoundException(
                f"Cannot unfollow, User {user_id} is not following bill {bill_id}"
            )
        db_user.followed_bills.remove(db_bill)
        db.commit()

    def get_user_bills(self, db: Session, user_id: int) -> List[models.Bill]:
        try:
            db_user = self.read(db=db, obj_id=user_id)
            return db_user.followed_bills
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")


class VoteCRUD(BaseCRUD[models.Vote]):
    pass


bill = BillCRUD(models.Bill)
legislator = LegislatorCRUD(models.Legislator)
legislative_body = LegislativeBodyCRUD(models.LegislativeBody)
party = UserCRUD(models.Party)
role = UserCRUD(models.Role)
state = UserCRUD(models.State)
topic = TopicCRUD(models.Topic)
user = UserCRUD(models.User)

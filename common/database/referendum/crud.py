from sqlalchemy.orm import Session, noload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel
from typing import Any, Dict, Generic, List, TypeVar, Type, Union

from common.database.referendum import models, schemas

import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=models.Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

T = TypeVar("T")


class CRUDException(Exception):
    pass


class ObjectNotFoundException(CRUDException):
    pass


class ObjectAlreadyExistsException(CRUDException):
    pass


class DatabaseException(CRUDException):
    pass


class DependencyException(CRUDException):
    pass


class NullValueException(CRUDException):
    pass


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
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

    def read_all(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def read_filtered(
        self, db: Session, *, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        query = db.query(self.model)
        for prop, value in filters.items():
            query = query.filter(getattr(self.model, prop) == value)
        return query.offset(skip).limit(limit).all()

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        if db_obj is None:
            raise ObjectNotFoundException("Object not found")
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
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


class BillCRUD(BaseCRUD[models.Bill, schemas.BillCreate, schemas.BillRecord]):
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

    def add_topic(self, db: Session, bill_id: int, topic_id: int):
        db_bill = self.read(db=db, obj_id=bill_id)
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if not db_topic:
            raise ObjectNotFoundException(f"Topic not found for id: {topic_id}")
        db_bill.topics.append(db_topic)
        db.commit()

    def remove_topic(self, db: Session, bill_id: int, topic_id: int):
        db_bill = self.read(db=db, obj_id=bill_id)
        db_topic = db.query(models.Topic).filter(models.Topic.id == topic_id).first()
        if not db_topic:
            raise ObjectNotFoundException(f"Topic not found for id: {topic_id}")
        if db_topic not in db_bill.topics:
            raise ObjectNotFoundException(
                f"Cannot unfollow, bill {bill_id} does not have topic {topic_id}"
            )
        db_bill.topics.remove(db_topic)
        db.commit()

    def add_sponsor(
        self, db: Session, bill_id: int, legislator_id: int, is_primary: bool = False
    ):
        db_bill = self.read(db=db, obj_id=bill_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )

        # Check if the sponsor already exists
        existing_sponsor = [
            sponsor
            for sponsor in db_bill.sponsors
            if sponsor.legislator_id == legislator_id
        ]
        if existing_sponsor:
            existing_sponsor = existing_sponsor[0]
            if existing_sponsor.is_primary != is_primary:
                existing_sponsor.is_primary = is_primary
                db.commit()
        else:
            db.execute(
                models.bill_sponsors.insert().values(
                    bill_id=bill_id, legislator_id=legislator_id, is_primary=is_primary
                )
            )
        db.commit()

    def remove_sponsor(
        self,
        db: Session,
        bill_id: int,
        legislator_id: int,
    ):
        db_bill = self.read(db=db, obj_id=bill_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )
        if db_legislator not in db_bill.sponsors:
            raise ObjectNotFoundException(
                f"Cannot remove, bill {bill_id} does not have sponsor {legislator_id}"
            )
        db_bill.sponsors.remove(db_legislator)
        db.commit()


class BillActionCRUD(
    BaseCRUD[models.BillAction, schemas.BillActionCreate, schemas.BillAction]
):
    pass


class CommitteeCRUD(
    BaseCRUD[models.Committee, schemas.CommitteeCreate, schemas.Committee]
):
    def add_legislator_membership(
        self, db: Session, committee_id: int, legislator_id: int
    ):
        db_committee = self.read(db=db, obj_id=committee_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )
        db_committee.legislators.append(db_legislator)
        db.commit()

    def remove_legislator_membership(
        self, db: Session, committee_id: int, legislator_id: int
    ):
        db_committee = self.read(db=db, obj_id=committee_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )
        if db_legislator not in db_committee.legislators:
            raise ObjectNotFoundException(
                f"Cannot remove legislator membership, legislator {legislator_id} is not in committee {committee_id}"
            )
        db_committee.legislators.remove(db_legislator)
        db.commit()

    def get_legislators(
        self, db: Session, committee_id: int
    ) -> List[models.Legislator]:
        try:
            db_committee = self.read(db=db, obj_id=committee_id)
            if db_committee is None:
                raise ObjectNotFoundException(f"User not found for id: {committee_id}")
            return db_committee.legislators
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")


class CommentCRUD(BaseCRUD[models.Comment, schemas.CommentCreate, schemas.Comment]):
    def delete(self, db: Session, obj_id: int) -> None:
        db_comment = db.get(self.model, obj_id)
        if db_comment is None:
            raise ObjectNotFoundException("Comment not found")

        # Check if the comment has any children
        replies = (
            db.query(models.Comment).filter(models.Comment.parent_id == obj_id).all()
        )
        if len(replies) > 0:
            raise DependencyException("Cannot delete a comment with replies")
        try:
            db.delete(db_comment)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")


class LegislatorCRUD(
    BaseCRUD[models.Legislator, schemas.LegislatorCreate, schemas.LegislatorRecord]
):
    pass


class LegislativeBodyCRUD(
    BaseCRUD[
        models.LegislativeBody, schemas.LegislativeBodyCreate, schemas.LegislativeBody
    ]
):
    pass


class PartyCRUD(BaseCRUD[models.Party, schemas.Party.Base, schemas.Party.Record]):
    pass


class RoleCRUD(BaseCRUD[models.Role, schemas.Role.Base, schemas.Role.Record]):
    pass


class StateCRUD(BaseCRUD[models.State, schemas.StateCreate, schemas.State]):
    pass


class TopicCRUD(BaseCRUD[models.Topic, schemas.TopicCreate, schemas.Topic]):
    pass


class UserCRUD(BaseCRUD[models.User, schemas.UserCreate, schemas.UserCreate]):
    def get_user_by_email(self, db: Session, email: str) -> models.User:
        try:
            db_user = (
                db.query(models.User)
                # TODO - reenable this to avoid querying all relationships on authentication
                # .options(noload(models.User.topics), noload(models.User.bills))
                .filter(models.User.email == email).first()
            )
            if db_user is None:
                raise ObjectNotFoundException(f"User with email {email} not found")
            return db_user
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
            if db_user is None:
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

    def follow_legislator(self, db: Session, user_id: int, legislator_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )
        db_user.followed_legislators.append(db_legislator)
        db.commit()

    def unfollow_legislator(self, db: Session, user_id: int, legislator_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_legislator = (
            db.query(models.Legislator)
            .filter(models.Legislator.id == legislator_id)
            .first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(
                f"Legislator not found for id: {legislator_id}"
            )
        if db_legislator not in db_user.followed_legislators:
            raise ObjectNotFoundException(
                f"Cannot unfollow, User {user_id} is not following legislator {legislator_id}"
            )
        db_user.followed_legislators.remove(db_legislator)
        db.commit()

    def get_user_legislators(
        self, db: Session, user_id: int
    ) -> List[models.Legislator]:
        try:
            db_user = self.read(db=db, obj_id=user_id)
            return db_user.followed_legislators
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")

    def like_comment(self, db: Session, user_id: int, comment_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_comment = (
            db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        )
        if not db_comment:
            raise ObjectNotFoundException(f"Comment not found for id: {comment_id}")
        db_user.liked_comments.append(db_comment)
        db.commit()

    def unlike_comment(self, db: Session, user_id: int, comment_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_comment = (
            db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        )
        if not db_comment:
            raise ObjectNotFoundException(f"Comment not found for id: {comment_id}")
        if db_comment not in db_user.liked_comments:
            raise ObjectNotFoundException(
                f"Cannot unfollow, User {user_id} is not following bill {comment_id}"
            )
        db_user.liked_comments.remove(db_comment)
        db.commit()


class LegislatorVoteCRUD(
    BaseCRUD[
        models.LegislatorVote, schemas.LegislatorVoteCreate, schemas.LegislatorVote
    ]
):
    def create_or_update_vote(
        self, db: Session, legislator_vote_object: schemas.LegislatorVote
    ):
        try:
            existing_vote = (
                db.query(self.model)
                .filter(
                    models.LegislatorVote.legislator_id
                    == legislator_vote_object.legislator_id,
                    models.LegislatorVote.bill_id == legislator_vote_object.bill_id,
                )
                .first()
            )

            if existing_vote:
                for key, value in legislator_vote_object.model_dump().items():
                    setattr(existing_vote, key, value)
            else:
                existing_vote = self.model(**legislator_vote_object.model_dump())
                db.add(existing_vote)

            db.commit()
            db.refresh(existing_vote)
            return existing_vote
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def get_votes_for_bill(
        self, db: Session, bill_id: int
    ) -> List[models.LegislatorVote]:
        return self.read_filtered(db=db, filters={"bill_id": bill_id})

    def get_votes_for_legislator(
        self, db: Session, legislator_id: int
    ) -> List[models.LegislatorVote]:
        return self.read_filtered(db=db, filters={"legislator_id": legislator_id})


class UserVoteCRUD(BaseCRUD[models.UserVote, schemas.UserVoteCreate, schemas.UserVote]):
    def create_or_update_vote(self, db: Session, user_vote_object: schemas.UserVote):
        try:
            existing_vote = (
                db.query(self.model)
                .filter(
                    models.UserVote.user_id == user_vote_object.user_id,
                    models.UserVote.bill_id == user_vote_object.bill_id,
                )
                .first()
            )

            if existing_vote:
                for key, value in user_vote_object.model_dump().items():
                    setattr(existing_vote, key, value)
            else:
                existing_vote = self.model(**user_vote_object.model_dump())
                db.add(existing_vote)

            db.commit()
            db.refresh(existing_vote)
            return existing_vote
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def get_votes_for_bill(self, db: Session, bill_id: int) -> List[models.UserVote]:
        return self.read_filtered(db=db, filters={"bill_id": bill_id})

    def get_votes_for_user(self, db: Session, user_id: int) -> List[models.UserVote]:
        return self.read_filtered(db=db, filters={"user_id": user_id})


bill = BillCRUD(models.Bill)
bill_action = BillActionCRUD(models.BillAction)
comment = CommentCRUD(models.Comment)
committee = CommitteeCRUD(models.Committee)
legislator = LegislatorCRUD(models.Legislator)
legislative_body = LegislativeBodyCRUD(models.LegislativeBody)
legislator_vote = LegislatorVoteCRUD(models.LegislatorVote)
party = UserCRUD(models.Party)
role = UserCRUD(models.Role)
state = UserCRUD(models.State)
topic = TopicCRUD(models.Topic)
user = UserCRUD(models.User)
user_vote = UserVoteCRUD(models.UserVote)

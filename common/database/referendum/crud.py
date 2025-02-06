import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.elements import BinaryExpression, ColumnElement


from common.database.referendum import models, schemas

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
                if value is None and self.model.__table__.columns[field].nullable is False:
                    raise NullValueException(f"Null value provided for non-nullable field: {field}")

            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to create with database error {str(e)}")
            if "unique constraint" in str(e).lower():
                raise ObjectAlreadyExistsException("Object already exists")
            raise DatabaseException(f"Integrity error: {str(e)}")
        except NullValueException as e:
            db.rollback()
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def read(self, db: Session, obj_id: Column[int] | int) -> ModelType:
        db_obj = db.query(self.model).filter(self.model.id == obj_id).first()
        if db_obj is None:
            raise ObjectNotFoundException("Object not found")
        return db_obj

    def read_all(
        self,
        db: Session,
        *,
        skip: int | None = None,
        limit: int | None = None,
        column_filter: ColumnElement[bool] | None = None,
        search_filter: ColumnElement[bool] | BinaryExpression | None = None,
        order_by: List[Column] | None = None,
    ) -> List[ModelType]:
        query = db.query(self.model)

        if column_filter is not None:
            query = query.filter(column_filter)
        if search_filter is not None:
            query = query.filter(search_filter)
        if order_by:
            query = query.order_by(*order_by)
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def read_filtered(
        self,
        db: Session,
        *,
        filters: Dict[str, Any],
        skip: int | None = None,
        limit: int | None = None,
    ) -> List[ModelType]:
        query = db.query(self.model)
        for prop, value in filters.items():
            query = query.filter(getattr(self.model, prop) == value)
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

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
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)
            for field in update_data:
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


class BillCRUD(BaseCRUD[models.Bill, schemas.Bill.Base, schemas.Bill.Record]):
    def get_bill_user_votes(self, db: Session, bill_id: int) -> Dict[str, Union[int, float]]:
        db_bill = self.read(db=db, obj_id=bill_id)
        yea = sum(1 for vote in db_bill.user_votes if vote.vote_choice_id == 1)
        nay = sum(1 for vote in db_bill.user_votes if vote.vote_choice_id == 2)
        total = len(db_bill.user_votes)
        return {
            "yea": yea,
            "nay": nay,
            "yea_pct": round(yea / total, 3),
            "nay_pct": round(nay / total, 3),
            "total": total,
        }

    def get_bill_comments(self, db: Session, bill_id: int) -> List[schemas.Comment.Record]:
        db_bill = self.read(db=db, obj_id=bill_id)

        return db_bill.comments

    def read_denormalized(self, db: Session, bill_id: int) -> models.Bill:
        db_bill = (
            db.query(models.Bill)
            .options(
                joinedload(models.Bill.state),
                joinedload(models.Bill.status),
                joinedload(models.Bill.legislative_body).joinedload(models.LegislativeBody.role),
                joinedload(models.Bill.sponsors).joinedload(models.Sponsor.legislator),
                joinedload(models.Bill.topics),
                joinedload(models.Bill.bill_versions),
                joinedload(models.Bill.session),
            )
            .filter(models.Bill.id == bill_id)
            .first()
        )
        if not db_bill:
            raise ObjectNotFoundException(f"Bill not found for id {bill_id}")

        return db_bill

    def read_all_denormalized(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        column_filter: ColumnElement[bool] | None = None,
        search_filter: BinaryExpression | ColumnElement[bool] | None = None,
        order_by: List[Column] | None = None,
    ) -> List[models.Bill]:
        query = db.query(models.Bill).options(
            joinedload(models.Bill.state),
            joinedload(models.Bill.status),
            joinedload(models.Bill.legislative_body).joinedload(models.LegislativeBody.role),
            joinedload(models.Bill.sponsors).joinedload(models.Sponsor.legislator),
            joinedload(models.Bill.topics),
            joinedload(models.Bill.bill_versions),
            joinedload(models.Bill.session),
        )

        if column_filter is not None:
            query = query.filter(column_filter)
        if search_filter is not None:
            query = query.filter(search_filter)
        if order_by:
            query = query.order_by(*order_by)

        return query.offset(skip).limit(limit).all()

    def get_bill_by_legiscan_id(self, db: Session, legiscan_id: int) -> models.Bill:
        try:
            bill = db.query(models.Bill).filter(models.Bill.legiscan_id == legiscan_id).first()
            if bill is None:
                raise ObjectNotFoundException(f"Bill with legiscan_id {legiscan_id} not found")
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
        self, db: Session, bill_id: int, legislator_id: int, type: str = "Sponsor", rank: int = 1
    ):
        db_legislator = (
            db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(f"Legislator not found for id: {legislator_id}")

        existing_sponsor = (
            db.query(models.Sponsor)
            .filter(
                models.Sponsor.bill_id == bill_id, models.Sponsor.legislator_id == legislator_id
            )
            .first()
        )

        if existing_sponsor:
            existing_sponsor.rank = rank
            existing_sponsor.type = type
        else:
            new_sponsor = models.Sponsor(
                bill_id=bill_id, legislator_id=legislator_id, rank=rank, type=type
            )
            db.add(new_sponsor)

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error adding sponsor: {str(e)}")

    def remove_sponsor(
        self,
        db: Session,
        bill_id: int,
        legislator_id: int,
    ):
        sponsor = (
            db.query(models.Sponsor)
            .filter(
                models.Sponsor.bill_id == bill_id, models.Sponsor.legislator_id == legislator_id
            )
            .first()
        )

        if not sponsor:
            raise ObjectNotFoundException(
                f"Sponsor relationship not found for bill {bill_id} and legislator {legislator_id}"
            )

        try:
            db.delete(sponsor)
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error removing sponsor: {str(e)}")


class BillActionCRUD(
    BaseCRUD[models.BillAction, schemas.BillAction.Base, schemas.BillAction.Record]
):
    pass


class BillVersionCRUD(
    BaseCRUD[models.BillVersion, schemas.BillVersion.Base, schemas.BillVersion.Record]
):
    pass


class CommitteeCRUD(BaseCRUD[models.Committee, schemas.Committee.Base, schemas.Committee.Record]):
    def add_legislator_membership(self, db: Session, committee_id: int, legislator_id: int):
        db_committee = self.read(db=db, obj_id=committee_id)
        db_legislator = (
            db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(f"Legislator not found for id: {legislator_id}")
        db_committee.legislators.append(db_legislator)
        db.commit()

    def remove_legislator_membership(self, db: Session, committee_id: int, legislator_id: int):
        db_committee = self.read(db=db, obj_id=committee_id)
        db_legislator = (
            db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(f"Legislator not found for id: {legislator_id}")
        if db_legislator not in db_committee.legislators:
            raise ObjectNotFoundException(
                f"Cannot remove legislator membership, legislator {legislator_id} is not in committee {committee_id}"
            )
        db_committee.legislators.remove(db_legislator)
        db.commit()

    def get_legislators(self, db: Session, committee_id: int) -> List[models.Legislator]:
        try:
            db_committee = self.read(db=db, obj_id=committee_id)
            if db_committee is None:
                raise ObjectNotFoundException(f"User not found for id: {committee_id}")
            return db_committee.legislators
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")


class CommentCRUD(BaseCRUD[models.Comment, schemas.Comment.Record, schemas.Comment.Record]):
    def delete(self, db: Session, obj_id: int) -> None:
        db_comment = db.get(self.model, obj_id)
        if db_comment is None:
            raise ObjectNotFoundException("Comment not found")

        # Check if the comment has any children
        replies = db.query(models.Comment).filter(models.Comment.parent_id == obj_id).all()
        if len(replies) > 0:
            raise DependencyException("Cannot delete a comment with replies")
        try:
            db.delete(db_comment)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")


class LegislatorCRUD(
    BaseCRUD[models.Legislator, schemas.Legislator.Base, schemas.Legislator.Record]
):
    pass


class LegislativeBodyCRUD(
    BaseCRUD[
        models.LegislativeBody,
        schemas.LegislativeBody.Base,
        schemas.LegislativeBody.Record,
    ]
):
    pass


class PartyCRUD(BaseCRUD[models.Party, schemas.Party.Base, schemas.Party.Record]):
    pass


class RoleCRUD(BaseCRUD[models.Role, schemas.Role.Base, schemas.Role.Record]):
    pass


class StateCRUD(BaseCRUD[models.State, schemas.State.Base, schemas.State.Record]):
    pass


class StatusCRUD(BaseCRUD[models.Status, schemas.Status.Base, schemas.Status.Record]):
    pass


class TopicCRUD(BaseCRUD[models.Topic, schemas.Topic.Base, schemas.Topic.Record]):
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
            if not db_user:
                raise ObjectNotFoundException(f"User not found for email: {email}")

            return db_user
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")
    
    def get_user_by_social_provider(self, db: Session, social_provider_user_id: str, social_provider_name: str) -> models.User:
        try:
            # To-Do: This query shouldn't directly access keys with hard-coded strings as it tightly couples with the database schema
            db_user = (
                db.query(models.User).
                filter(
                    models.User.settings['social_provider_user_id'].astext == social_provider_user_id,
                    models.User.settings['social_provider_name'].astext == social_provider_name
                ).first()
            )
            return db_user
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")

    def update_user_password(self, db: Session, user_id: Column[int] | int, hashed_password: str):
        db_user = self.read(db=db, obj_id=user_id)
        db_user.hashed_password = hashed_password
        db.commit()
        db.refresh(db_user)

    def update_soft_delete(
        self,
        db: Session,
        user_id: Column[int] | int,
        deleted: bool,
    ) -> models.User:
        try:
            db_user = db.query(models.User).filter(models.User.id == user_id).first()
            if db_user is None:
                raise ObjectNotFoundException(f"User {user_id} not found")
            # Copy and reassign to trigger SQLAlchemy change 
            settings = dict(db_user.settings)
            settings["deleted"] = deleted
            db_user.settings = settings
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)

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
            db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(f"Legislator not found for id: {legislator_id}")
        db_user.followed_legislators.append(db_legislator)
        db.commit()

    def unfollow_legislator(self, db: Session, user_id: int, legislator_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_legislator = (
            db.query(models.Legislator).filter(models.Legislator.id == legislator_id).first()
        )
        if not db_legislator:
            raise ObjectNotFoundException(f"Legislator not found for id: {legislator_id}")
        if db_legislator not in db_user.followed_legislators:
            raise ObjectNotFoundException(
                f"Cannot unfollow, User {user_id} is not following legislator {legislator_id}"
            )
        db_user.followed_legislators.remove(db_legislator)
        db.commit()

    def get_user_legislators(self, db: Session, user_id: int) -> List[models.Legislator]:
        try:
            db_user = self.read(db=db, obj_id=user_id)
            return db_user.followed_legislators
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database error: {str(e)}")

    def like_comment(self, db: Session, user_id: int, comment_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
        if not db_comment:
            raise ObjectNotFoundException(f"Comment not found for id: {comment_id}")
        db_user.liked_comments.append(db_comment)
        db.commit()

    def unlike_comment(self, db: Session, user_id: int, comment_id: int):
        db_user = self.read(db=db, obj_id=user_id)
        db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
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
        models.LegislatorVote,
        schemas.LegislatorVote.Base,
        schemas.LegislatorVote.Record,
    ]
):
    def create_or_update_vote(self, db: Session, vote: schemas.LegislatorVote.Record):
        try:
            db_vote = (
                db.query(self.model)
                .filter(
                    models.LegislatorVote.legislator_id == vote.legislator_id,
                    models.LegislatorVote.bill_id == vote.bill_id,
                    models.LegislatorVote.bill_action_id == vote.bill_action_id,
                )
                .first()
            )

            if db_vote:
                for key, value in vote.model_dump().items():
                    setattr(db_vote, key, value)
            else:
                db_vote = self.model(**vote.model_dump())
                db.add(db_vote)

            db.commit()
            db.refresh(db_vote)
            return db_vote
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def delete_vote(self, db: Session, legislator_id: int, bill_action_id: int):
        try:
            db_vote = (
                db.query(self.model)
                .filter(
                    models.LegislatorVote.legislator_id == legislator_id,
                    models.LegislatorVote.bill_action_id == bill_action_id,
                )
                .first()
            )
            if db_vote is None:
                raise ObjectNotFoundException(
                    f"Vote not found for legislator {legislator_id} for bill action {bill_action_id}"
                )

            db.delete(db_vote)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def get_votes_for_bill(self, db: Session, bill_id: int) -> List[models.LegislatorVote]:
        return self.read_filtered(db=db, filters={"bill_id": bill_id})

    def get_votes_for_legislator(
        self, db: Session, legislator_id: int
    ) -> List[models.LegislatorVote]:
        return self.read_filtered(db=db, filters={"legislator_id": legislator_id})


class UserVoteCRUD(BaseCRUD[models.UserVote, schemas.UserVoteCreate, schemas.UserVote]):
    def cast_vote(self, db: Session, vote: schemas.UserVote):
        try:
            db_vote = (
                db.query(self.model)
                .filter(
                    models.UserVote.user_id == vote.user_id,
                    models.UserVote.bill_id == vote.bill_id,
                )
                .first()
            )

            if db_vote:
                for key, value in vote.model_dump().items():
                    setattr(db_vote, key, value)
            else:
                db_vote = self.model(**vote.model_dump())
                db.add(db_vote)

            db.commit()
            db.refresh(db_vote)
            return db_vote
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def uncast_vote(self, db: Session, user_id: int, bill_id: int) -> None:
        try:
            db_vote = (
                db.query(self.model)
                .filter(
                    models.UserVote.user_id == user_id,
                    models.UserVote.bill_id == bill_id,
                )
                .first()
            )

            if db_vote:
                db.delete(db_vote)
                db.commit()
            else:
                raise ObjectNotFoundException(
                    f"No vote exists for user {user_id} on bill {bill_id}"
                )

        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"Database error: {str(e)}")

    def get_votes_for_bill(self, db: Session, bill_id: int) -> List[models.UserVote]:
        return self.read_filtered(db=db, filters={"bill_id": bill_id})

    def get_votes_for_user(
        self, db: Session, user_id: int, bill_id: Optional[int] = None
    ) -> List[models.UserVote]:
        filters = {"user_id": user_id}
        if bill_id is not None:
            filters["bill_id"] = bill_id
        return self.read_filtered(db=db, filters=filters)


class VoteChoiceCRUD(
    BaseCRUD[models.VoteChoice, schemas.VoteChoice.Base, schemas.VoteChoice.Record]
):
    pass


class SessionCRUD(BaseCRUD[models.Session, schemas.Session.Base, schemas.Session.Record]):
    pass


class PresidentCRUD(BaseCRUD[models.President, schemas.President.Base, schemas.President.Record]):
    pass


class ExecutiveOrderCRUD(
    BaseCRUD[models.ExecutiveOrder, schemas.ExecutiveOrder.Base, schemas.ExecutiveOrder.Record]
):
    def read_denormalized(self, db: Session, executive_order_id: int) -> models.ExecutiveOrder:
        db_eo = (
            db.query(models.ExecutiveOrder)
            .options(
                joinedload(models.ExecutiveOrder.president_id),
            )
            .filter(models.ExecutiveOrder.id == executive_order_id)
            .first()
        )
        if not db_eo:
            raise ObjectNotFoundException(f"Executive Order not found for id: {executive_order_id}")

    def read_all_denormalized(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        column_filter: ColumnElement[bool] | None = None,
        search_filter: BinaryExpression | ColumnElement[bool] | None = None,
        order_by: List[Column] | None = None,
    ) -> List[models.ExecutiveOrder]:
        query = db.query(models.ExecutiveOrder).options(
            joinedload(models.ExecutiveOrder.president),
        )

        if column_filter is not None:
            query = query.filter(column_filter)
        if search_filter is not None:
            query = query.filter(search_filter)
        if order_by:
            query = query.order_by(*order_by)

        return query.offset(skip).limit(limit).all()


bill = BillCRUD(models.Bill)
bill_action = BillActionCRUD(models.BillAction)
bill_version = BillVersionCRUD(models.BillVersion)
comment = CommentCRUD(models.Comment)
committee = CommitteeCRUD(models.Committee)
executive_order = ExecutiveOrderCRUD(models.ExecutiveOrder)
legislator = LegislatorCRUD(models.Legislator)
legislative_body = LegislativeBodyCRUD(models.LegislativeBody)
legislator_vote = LegislatorVoteCRUD(models.LegislatorVote)
party = PartyCRUD(models.Party)
president = PartyCRUD(models.President)
role = RoleCRUD(models.Role)
state = StateCRUD(models.State)
status = StatusCRUD(models.Status)
session = SessionCRUD(models.Session)
topic = TopicCRUD(models.Topic)
user = UserCRUD(models.User)
user_vote = UserVoteCRUD(models.UserVote)
vote_choice = VoteChoiceCRUD(models.VoteChoice)

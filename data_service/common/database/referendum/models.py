import datetime
import logging

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)
Base = declarative_base()

# Association tables
user_topic_follows = Table(
    "user_topic_follows",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)

user_bill_follows = Table(
    "user_bill_follows",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
)

user_legislator_follows = Table(
    "user_legislator_follows",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("legislator_id", Integer, ForeignKey("legislators.id"), primary_key=True),
)

user_comment_likes = Table(
    "user_comment_likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("comment_id", Integer, ForeignKey("comments.id"), primary_key=True),
)


committee_membership = Table(
    "committee_membership",
    Base.metadata,
    Column("committee_id", Integer, ForeignKey("committees.id"), primary_key=True),
    Column("legislator_id", Integer, ForeignKey("legislators.id"), primary_key=True),
)


bill_topics = Table(
    "bill_topics",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)


class Sponsor(Base):
    __tablename__ = "bill_sponsors"

    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    legislator_id = Column(Integer, ForeignKey("legislators.id"), primary_key=True)
    rank = Column(Integer, nullable=False, default=0)
    type = Column(String, nullable=False, default="")

    legislator = relationship("Legislator")
    bill = relationship("Bill")


class VoteChoice(Base):
    __tablename__ = "vote_choices"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


# Core models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    settings = Column(JSONB, nullable=False, default={})

    followed_topics = relationship("Topic", secondary=user_topic_follows)
    followed_bills = relationship("Bill", secondary=user_bill_follows)
    followed_legislators = relationship("Legislator", secondary=user_legislator_follows)
    liked_comments = relationship("Comment", secondary=user_comment_likes, back_populates="likes")
    forgot_password_tokens = relationship("ForgotPasswordToken", back_populates="user")


class Party(Base):
    __tablename__ = "partys"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    abbr = Column(String, nullable=False)


class LegislativeBody(Base):
    __tablename__ = "legislative_bodys"

    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)

    role = relationship("Role")
    state = relationship("State")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Committee(Base):
    __tablename__ = "committees"

    id = Column(Integer, primary_key=True)
    legislative_body_id = Column(Integer, ForeignKey("legislative_bodys.id"))
    name = Column(String, unique=True, nullable=False)

    legislators = relationship(
        "Legislator", secondary=committee_membership, back_populates="committees"
    )


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    legiscan_id = Column(Integer, unique=True, index=True)
    identifier = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"), index=True)
    legislative_body_id = Column(Integer, ForeignKey("legislative_bodys.id"), index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), index=True)
    status_date = Column(Date)
    current_version_id = Column(Integer, ForeignKey("bill_versions.id"), nullable=True)

    status = relationship("Status")
    state = relationship("State")
    legislative_body = relationship("LegislativeBody")
    topics = relationship("Topic", secondary=bill_topics)
    user_votes = relationship("UserVote", back_populates="bill")
    comments = relationship("Comment")
    bill_versions = relationship("BillVersion", foreign_keys="BillVersion.bill_id")
    session = relationship("Session", back_populates="bills")
    sponsors = relationship("Sponsor", back_populates="bill")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), index=True)

    state = relationship("State")
    bills = relationship("Bill", back_populates="session")


class ForgotPasswordToken(Base):
    __tablename__ = "forgot_password_tokens"

    id = Column(Integer, primary_key=True)
    passcode = Column(String, nullable=False)
    expires_at = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="forgot_password_tokens")


class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class BillVersion(Base):
    __tablename__ = "bill_versions"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    url = Column(String, nullable=True)
    hash = Column(String, nullable=True)
    date = Column(Date, nullable=False, default=datetime.date(1970, 1, 1))
    briefing = Column(String, nullable=True)


class BillAction(Base):
    __tablename__ = "bill_actions"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    legislative_body_id = Column(Integer, ForeignKey("legislative_bodys.id"), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)

    legislator_votes = relationship("LegislatorVote", back_populates="bill_action")


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True)
    legiscan_id = Column(Integer, unique=True, index=True)
    name = Column(String, nullable=False)
    image_url = Column(String)
    party_id = Column(Integer, ForeignKey("partys.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))
    state_id = Column(Integer, ForeignKey("states.id"))
    district = Column(String, nullable=False)
    representing_state_id = Column(Integer, ForeignKey("states.id"))
    address = Column(String)
    facebook = Column(String)
    instagram = Column(String)
    phone = Column(String)
    twitter = Column(String)

    legislator_votes = relationship("LegislatorVote", back_populates="legislator")
    party = relationship("Party")
    state = relationship("State", foreign_keys=[state_id])
    representing_state = relationship("State", foreign_keys=[representing_state_id])
    role = relationship("Role")
    committees = relationship(
        "Committee", secondary=committee_membership, back_populates="legislators"
    )
    sponsored_bills = relationship("Sponsor", back_populates="legislator")


class UserVote(Base):
    __tablename__ = "user_votes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    vote_choice_id = Column(Integer, ForeignKey("vote_choices.id"), nullable=False)

    bill = relationship("Bill", back_populates="user_votes")


class LegislatorVote(Base):
    __tablename__ = "legislator_votes"

    legislator_id = Column(Integer, ForeignKey("legislators.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    bill_action_id = Column(Integer, ForeignKey("bill_actions.id"), primary_key=True)
    vote_choice_id = Column(Integer, ForeignKey("vote_choices.id"), nullable=False)

    bill_action = relationship(
        "BillAction",
        order_by="desc(BillAction.id), desc(BillAction.date)",
        back_populates="legislator_votes",
    )
    legislator = relationship("Legislator", back_populates="legislator_votes")
    vote_choice = relationship("VoteChoice")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))
    comment = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    bill = relationship("Bill")
    likes = relationship("User", secondary=user_comment_likes, back_populates="liked_comments")
    user = relationship("User")


class President(Base):
    __tablename__ = "presidents"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    party_id = Column(Integer, ForeignKey("partys.id"))


class ExecutiveOrder(Base):
    __tablename__ = "executive_orders"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    signed_date = Column(Date)
    url = Column(String)
    hash = Column(String)
    briefing = Column(String, nullable=True)
    president_id = Column(Integer, ForeignKey("presidents.id"), index=True)

    president = relationship("President")

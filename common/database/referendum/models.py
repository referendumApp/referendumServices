from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Table, Date
from sqlalchemy.orm import relationship
import enum

from common.database.postgres_core.utils import Base


user_topic_follows = Table(
    "user_topic_follows",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("topic_id", Integer, ForeignKey("topics.id")),
)


user_bill_follows = Table(
    "user_bill_follows",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("bill_id", Integer, ForeignKey("bills.id")),
)


class Party(Base):
    __tablename__ = "partys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)


class LegislativeBody(Base):
    __tablename__ = "legislative_bodys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer)
    state_id = Column(Integer)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    followed_topics = relationship("Topic", secondary=user_topic_follows)
    followed_bills = relationship("Bill", secondary=user_bill_follows)


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legiscan_id = Column(Integer, index=True)
    identifier = Column(String)
    title = Column(String)
    description = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"), index=True)
    legislative_body_id = Column(
        Integer, ForeignKey("legislative_bodys.id"), index=True
    )
    session_id = Column(Integer, index=True)
    briefing = Column(String)
    status_id = Column(Integer)
    status_date = Column(Date)


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    image_url = Column(String, nullable=True)
    party_id = Column(Integer, nullable=False)
    district = Column(String)

    address = Column(String)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    twitter = Column(String, nullable=True)


class VoteChoice(enum.Enum):
    YES = 1
    NO = 2


class Vote(Base):
    __tablename__ = "votes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    vote_type = Column(Enum(VoteChoice), nullable=False)

from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date
from sqlalchemy.orm import relationship

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


legislative_body_membership = Table(
    "legislative_body_membership",
    Base.metadata,
    Column("legislative_body_id", Integer, ForeignKey("legislative_bodies.id")),
    Column("legislator_id", Integer, ForeignKey("legislators.id")),
    Column("start_date", Date),
    Column("end_date", Date),
)


party_membership = Table(
    "party_membership",
    Base.metadata,
    Column("party_id", Integer, ForeignKey("parties.id")),
    Column("legislator_id", Integer, ForeignKey("legislators.id")),
    Column("start_date", Date),
    Column("end_date", Date),
)


class Party(Base):
    __tablename__ = "parties"

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


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class LegislativeBody(Base):
    __tablename__ = "legislative_bodies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    role_id = Column(Integer)
    state_id = Column(Integer)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    topics = relationship("Topic", secondary=user_topic_follows)
    bills = relationship("Bill", secondary=user_bill_follows)


class Bill(Base):
    __tablename__ = "bills"

    legiscan_id = Column(Integer, index=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String)
    title = Column(String)
    description = Column(String)
    state = Column(String, index=True)
    body = Column(String, index=True)
    session = Column(String, index=True)
    briefing = Column(String)
    status = Column(String)
    latest_action = Column(String)


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    image_url = Column(String, nullable=True)
    district = Column(String)

    address = Column(String)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    twitter = Column(String, nullable=True)

    parties = relationship("Party", secondary=party_membership)
    legislative_bodies = relationship(
        "LegislativeBody", secondary=legislative_body_membership
    )

from sqlalchemy import Column, Integer, String, ForeignKey, Table
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

    topics = relationship("Topic", secondary=user_topic_follows)
    bills = relationship("Bill", secondary=user_bill_follows)


class Bill(Base):
    __tablename__ = "bills"

    legiscan_id = Column(Integer, index=True)  # bill_id
    id = Column(Integer, primary_key=True, autoincrement=True)
    identifier = Column(String)  # bill_number
    title = Column(String)  # title
    description = Column(String)  # description
    state_id = Column(String, index=True)  # state_id
    legislative_body_id = Column(String, index=True)  # body_id
    session_id = Column(String, index=True)  # session_id
    briefing = Column(String)  # empty
    status_id = Column(String)  # status_id and status date, get rid of latest action
    status_date = Column(String)


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

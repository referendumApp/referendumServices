from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Table, Date, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


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


committee_membership = Table(
    "committee_membership",
    Base.metadata,
    Column("committee_id", Integer, ForeignKey("committees.id"), primary_key=True),
    Column("legislator_id", Integer, ForeignKey("legislators.id"), primary_key=True),
)


bill_sponsors = Table(
    "bill_sponsors",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
    Column("legislator_id", Integer, ForeignKey("legislators.id"), primary_key=True),
    Column("is_primary", Boolean, nullable=False, default=False),
)


bill_topics = Table(
    "bill_topics",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)


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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    followed_topics = relationship("Topic", secondary=user_topic_follows)
    followed_bills = relationship("Bill", secondary=user_bill_follows)


class BillVersion(Base):
    __tablename__ = "bill_versions"

    bill_id = Column(Integer, primary_key=True)
    version = Column(Integer, primary_key=True)


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    legiscan_id = Column(Integer, unique=True, index=True)
    identifier = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    state_id = Column(Integer, ForeignKey("states.id"), index=True, nullable=True)
    legislative_body_id = Column(
        Integer, ForeignKey("legislative_bodys.id"), index=True, nullable=True
    )
    session_id = Column(Integer, index=True, nullable=True)
    briefing = Column(String)
    status_id = Column(Integer, nullable=True)
    status_date = Column(Date, nullable=True)

    state = relationship("State")
    topics = relationship("Topic", secondary=bill_topics)
    legislative_body = relationship("LegislativeBody")
    sponsors = relationship(
        "Legislator", secondary=bill_sponsors, back_populates="sponsored_bills"
    )


class BillActionType(enum.Enum):
    FLOOR_VOTE = 1
    COMMITTEE_VOTE = 2


class BillAction(Base):
    __tablename__ = "bill_actions"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer)
    date = Column(Date, nullable=True)
    type = Column(Enum(BillActionType), nullable=False)


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True)
    legiscan_id = Column(Integer, unique=True, index=True)
    name = Column(String, nullable=False)
    image_url = Column(String)
    party_id = Column(Integer, ForeignKey("partys.id"), nullable=True)
    district = Column(String, nullable=False)
    address = Column(String, nullable=True)
    facebook = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    twitter = Column(String, nullable=True)

    party = relationship("Party")
    committees = relationship(
        "Committee", secondary=committee_membership, back_populates="legislators"
    )
    sponsored_bills = relationship(
        "Bill", secondary=bill_sponsors, back_populates="sponsors"
    )


class VoteChoice(enum.Enum):
    YES = 1
    NO = 2


class UserVote(Base):
    __tablename__ = "user_votes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    vote_choice = Column(Enum(VoteChoice), nullable=False)


class LegislatorVote(Base):
    __tablename__ = "legislator_votes"

    legislator_id = Column(Integer, ForeignKey("legislators.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    vote_choice = Column(Enum(VoteChoice), nullable=False)

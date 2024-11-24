from sqlalchemy import Column, Enum, Integer, String, ForeignKey, Table, Date, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum

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

bill_sponsors = Table(
    "bill_sponsors",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
    Column("legislator_id", Integer, ForeignKey("legislators.id"), primary_key=True),
    Column("order", String, nullable=False, default=False),
    Column("type", String, nullable=False, default=False),
)

bill_topics = Table(
    "bill_topics",
    Base.metadata,
    Column("bill_id", Integer, ForeignKey("bills.id"), primary_key=True),
    Column("topic_id", Integer, ForeignKey("topics.id"), primary_key=True),
)


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
    hashed_password = Column(String, nullable=False)

    followed_topics = relationship("Topic", secondary=user_topic_follows)
    followed_bills = relationship("Bill", secondary=user_bill_follows)
    followed_legislators = relationship("Legislator", secondary=user_legislator_follows)
    liked_comments = relationship("Comment", secondary=user_comment_likes, back_populates="likes")


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
    briefing = Column(String, nullable=True)
    status = Column(String)
    status_date = Column(Date)

    state = relationship("State")
    legislative_body = relationship("LegislativeBody")
    topics = relationship("Topic", secondary=bill_topics)
    sponsors = relationship("Legislator", secondary=bill_sponsors, back_populates="sponsored_bills")
    bill_versions = relationship("BillVersion", back_populates="bill")
    session = relationship("Session", back_populates="bills")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), index=True)

    state = relationship("State")
    bills = relationship("Bill", back_populates="session")


class BillVersion(Base):
    __tablename__ = "bill_versions"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    url = Column(String, nullable=True)
    hash = Column(String, nullable=True)

    bill = relationship("Bill", back_populates="bill_versions")


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
    address = Column(String)
    facebook = Column(String)
    instagram = Column(String)
    phone = Column(String)
    twitter = Column(String)

    legislator_votes = relationship("LegislatorVote", back_populates="legislator")
    party = relationship("Party")
    state = relationship("State")
    role = relationship("Role")
    committees = relationship(
        "Committee", secondary=committee_membership, back_populates="legislators"
    )
    sponsored_bills = relationship("Bill", secondary=bill_sponsors, back_populates="sponsors")


class UserVote(Base):
    __tablename__ = "user_votes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    vote_choice_id = Column(Integer, ForeignKey("vote_choices.id"), nullable=False)


class LegislatorVote(Base):
    __tablename__ = "legislator_votes"

    legislator_id = Column(Integer, ForeignKey("legislators.id"), primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), primary_key=True)
    bill_action_id = Column(Integer, ForeignKey("bill_actions.id"), primary_key=True)
    vote_choice_id = Column(Integer, ForeignKey("vote_choices.id"), nullable=False)

    bill_action = relationship("BillAction", back_populates="legislator_votes")
    legislator = relationship("Legislator", back_populates="legislator_votes")
    vote_choice = relationship("VoteChoice")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"))
    comment = Column(String, nullable=False)

    likes = relationship("User", secondary=user_comment_likes, back_populates="liked_comments")

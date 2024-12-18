import datetime
import logging

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table, event
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Query

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
    status = Column(String)
    status_date = Column(Date)
    current_version_id = Column(Integer, ForeignKey("bill_versions.id"), nullable=True)

    state = relationship("State")
    legislative_body = relationship("LegislativeBody")
    topics = relationship("Topic", secondary=bill_topics)
    user_votes = relationship("UserVote", back_populates="bill")
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

    likes = relationship("User", secondary=user_comment_likes, back_populates="liked_comments")


BILL_SUBSET_IDS = [
    999999,
    1650479,
    1650485,
    1650487,
    1650489,
    1650495,
    1650498,
    1650511,
    1650517,
    1650520,
    1650522,
    1650530,
    1650533,
    1650543,
    1650547,
    1650577,
    1650590,
    1650609,
    1650615,
    1650618,
    1650634,
    1650664,
    1650693,
    1650697,
    1650704,
    1650717,
    1650758,
    1650764,
    1650775,
    1650799,
    1650801,
    1650812,
    1650826,
    1650896,
    1650936,
    1650939,
    1650942,
    1650961,
    1650965,
    1650988,
    1651010,
    1651014,
    1651016,
    1651024,
    1653507,
    1655806,
    1655816,
    1655889,
    1656001,
    1656123,
    1656164,
    1656185,
    1657885,
    1657890,
    1657893,
    1657897,
    1657899,
    1657901,
    1657907,
    1657908,
    1657913,
    1657938,
    1659561,
    1659566,
    1664816,
    1664819,
    1664824,
    1664830,
    1664834,
    1664836,
    1664843,
    1674730,
    1674735,
    1674737,
    1674738,
    1674746,
    1674748,
    1674759,
    1674763,
    1674785,
    1674808,
    1674812,
    1677278,
    1677308,
    1677449,
    1677513,
    1677559,
    1679223,
    1679235,
    1679249,
    1679268,
    1679272,
    1679282,
    1650880,
    1650933,
    1657889,
    1664821,
    1677202,
    1677339,
    1679233,
    1679239,
    1724917,
]


@event.listens_for(Query, "before_compile", retval=True)
def filter_bill_queries(query):
    """Filter both direct bill queries and queries with bill_id foreign keys"""

    if not query.column_descriptions:
        return query

    if getattr(query, "_bill_filtered", False):
        return query

    # Log all entities involved in the query
    for desc in query.column_descriptions:
        entity = desc.get("entity")

        if entity is Bill:
            query = query.filter(Bill.id.in_(BILL_SUBSET_IDS))
            query._bill_filtered = True
            return query

        if entity and hasattr(entity, "bill_id"):
            query = query.filter(entity.bill_id.in_(BILL_SUBSET_IDS))
            query._bill_filtered = True
            return query

    return query


@event.listens_for(Engine, "before_execute", retval=True)
def filter_bill_selects(conn, clauseelement, multiparams, params, execution_options):
    """Filter bill-related select() statements"""
    logger.warning("Starting filter for SQL statement")
    logger.warning(f"Statement: {clauseelement}")

    if hasattr(clauseelement, "_bill_filtered") and clauseelement._bill_filtered:
        logger.warning("Statement already filtered, skipping")
        return clauseelement, multiparams, params

    if hasattr(clauseelement, "froms"):
        for table in clauseelement.froms:
            logger.warning(f"Checking table: {table}")
            if hasattr(table, "name"):
                if table.name == "bills":
                    logger.warning("Found bills table, applying filter")
                    clauseelement = clauseelement.where(table.c.id.in_(BILL_SUBSET_IDS))
                    clauseelement._bill_filtered = True
                elif hasattr(table.c, "bill_id"):
                    logger.warning(f"Found table with bill_id: {table.name}")
                    clauseelement = clauseelement.where(table.c.bill_id.in_(BILL_SUBSET_IDS))
                    clauseelement._bill_filtered = True

    return clauseelement, multiparams, params

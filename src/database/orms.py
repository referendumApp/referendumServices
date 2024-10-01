from sqlalchemy import Column, Integer, String

from database.database import Base


# Junction table for Bill-Tag relationship
# bill_topics = Table('bill_topics', Base.metadata,
#     Column('bill_id', Integer, ForeignKey('bills.id'), primary_key=True),
#     Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True)
#     )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


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
    latestAction = Column(String)
    # topics = relationship("Topic", secondary=bill_topics, back_populates="bills" )


# class Topic(Base):
#     __tablename__ = "topics"

#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     bills = relationship("Bill", secondary=bill_topics, back_populates="topics")


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chamber = Column(String)
    district = Column(String)
    email = Column(String)
    facebook = Column(String)
    imageUrl = Column(String)
    instagram = Column(String)
    name = Column(String)
    office = Column(String)
    party = Column(String)
    phone = Column(String)
    state = Column(String)
    twitter = Column(String)

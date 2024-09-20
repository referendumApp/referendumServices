from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from .database import Base








# Junction table for Bill-Tag relationship
# bill_topics = Table('bill_topics', Base.metadata,
#     Column('bill_id', Integer, ForeignKey('bills.id'), primary_key=True),
#     Column('topic_id', Integer, ForeignKey('topics.id'), primary_key=True)
#     )



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    

class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    identifier = Column(String)
    title = Column(String)
    description = Column(String)
    state = Column(String, index=True)
    body = Column(String, index=True)
    session = Column(String, index=True)
    briefing = Column(String)
    sponsorIds = Column(Integer)
    status = Column(String)
    latestAction = Column(String)
    yesVotes = Column(Integer)
    noVotes = Column(Integer)
    userVote = Column(String, default="null")
#    topics = relationship("Topic", secondary=bill_topics, back_populates="bills" )

# class Topic(Base):
#     __tablename__ = "topics"

#     id = Column(Integer, primary_key=True)
#     name = Column(String)
#     bills = relationship("Bill", secondary=bill_topics, back_populates="topics")





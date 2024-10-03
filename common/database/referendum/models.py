from sqlalchemy import Column, Integer, String

from common.database.postgres_core.utils import Base


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
    latest_action = Column(String)


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chamber = Column(String)
    district = Column(String)
    email = Column(String)
    facebook = Column(String)
    image_url = Column(String)
    instagram = Column(String)
    name = Column(String)
    office = Column(String)
    party = Column(String)
    phone = Column(String)
    state = Column(String)
    twitter = Column(String)

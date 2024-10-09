from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List


# Party


class PartyBase(BaseModel):
    name: str


class PartyCreate(PartyBase):
    pass


class Party(PartyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Role


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# State


class StateBase(BaseModel):
    name: str


class StateCreate(StateBase):
    pass


class State(StateBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# LegislativeBody


class LegislativeBodyBase(BaseModel):
    name: str


class LegislativeBodyCreate(LegislativeBodyBase):
    pass


class LegislativeBody(LegislativeBodyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Topics


class TopicBase(BaseModel):
    name: str


class TopicCreate(TopicBase):
    pass


class Topic(TopicBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Bills


class BillBase(BaseModel):
    legiscan_id: int
    identifier: str
    title: str
    description: str
    state_id: int
    legislative_body_id: int
    session_id: int
    briefing: str
    status_id: int
    status_date: date


class BillCreate(BillBase):
    pass


class BillRecord(BillBase):
    id: int

    class Config:
        from_attributes = True


class Bill(BillRecord):
    state: Optional[State] = None
    legislative_body: Optional[LegislativeBody] = None

    model_config = ConfigDict(from_attributes=True)


# Legislators


class LegislatorBase(BaseModel):
    name: str
    image_url: Optional[str]
    district: str
    party_id: int

    address: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    phone: Optional[str] = None
    twitter: Optional[str] = None


class LegislatorCreate(LegislatorBase):
    pass


class Legislator(LegislatorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Users


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    hashed_password: str


class User(UserBase):
    id: int

    followed_bills: List[Bill] = []
    followed_topics: List[Topic] = []

    model_config = ConfigDict(from_attributes=True)

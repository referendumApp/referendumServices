from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import List


# Topics


class TopicBase(BaseModel):
    name: str


class TopicCreate(TopicBase):
    pass


class Topic(TopicBase):
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

    topics: List[Topic] = []

    model_config = ConfigDict(from_attributes=True)


# Bills


class BillBase(BaseModel):
    legiscan_id: int
    identifier: str
    title: str
    description: str
    state: str
    body: str
    session: str
    briefing: str
    status: str
    latest_action: str
    # topics


class BillCreate(BillBase):
    pass


class Bill(BillBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Legislators


class LegislatorBase(BaseModel):
    chamber: str
    district: str
    email: str
    facebook: str
    image_url: str
    instagram: str
    name: str
    office: str
    party: str
    phone: str
    state: str
    twitter: str


class LegislatorCreate(LegislatorBase):
    pass


class Legislator(LegislatorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

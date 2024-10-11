from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List

from .models import VoteChoice, BillActionType


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
    role_id: int
    state_id: int


class LegislativeBodyCreate(LegislativeBodyBase):
    pass


class LegislativeBody(LegislativeBodyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Committee


class CommitteeBase(BaseModel):
    name: str
    legislative_body_id: int


class CommitteeCreate(CommitteeBase):
    pass


class Committee(CommitteeBase):
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


# Legislators


class LegislatorBase(BaseModel):
    legiscan_id: int
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


class LegislatorRecord(LegislatorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class Legislator(LegislatorRecord):
    committees: List[Committee]

    model_config = ConfigDict(from_attributes=True)


# Bill Versions


class BillVersion(BaseModel):
    bill_id: int
    version: int


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

    model_config = ConfigDict(from_attributes=True)


class Bill(BillRecord):
    state: Optional[State] = None
    legislative_body: Optional[LegislativeBody] = None
    topics: List[Topic] = []
    sponsors: List[LegislatorRecord] = []
    versions: List[BillVersion] = []

    model_config = ConfigDict(from_attributes=True)


# Bill Actions


class BillActionBase(BaseModel):
    bill_id: int
    date: date
    type: BillActionType


class BillActionCreate(BillActionBase):
    pass


class BillAction(BillActionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# Users


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    hashed_password: str


class UserReference(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    id: int

    followed_bills: List[Bill] = []
    followed_topics: List[Topic] = []
    followed_legislators: List[Legislator] = []

    model_config = ConfigDict(from_attributes=True)


class VoteBase(BaseModel):
    bill_id: int
    vote_choice: VoteChoice


class UserVoteCreate(VoteBase):
    pass


class UserVote(VoteBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class LegislatorVoteCreate(VoteBase):
    pass


class LegislatorVote(VoteBase):
    legislator_id: int

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    bill_id: int
    parent_id: Optional[int]
    comment: str


class CommentCreate(CommentBase):
    user_id: int


class Comment(CommentCreate):
    id: int

    likes: List[UserReference]

    model_config = ConfigDict(from_attributes=True)

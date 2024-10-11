from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List

from .models import VoteChoice, BillActionType


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Party
class PartyBase(BaseSchema):
    name: str


class PartyCreate(PartyBase):
    pass


class Party(PartyBase):
    id: int


# Role
class RoleBase(BaseSchema):
    name: str


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int


# State
class StateBase(BaseSchema):
    name: str


class StateCreate(StateBase):
    pass


class State(StateBase):
    id: int


# LegislativeBody
class LegislativeBodyBase(BaseSchema):
    role_id: int
    state_id: int


class LegislativeBodyCreate(LegislativeBodyBase):
    pass


class LegislativeBody(LegislativeBodyBase):
    id: int


# Committee
class CommitteeBase(BaseSchema):
    name: str
    legislative_body_id: int


class CommitteeCreate(CommitteeBase):
    pass


class Committee(CommitteeBase):
    id: int


# Topic
class TopicBase(BaseSchema):
    name: str


class TopicCreate(TopicBase):
    pass


class Topic(TopicBase):
    id: int


# Legislator
class LegislatorBase(BaseSchema):
    legiscan_id: int
    name: str
    image_url: Optional[str] = None
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


class Legislator(LegislatorRecord):
    committees: List[Committee] = []


# BillVersion
class BillVersion(BaseSchema):
    bill_id: int
    version: int


# Bill
class BillBase(BaseSchema):
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


class Bill(BillRecord):
    state: Optional[State] = None
    legislative_body: Optional[LegislativeBody] = None
    topics: List[Topic] = []
    sponsors: List[LegislatorRecord] = []
    versions: List[BillVersion] = []


# BillAction
class BillActionBase(BaseSchema):
    bill_id: int
    date: date
    type: BillActionType


class BillActionCreate(BillActionBase):
    pass


class BillAction(BillActionBase):
    id: int


# User
class UserBase(BaseSchema):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    hashed_password: str


class UserReference(UserBase):
    id: int


class User(UserBase):
    id: int
    followed_bills: List[Bill] = []
    followed_topics: List[Topic] = []
    followed_legislators: List[Legislator] = []


# Vote
class VoteBase(BaseSchema):
    bill_id: int
    vote_choice: VoteChoice


class UserVoteCreate(VoteBase):
    pass


class UserVote(VoteBase):
    user_id: int


class LegislatorVoteCreate(VoteBase):
    pass


class LegislatorVote(VoteBase):
    legislator_id: int


# Comment
class CommentBase(BaseSchema):
    bill_id: int
    parent_id: Optional[int] = None
    comment: str


class CommentCreate(CommentBase):
    user_id: int


class Comment(CommentCreate):
    id: int
    likes: List[UserReference] = []

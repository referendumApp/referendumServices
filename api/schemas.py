from datetime import date
from typing import List, Optional
from pydantic import Field, field_validator

from common.database.referendum.schemas import CamelCaseBaseModel, UserBase


class ErrorResponse(CamelCaseBaseModel):
    detail: str


class HealthResponse(CamelCaseBaseModel):
    status: str


class TokenResponse(CamelCaseBaseModel):
    access_token: str
    token_type: str


class TokenData(CamelCaseBaseModel):
    email: Optional[str] = None


class UserCreateInput(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class VoteCount(CamelCaseBaseModel):
    vote_choice_id: int
    count: int


class LegislatorVoteDetail(CamelCaseBaseModel):
    # Action
    bill_action_id: int
    date: date
    action_description: str
    legislative_body_id: int

    # Vote
    legislator_id: int
    legislator_name: str
    party_name: str
    role_name: str
    state_name: str

    vote_choice_name: str


class VoteCountByChoice(CamelCaseBaseModel):
    vote_choice_id: int
    count: int


class VoteCountByParty(CamelCaseBaseModel):
    vote_choice_id: int
    party_id: int
    count: int


class VoteSummary(CamelCaseBaseModel):
    bill_action_id: int
    total_votes: int
    vote_counts_by_choice: List[VoteCountByChoice] = Field(default_factory=list)
    vote_counts_by_party: List[VoteCountByParty] = Field(default_factory=list)


class BillVotingHistory(CamelCaseBaseModel):
    bill_id: int
    votes: List[LegislatorVoteDetail]
    summaries: List[VoteSummary]

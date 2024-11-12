from typing import List, Optional
from pydantic import field_validator

from common.database.referendum.schemas import CamelCaseBaseModel, UserBase, LegislatorVote


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


class BillVotingHistory(CamelCaseBaseModel):
    bill_id: int
    legislator_votes: List[LegislatorVote.Record]
    vote_counts: List[VoteCount]

from datetime import date
from typing import List, Optional
from pydantic import Field, field_validator

from common.database.referendum.schemas import CamelCaseBaseModel, UserBase, Sponsor


class FormErrorModel(CamelCaseBaseModel):
    field: str
    message: str


class FormErrorResponse(CamelCaseBaseModel):
    detail: FormErrorModel


class ErrorResponse(CamelCaseBaseModel):
    detail: str


class HealthResponse(CamelCaseBaseModel):
    status: str


class RefreshToken(CamelCaseBaseModel):
    refresh_token: str


class TokenResponse(CamelCaseBaseModel):
    access_token: str
    refresh_token: str
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

    vote_choice_id: int


class BillActionVote(CamelCaseBaseModel):
    bill_action_id: int
    date: date
    action_description: str
    vote_choice_id: int


class LegislatorVote(CamelCaseBaseModel):
    bill_id: int
    identifier: str
    title: str
    bill_action_votes: List[BillActionVote]


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


class DenormalizedBill(CamelCaseBaseModel):
    """Represents a denormalized view of a bill with all related information."""

    bill_id: int = Field(description="Primary identifier of the bill")
    legiscan_id: int = Field(description="External identifier from LegiScan")
    identifier: str = Field(description="Bill identifier (e.g., 'HB 123')")
    title: str = Field(description="Official title of the bill")
    description: str = Field(description="Full description of the bill")
    briefing: Optional[str] = Field(None, description="Brief summary of the bill")
    current_version_id: int = Field(description="Current version ID of the bill")
    status: str = Field(description="Current status of the bill")
    status_date: date = Field(description="Date of the last status change")
    session_id: int = Field(description="Legislative session")
    state_id: int = Field(description="State identifier")
    state_name: str = Field(description="Name of the state")
    legislative_body_id: int = Field(description="Legislative body identifier")
    legislative_body_role: str = Field(description="Role name of the legislative body")
    sponsors: List[Sponsor.Record] = Field(
        default_factory=list, description="List of all bill sponsors"
    )

    model_config = {
        "from_attributes": True,
    }

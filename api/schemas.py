from datetime import date
from typing import List, Optional, TypeVar, Generic
from pydantic import model_serializer, Field, field_validator

from common.database.referendum.schemas import CamelCaseBaseModel, UserBase


T = TypeVar("T")


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


class FilterOptions(CamelCaseBaseModel):
    party_id: Optional[List[int]] = None
    role_id: Optional[List[int]] = None
    state_id: Optional[List[int]] = None
    status_id: Optional[List[int]] = None

    @model_serializer()
    def exclude_null_fields(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class PaginationParams(CamelCaseBaseModel):
    skip: int = 0
    limit: int = 100
    filter_options: Optional[FilterOptions] = None
    search_query: Optional[str] = None
    order_by: Optional[str] = None


class PaginatedResponse(CamelCaseBaseModel, Generic[T]):
    has_more: bool
    items: List[T]


class LegislatorVote(CamelCaseBaseModel):
    legislator_id: int
    legislator_name: str
    party_name: str
    state_name: str
    role_name: str
    vote_choice_id: int


class LegislatorVoteDetail(CamelCaseBaseModel):
    # Action
    bill_action_id: int
    date: date
    action_description: str
    legislator_votes: List[LegislatorVote]


class BillActionVote(CamelCaseBaseModel):
    bill_action_id: int
    date: date
    action_description: str
    vote_choice_id: int


class LegislatorVotingHistory(CamelCaseBaseModel):
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


class SponsorDetail(CamelCaseBaseModel):
    bill_id: int
    legislator_id: int
    legislator_name: str
    rank: int
    type: str


class DenormalizedBill(CamelCaseBaseModel):
    """Represents a denormalized view of a bill with all related information."""

    bill_id: int = Field(description="Primary identifier of the bill")
    legiscan_id: int = Field(description="External identifier from LegiScan")
    identifier: str = Field(description="Bill identifier (e.g., 'HB 123')")
    title: str = Field(description="Official title of the bill")
    description: str = Field(description="Full description of the bill")
    current_version_id: Optional[int] = Field(None, description="Current version ID of the bill")
    status_id: int = Field(description="ID of current status of the bill")
    status: str = Field(description="Name of current status of the bill")
    status_date: date = Field(description="Date of the last status change")
    session_id: int = Field(description="Legislative session ID")
    session_name: str = Field(description="Legislative session name")
    state_id: int = Field(description="State identifier")
    state_name: str = Field(description="Name of the state")
    legislative_body_id: int = Field(description="Legislative body identifier")
    role_id: int = Field(description="Role ID of the legislative body")
    legislative_body_role: str = Field(description="Role name of the legislative body")
    sponsors: List[SponsorDetail] = Field(
        default_factory=list, description="List of all bill sponsors"
    )

    model_config = {
        "from_attributes": True,
    }


class UserBillVotes(CamelCaseBaseModel):
    yay: int
    nay: int
    yay_pct: float
    nay_pct: float
    total: int

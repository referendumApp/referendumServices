from datetime import date
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import Field, field_validator, model_serializer

from common.database.referendum.schemas import UserBase
from common.core.schemas import CamelCaseBaseModel

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
    user_id: int
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(CamelCaseBaseModel):
    email: Optional[str] = None


class UserCreateInput(UserBase):
    password: str
    settings: Optional[Dict] = {}

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class UserUpdateInput(UserBase):
    password: str
    settings: Dict = {}

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class PasswordResetInput(CamelCaseBaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class UserPasswordResetInput(PasswordResetInput):
    current_password: str


class VoteCount(CamelCaseBaseModel):
    vote_choice_id: int
    count: int


class BaseFilterOptions(CamelCaseBaseModel):
    party_id: Optional[List[int]] = None
    role_id: Optional[List[int]] = None
    state_id: Optional[List[int]] = None
    status_id: Optional[List[int]] = None

    @model_serializer()
    def exclude_null_fields(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BillFilterOptions(BaseFilterOptions):
    status_id: Optional[List[int]] = None


class LegislatorFilterOptions(BaseFilterOptions):
    party_id: Optional[List[int]] = None


class BasePaginationRequestBody(CamelCaseBaseModel):
    skip: int = 0
    limit: int = 100
    search_query: Optional[str] = None
    order_by: Optional[str] = None


class BillPaginationRequestBody(BasePaginationRequestBody):
    filter_options: Optional[BillFilterOptions] = None


class LegislatorPaginationRequestBody(BasePaginationRequestBody):
    filter_options: Optional[LegislatorFilterOptions] = None


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
    yea: int
    nay: int
    yea_pct: float
    nay_pct: float
    total: int


class CommentDetail(CamelCaseBaseModel):
    id: int
    bill_id: int
    user_id: int
    user_name: str
    comment: str
    parent_id: Optional[int] = None


class LegislatorScorecard(CamelCaseBaseModel):
    legislator_id: int
    delinquency: float
    bipartisanship: float


class ChatMessageRequest(CamelCaseBaseModel):
    message: str
    session_id: str


class ChatMessageResponse(CamelCaseBaseModel):
    response: str
    session_id: str

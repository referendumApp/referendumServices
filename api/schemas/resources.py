from datetime import date
from typing import List, Optional

from pydantic import Field

from common.core.schemas import CamelCaseBaseModel


####################
# Vote Summaries
####################


class VoteCount(CamelCaseBaseModel):
    vote_choice_id: int
    count: int


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


####################
# Voting History
####################


class LegislatorVote(CamelCaseBaseModel):
    legislator_id: int
    legislator_name: str
    party_name: str
    state_name: str
    role_name: str
    vote_choice_id: int


class BillActionVote(CamelCaseBaseModel):
    bill_action_id: int
    date: date
    action_description: str
    vote_choice_id: int


class LegislatorVoteDetail(CamelCaseBaseModel):
    bill_action_id: int
    date: date
    action_description: str
    legislator_votes: List[LegislatorVote]


class LegislatorVotingHistory(CamelCaseBaseModel):
    bill_id: int
    identifier: str
    title: str
    bill_action_votes: List[BillActionVote]


class BillVotingHistory(CamelCaseBaseModel):
    bill_id: int
    votes: List[LegislatorVoteDetail]
    summaries: List[VoteSummary]


####################
# Bill Details
####################


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


####################
# Executive Order Details
####################


class DenormalizedExecutiveOrder(CamelCaseBaseModel):
    executive_order_id: int = Field(description="Primary identifier of the executive order")
    title: str = Field(description="Official title of the executive order")
    signed_date: date = Field(description="Date the executive order was signed")
    url: str = Field(description="URL of the official PDF of the executive order")
    hash: str = Field(description="Hash to uniquely identify the text in Referendum")
    briefing: Optional[str] = Field(None, description="Summary of the executive order")
    president_id: int = Field(description="ID of the president who signed the EO")
    president_name: str = Field(description="Name of the president who signed the EO")

    model_config = {
        "from_attributes": True,
    }


####################
# Legislator Details
####################


class LegislatorScorecard(CamelCaseBaseModel):
    legislator_id: int
    delinquency: float
    bipartisanship: float

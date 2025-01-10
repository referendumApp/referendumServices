import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload, load_only

from common.database.referendum import crud, models, schemas

from ..database import get_db
from ..schemas import ErrorResponse, LegislatorVotingHistory
from ..security import CredentialsException, get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislator,
    create_schema=schemas.Legislator.Base,
    update_schema=schemas.Legislator.Record,
    response_schema=schemas.Legislator.Full,
    resource_name="legislator",
)


@router.get(
    "/{legislator_id}/voting_history",
    response_model=List[LegislatorVotingHistory],
    summary="Get legislator voting history",
    responses={
        200: {
            "model": List[LegislatorVotingHistory],
            "description": "Legislator voting history successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_legislator_voting_history(
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> List[LegislatorVotingHistory]:
    try:
        vote_query = (
            select(models.LegislatorVote)
            .options(
                joinedload(models.LegislatorVote.bill_action),
                joinedload(models.LegislatorVote.vote_choice),
            )
            .filter(models.LegislatorVote.legislator_id == legislator_id)
            .order_by(models.LegislatorVote.bill_id.desc())
        )
        vote_results = db.execute(vote_query).scalars().all()

        bill_action_votes = {}
        for vote in vote_results:
            bill_action_votes.setdefault(vote.bill_id, []).append(
                {
                    "bill_action_id": vote.bill_action_id,
                    "date": vote.bill_action.date,
                    "action_description": vote.bill_action.description,
                    "vote_choice_id": vote.vote_choice.id,
                }
            )

        bill_query = (
            select(models.Bill)
            .options(
                load_only(models.Bill.id, models.Bill.identifier, models.Bill.title),
            )
            .filter(models.Bill.id.in_(bill_action_votes.keys()))
            .order_by(models.Bill.id.desc())
        )

        bill_results = db.execute(bill_query).scalars().all()

        legislator_votes = []
        for bill in bill_results:
            legislator_votes.append(
                LegislatorVotingHistory(
                    bill_id=bill.id,
                    identifier=bill.identifier,
                    title=bill.title,
                    bill_action_votes=bill_action_votes[bill.id],
                )
            )

        return legislator_votes
    except CredentialsException as e:
        raise e
    except Exception as e:
        message = (
            f"Failed to get voting history for legislator {legislator_id} with error: {str(e)}"
        )
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)


@dataclass
class VoteData:
    vote_choice_name: str
    bill_action_description: str
    bill_action_id: int
    vote_choice_id: int


@dataclass
class SponsorData:
    bill_status: str


def calculate_legislator_scores(
    vote_results: List[VoteData],
    opposite_party_votes: Dict[Tuple[int, int], int],
    sponsored_bill_statuses: List[str],
) -> Dict[str, float]:
    """
    Calculate various scores for a legislator based on their voting and sponsorship history.

    Args:
        vote_results: List of legislator's votes with associated data
        opposite_party_votes: Dictionary mapping (bill_action_id, vote_choice_id) to count of opposite party votes
        sponsored_bill_statuses: List of statuses for all bills sponsored by the legislator

    Returns:
        Dictionary containing delinquency, bipartisanship, success, and virtue signaling scores
    """
    if not vote_results:
        delinquency_score = None
        bipartisanship_score = None
        success_score = None
    else:
        total_votes = len(vote_results)

        # Calculate delinquency score
        absent_votes = sum(1 for vote in vote_results if vote.vote_choice_name == "absent")
        delinquency_score = absent_votes / total_votes if total_votes > 0 else 0
        delinquency_score = round(delinquency_score, 3)

        # Calculate bipartisanship score
        matching_votes = sum(
            1
            for vote in vote_results
            if (vote.bill_action_id, vote.vote_choice_id) in opposite_party_votes
        )
        bipartisanship_score = matching_votes / total_votes if total_votes > 0 else 0
        bipartisanship_score = round(bipartisanship_score, 3)

        # Calculate success score
        yes_no_votes = [vote for vote in vote_results if vote.vote_choice_name in ["yes", "no"]]
        successful_votes = sum(
            1
            for vote in yes_no_votes
            if (
                (
                    vote.vote_choice_name == "yes"
                    and "passed" in vote.bill_action_description.lower()
                )
                or (
                    vote.vote_choice_name == "no"
                    and "failed" in vote.bill_action_description.lower()
                )
            )
        )
        success_score = successful_votes / len(yes_no_votes) if yes_no_votes else 0
        success_score = round(success_score, 3)

    # Calculate virtue signaling score
    total_sponsored = len(sponsored_bill_statuses)
    failed_at_first = sum(
        1 for status in sponsored_bill_statuses if status.lower().startswith("introduced")
    )
    virtue_signaling_score = failed_at_first / total_sponsored if total_sponsored > 0 else 0
    virtue_signaling_score = round(virtue_signaling_score, 3)

    return {
        "delinquency": delinquency_score,
        "bipartisanship": bipartisanship_score,
        "success": success_score,
        "virtue_signaling": virtue_signaling_score,
    }


@router.get(
    "/{legislator_id}/scores",
    response_model=Dict,
    summary="Get legislator scores",
    responses={
        200: {
            "model": Dict,
            "description": "Legislator scores successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_legislator_scores(
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    try:
        # Get all legislator votes
        vote_query = (
            select(models.LegislatorVote)
            .options(
                joinedload(models.LegislatorVote.vote_choice),
                joinedload(models.LegislatorVote.bill_action),
                joinedload(models.LegislatorVote.legislator).load_only(models.Legislator.party_id),
            )
            .filter(models.LegislatorVote.legislator_id == legislator_id)
        )
        vote_results = db.execute(vote_query).scalars().all()

        vote_data = [
            VoteData(
                vote_choice_name=vote.vote_choice.name,
                bill_action_description=vote.bill_action.description,
                bill_action_id=vote.bill_action_id,
                vote_choice_id=vote.vote_choice_id,
            )
            for vote in vote_results
        ]

        if vote_results:
            # Get all opposite party votes
            opposite_party_query = (
                select(
                    models.LegislatorVote.bill_action_id,
                    models.LegislatorVote.vote_choice_id,
                    func.count().label("vote_count"),
                )
                .join(models.Legislator)
                .join(models.VoteChoice)
                .filter(
                    models.Legislator.party_id != vote_results[0].legislator.party_id,
                    models.VoteChoice.name.in_(["yes", "no"]),
                )
                .group_by(
                    models.LegislatorVote.bill_action_id, models.LegislatorVote.vote_choice_id
                )
            )
            opposite_votes = {
                (row.bill_action_id, row.vote_choice_id): row.vote_count
                for row in db.execute(opposite_party_query).all()
            }
        else:
            opposite_votes = {}

        # Get all sponsored bills in one query
        sponsor_query = (
            select(models.Sponsor)
            .options(joinedload(models.Sponsor.bill).joinedload(models.Bill.status))
            .filter(models.Sponsor.legislator_id == legislator_id)
        )
        sponsored_bills = db.execute(sponsor_query).scalars().all()

        # Get statuses for all sponsored bills
        sponsored_bill_statuses = [sponsor.bill.status.name for sponsor in sponsored_bills]

        return calculate_legislator_scores(vote_data, opposite_votes, sponsored_bill_statuses)

    except CredentialsException as e:
        raise e
    except Exception as e:
        message = f"Failed to get scores for legislator {legislator_id} with error: {str(e)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

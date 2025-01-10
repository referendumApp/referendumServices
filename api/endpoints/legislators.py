import logging
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, and_, exists
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


def calculate_legislator_scores(
    votes: List[models.LegislatorVote],
    opposite_party_votes: Dict[Tuple[int, int], int],
) -> Dict[str, float | None]:
    if not votes:
        return {"delinquency": None, "bipartisanship": None}

    total_votes = len(votes)
    absent_votes = sum(vote.vote_choice_id == 4 for vote in votes)
    matching_votes = sum(
        (vote.bill_action_id, vote.vote_choice_id) in opposite_party_votes for vote in votes
    )

    # TODO - Calculate success score (% of votes that go the way this legislator voted)
    # TODO - Calculate virtue signaling score (% of bills introduced by this legislator that go nowhere that go the way
    scores = {
        "delinquency": absent_votes / total_votes,
        "bipartisanship": matching_votes / total_votes,
    }

    return {k: round(v, 3) for k, v in scores.items()}


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
        # Get total votes, absent votes, and bipartisan matches in one query
        stats_query = (
            select(
                func.count().label("total_votes"),
                func.sum(models.LegislatorVote.vote_choice_id == 4).label("absent_votes"),
                func.sum(
                    and_(
                        # Join to get opposite party votes for same bill
                        exists(
                            select(1)
                            .select_from(models.LegislatorVote)
                            .join(models.Legislator)
                            .join(models.VoteChoice)
                            .where(
                                and_(
                                    models.LegislatorVote.bill_action_id
                                    == models.LegislatorVote.bill_action_id,
                                    models.Legislator.party_id != models.Legislator.party_id,
                                    models.VoteChoice.name.in_(["yes", "no"]),
                                    models.LegislatorVote.vote_choice_id
                                    == models.LegislatorVote.vote_choice_id,
                                )
                            )
                        )
                    )
                ).label("matching_votes"),
            )
            .select_from(models.LegislatorVote)
            .join(models.Legislator)
            .filter(models.LegislatorVote.legislator_id == legislator_id)
        )

        result = db.execute(stats_query).first()

        if not result or result.total_votes == 0:
            return {"delinquency": None, "bipartisanship": None}

        return {
            "delinquency": round(result.absent_votes / result.total_votes, 3),
            "bipartisanship": round(result.matching_votes / result.total_votes, 3),
        }

    except CredentialsException as e:
        raise e
    except Exception as e:
        message = f"Failed to get scores for legislator {legislator_id} with error: {str(e)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

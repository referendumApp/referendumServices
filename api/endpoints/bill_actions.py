import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from common.database.referendum import crud, models, schemas

from ..database import get_db
from ..schemas import BillActionVotingHistory, ErrorResponse
from ..security import CredentialsException, get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/{bill_action_id}/voting_history",
    response_model=BillActionVotingHistory,
    summary="Get bill action voting history",
    responses={
        200: {
            "model": BillActionVotingHistory,
            "description": "Legislator voting history successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_action_voting_history(
    bill_action_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> BillActionVotingHistory:
    try:
        vote_query = (
            select(models.LegislatorVote)
            .options(joinedload(models.LegislatorVote.legislator))
            .filter(models.LegislatorVote.bill_action_id == bill_action_id)
            # .order_by(models.LegislatorVote.bill_id.desc())
        )

        vote_results = db.execute(vote_query).scalars().all()

        legislator_votes = []
        for vote in vote_results:
            legislator_votes.append(
                {
                    "legislator_id": vote.legislator.id,
                    "legislator_name": vote.legislator.name,
                    "party_name": vote.legislator.party.name,
                    "vote_choice_id": vote.vote_choice_id,
                }
            )

        bill_action_voting = BillActionVotingHistory(
            bill_action_id=bill_action_id, legislator_vote=legislator_votes
        )

        return bill_action_voting
    except CredentialsException as e:
        raise e
    except Exception as e:
        message = (
            f"Failed to get voting history for bill action {bill_action_id} with error: {str(e)}"
        )
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_action,
    create_schema=schemas.BillAction.Base,
    update_schema=schemas.BillAction.Record,
    response_schema=schemas.BillAction.Full,
    resource_name="bill_action",
)

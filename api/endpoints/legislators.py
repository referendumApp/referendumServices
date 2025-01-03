import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, load_only

from common.database.referendum import crud, models, schemas

from ..database import get_db
from ..schemas import ErrorResponse, LegislatorVotingHistory, PaginatedResponse
from ..security import CredentialsException, get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[schemas.Legislator.Full],
    summary="Get all legislators",
    responses={
        200: {
            "model": PaginatedResponse[schemas.Legislator.Full],
            "description": "legislators successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_legislators(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    logger.info(f"Attempting to read all legislators (skip: {skip}, limit: {limit})")
    try:
        legislators = crud.legislator.read_all(db=db, skip=skip, limit=limit + 1)
        if len(legislators) > limit:
            has_more = True
            legislators.pop()
        else:
            has_more = False

        return {"has_more": has_more, "items": legislators}
    except crud.DatabaseException as e:
        logger.error(f"Database error while reading all legislators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
            "model": LegislatorVotingHistory,
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

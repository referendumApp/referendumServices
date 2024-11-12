from collections import Counter, defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import ObjectNotFoundException, DatabaseException

from ..database import get_db
from ..schemas import (
    ErrorResponse,
    BillVotingHistory,
    LegislatorVoteDetail,
    VoteSummary,
    VoteCountByParty,
    VoteCountByChoice,
)
from ..security import get_current_user_or_verify_system_token, verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill,
    create_schema=schemas.Bill.Base,
    update_schema=schemas.Bill.Record,
    response_schema=schemas.Bill.Full,
    resource_name="bill",
)


@router.get(
    "/{bill_id}/bill_versions",
    response_model=List[schemas.BillVersion.Record],
    summary="Get bill versions",
    responses={
        200: {
            "model": Dict[str, str | int],
            "description": "Bill versions successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_versions(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill = crud.bill.read(db=db, obj_id=bill_id)
    return bill.bill_versions


@router.get(
    "/{bill_id}/voting_history",
    response_model=BillVotingHistory,
    summary="Get bill voting history",
    responses={
        200: {
            "model": BillVotingHistory,
            "description": "Bill voting history successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_voting_history(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> BillVotingHistory:
    try:
        # Get bill details
        bill = crud.bill.read(db=db, obj_id=bill_id)
        if not bill:
            raise HTTPException(status_code=404, detail=f"Bill {bill_id} not found")

        # Build the complex query
        query = (
            select(
                models.LegislatorVote,
                models.BillAction.date,
                models.BillAction.description,
                models.BillAction.legislative_body_id,
                models.VoteChoice.id.label("vote_choice_id"),
                models.VoteChoice.name.label("vote_choice_name"),
                models.Legislator.name.label("legislator_name"),
                models.Party.id.label("party_id"),
                models.Party.name.label("party_name"),
                models.Role.name.label("role_name"),
                models.State.name.label("state_name"),
            )
            .join(models.BillAction, models.LegislatorVote.bill_action_id == models.BillAction.id)
            .join(models.VoteChoice, models.LegislatorVote.vote_choice_id == models.VoteChoice.id)
            .join(models.Legislator, models.LegislatorVote.legislator_id == models.Legislator.id)
            .join(models.Party, models.Legislator.party_id == models.Party.id)
            .join(models.Role, models.Legislator.role_id == models.Role.id)
            .join(models.State, models.Legislator.state_id == models.State.id)
            .filter(models.LegislatorVote.bill_id == bill_id)
        )

        results = db.execute(query).fetchall()

        all_legislator_votes = []
        vote_summaries_by_action = defaultdict(
            lambda: {
                "total_votes": 0,
                "vote_choice_counter": Counter(),
                "party_vote_counter": Counter(),
            }
        )
        for row in results:
            vote_detail = LegislatorVoteDetail(
                bill_action_id=row.LegislatorVote.bill_action_id,
                date=row.date,
                action_description=row.description,
                legislative_body_id=row.legislative_body_id,
                legislator_id=row.LegislatorVote.legislator_id,
                legislator_name=row.legislator_name,
                party_name=row.party_name,
                role_name=row.role_name,
                state_name=row.state_name,
                vote_choice_name=row.vote_choice_name,
            )
            all_legislator_votes.append(vote_detail)

            action_summary = vote_summaries_by_action[row.LegislatorVote.bill_action_id]
            action_summary["total_votes"] += 1
            action_summary["vote_choice_counter"][row.vote_choice_id] += 1
            action_summary["party_vote_counter"][(row.party_id, row.vote_choice_id)] += 1

        # Convert summaries to VoteSummary objects
        summaries = []
        for action_id, summary_data in vote_summaries_by_action.items():
            vote_counts_by_choice = [
                VoteCountByChoice(vote_choice_id=vote_choice_id, count=count)
                for vote_choice_id, count in summary_data["vote_choice_counter"].items()
            ]

            vote_counts_by_party = [
                VoteCountByParty(vote_choice_id=vote_choice_id, party_id=party_id, count=count)
                for (party_id, vote_choice_id), count in summary_data["party_vote_counter"].items()
            ]

            summaries.append(
                VoteSummary(
                    bill_action_id=action_id,
                    total_votes=summary_data["total_votes"],
                    vote_counts_by_choice=vote_counts_by_choice,
                    vote_counts_by_party=vote_counts_by_party,
                )
            )

        return BillVotingHistory(bill_id=bill_id, votes=all_legislator_votes, summaries=summaries)
    except Exception as e:
        message = f"Failed to get voting history for bill {bill_id} with error: {str(e)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)


@router.post(
    "/{bill_id}/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add topic to a bill",
    responses={
        204: {"description": "Topic successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def add_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to add topic {topic_id} to bill {bill_id}")
    try:
        crud.bill.add_topic(db=db, bill_id=bill_id, topic_id=topic_id)
        logger.info(f"Topic {topic_id} successfully added to bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error adding topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error adding topic: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while adding topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{bill_id}/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove topic from a bill",
    responses={
        204: {"description": "Topic successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def remove_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to remove topic {topic_id} from bill {bill_id}")
    try:
        crud.bill.remove_topic(db=db, bill_id=bill_id, topic_id=topic_id)
        logger.info(f"Topic {topic_id} successfully removed from bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error removing topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while removing topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{bill_id}/sponsors/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add sponsor to a bill",
    responses={
        204: {"description": "Sponsor successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def add_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to add sponsor legislator {legislator_id} to bill {bill_id}")
    try:
        crud.bill.add_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
        logger.info(f"Sponsor {legislator_id} successfully added to bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error adding sponsor: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error adding sponsor: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while adding sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{bill_id}/sponsors/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove sponsor from a bill",
    responses={
        204: {"description": "Sponsor successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def remove_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to remove sponsor legislator {legislator_id} from bill {bill_id}")
    try:
        crud.bill.remove_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
        logger.info(f"Sponsor {legislator_id} successfully removed from bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error removing sponsor: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error removing sponsor: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while removing sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, load_only

from common.database.referendum import crud, models, schemas
from common.database.referendum.crud import DatabaseException, ObjectNotFoundException

from ..database import get_db
from ..schemas import (
    BillVotingHistory,
    DenormalizedBill,
    ErrorResponse,
    LegislatorVote,
    LegislatorVoteDetail,
    UserBillVotes,
    VoteCountByChoice,
    VoteCountByParty,
    VoteSummary,
)
from ..security import (
    CredentialsException,
    get_current_user_or_verify_system_token,
    verify_system_token,
)
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


# Note that this must be defined before adding crud routes to avoid conflicts with the GET /id endpoint
@router.get(
    "/details",
    response_model=List[DenormalizedBill],
    summary="Get all bill details",
    responses={
        200: {
            "model": List[DenormalizedBill],
            "description": "Bill details successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_details(
    skip: int | None = None,
    limit: int | None = None,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    try:
        bills = crud.bill.read_all_denormalized(db=db, skip=skip, limit=limit)
        result = []
        for bill in bills:
            sponsors = [
                {
                    "bill_id": sponsor.bill_id,
                    "legislator_id": sponsor.legislator_id,
                    "legislator_name": sponsor.legislator.name,
                    "rank": sponsor.rank,
                    "type": sponsor.type,
                }
                for sponsor in bill.sponsors
            ]
            bill_dict = {
                "bill_id": bill.id,
                "legiscan_id": bill.legiscan_id,
                "identifier": bill.identifier,
                "title": bill.title,
                "description": bill.description,
                "status_id": bill.status.id,
                "status": bill.status.name,
                "status_date": bill.status_date,
                "session_id": bill.session.id,
                "session_name": bill.session.name,
                "state_id": bill.state.id,
                "state_name": bill.state.name,
                "current_version_id": bill.current_version_id,
                "legislative_body_id": bill.legislative_body.id,
                "role_id": bill.legislative_body.role.id,
                "legislative_body_role": bill.legislative_body.role.name,
                "sponsors": sponsors,
            }
            result.append(bill_dict)
        return result
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


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
    "/{bill_id}/user_votes",
    response_model=UserBillVotes,
    summary="Get user vote counts for a bill",
    responses={
        200: {
            "model": UserBillVotes,
            "description": "Vote counts successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_vote_counts(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    bill_votes = crud.bill.get_bill_user_votes(db, bill_id)
    return bill_votes


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
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_voting_history(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> BillVotingHistory:
    try:
        query = (
            select(models.LegislatorVote)
            .options(
                joinedload(models.LegislatorVote.vote_choice),
                joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.party),
                joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.role),
                joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.state),
            )
            .filter(models.LegislatorVote.bill_id == bill_id)
        )

        results = db.execute(query).scalars().all()

        all_legislator_votes = {}
        vote_summaries_by_action = defaultdict(
            lambda: {
                "total_votes": 0,
                "vote_choice_counter": Counter(),
                "party_vote_counter": Counter(),
            }
        )
        for vote in results:
            all_legislator_votes.setdefault(vote.bill_action_id, []).append(
                LegislatorVote(
                    legislator_id=vote.legislator.id,
                    legislator_name=vote.legislator.name,
                    party_name=vote.legislator.party.name,
                    state_name=vote.legislator.state.name,
                    role_name=vote.legislator.role.name,
                    vote_choice_id=vote.vote_choice.id,
                )
            )

            running_summary = vote_summaries_by_action[vote.bill_action_id]
            running_summary["total_votes"] += 1
            running_summary["vote_choice_counter"][vote.vote_choice_id] += 1
            running_summary["party_vote_counter"][
                (vote.legislator.party_id, vote.vote_choice_id)
            ] += 1

        bill_action_query = (
            select(models.BillAction)
            .options(
                load_only(
                    models.BillAction.id, models.BillAction.date, models.BillAction.description
                ),
            )
            .filter(models.BillAction.id.in_(all_legislator_votes.keys()))
            .order_by(models.BillAction.id.desc(), models.BillAction.date.desc())
        )

        bill_action_results = db.execute(bill_action_query).scalars().all()

        legislator_vote_detail = []
        for bill_action in bill_action_results:
            legislator_vote_detail.append(
                LegislatorVoteDetail(
                    bill_action_id=bill_action.id,
                    date=bill_action.date,
                    action_description=bill_action.description,
                    legislator_votes=all_legislator_votes[bill_action.id],
                )
            )

        summaries = [
            VoteSummary(
                bill_action_id=action_id,
                total_votes=summary_data["total_votes"],
                vote_counts_by_choice=[
                    VoteCountByChoice(vote_choice_id=choice_id, count=count)
                    for choice_id, count in summary_data["vote_choice_counter"].items()
                ],
                vote_counts_by_party=[
                    VoteCountByParty(vote_choice_id=vote_choice_id, party_id=party_id, count=count)
                    for (party_id, vote_choice_id), count in summary_data[
                        "party_vote_counter"
                    ].items()
                ],
            )
            for action_id, summary_data in vote_summaries_by_action.items()
        ]

        return BillVotingHistory(bill_id=bill_id, votes=legislator_vote_detail, summaries=summaries)
    except CredentialsException as e:
        raise e
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

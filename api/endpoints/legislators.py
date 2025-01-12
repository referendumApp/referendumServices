import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload, load_only

from common.database.referendum import crud, models, schemas, utils

from ..constants import ABSENT_VOTE_ID, NAY_VOTE_ID, YEA_VOTE_ID
from ..database import get_db
from ..schemas import (
    ErrorResponse,
    LegislatorScorecard,
    LegislatorVotingHistory,
    PaginatedResponse,
    PaginationParams,
)
from ..security import CredentialsException, get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
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
    request_body: PaginationParams,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    logger.info(
        f"Attempting to read all legislators (skip: {request_body.skip}, limit: {request_body.limit})"
    )
    try:
        column_filter = (
            utils.create_column_filter(
                model=models.Legislator,
                filter_options=request_body.filter_options,
            )
            if request_body.filter_options
            else None
        )

        order_by = [request_body.order_by] if request_body.order_by else []
        search_filter = None
        if request_body.search_query:
            search_filter = utils.create_search_filter(
                search_query=request_body.search_query,
                search_config=utils.SearchConfig.ENGLISH,
                fields=[models.Legislator.name],
            )
            order_by.insert(0, "id")

        legislators = crud.legislator.read_all(
            db=db,
            skip=request_body.skip,
            limit=request_body.limit + 1,
            column_filter=column_filter,
            search_filter=search_filter,
            order_by=order_by,
        )
        if len(legislators) > request_body.limit:
            has_more = True
            legislators.pop()
        else:
            has_more = False

        return {"has_more": has_more, "items": legislators}
    except crud.DatabaseException as e:
        logger.error(f"Database error while reading all legislators: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise


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


@router.get(
    "/{legislator_id}/scores",
    response_model=LegislatorScorecard,
    summary="Get legislator scores",
    responses={
        200: {
            "model": LegislatorScorecard,
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
) -> LegislatorScorecard:
    try:
        # TODO - cache this and/or the subquery
        # TODO - Calculate success score (% of votes that go the way this legislator voted)
        # TODO - Calculate virtue signaling score (% of bills introduced by this legislator that go nowhere that go the way
        r = db.execute(
            text(
                """
                WITH legislator_party AS (
                    SELECT party_id FROM legislators WHERE id = :legislator_id
                ),
                opposition_majorities AS (
                    SELECT 
                        v1.bill_action_id,
                        v1.vote_choice_id as majority_choice
                    FROM vote_counts_by_party v1
                    -- Get counts from opposition party
                    WHERE v1.party_id != (SELECT party_id FROM legislator_party)
                    AND v1.vote_choice_id IN (:yea_vote_id, :nay_vote_id)
                    -- Only include votes where this choice had more support than opposition
                    AND NOT EXISTS (
                        SELECT 1 FROM vote_counts_by_party v2
                        WHERE v2.bill_action_id = v1.bill_action_id
                        AND v2.party_id = v1.party_id
                        AND v2.vote_choice_id IN (:yea_vote_id, :nay_vote_id)
                        AND v2.vote_choice_id != v1.vote_choice_id
                        AND v2.vote_count >= v1.vote_count
                    )
                )
                SELECT 
                    -- Delinquency Score: Absent votes (vote_choice_id=4) divided by total votes
                    COALESCE(
                        CAST(COUNT(CASE WHEN lv.vote_choice_id = :absent_vote_id THEN 1 END) AS FLOAT) / 
                        NULLIF(COUNT(*), 0), 
                        0
                    ) as delinquency,
    
                    -- Bipartisanship Score: Times voting with opposition majority / 
                    -- Number of bills where opposition had a majority
                    COALESCE(
                        CAST(
                            COUNT(CASE WHEN lv.vote_choice_id = om.majority_choice THEN 1 END) AS FLOAT
                        ) / 
                        NULLIF(
                            COUNT(CASE WHEN om.majority_choice IS NOT NULL THEN 1 END),
                            0
                        ),
                        0
                    ) as bipartisanship
                FROM legislator_votes lv
                LEFT JOIN opposition_majorities om ON om.bill_action_id = lv.bill_action_id
                WHERE lv.legislator_id = :legislator_id
            """
            ),
            {
                "legislator_id": legislator_id,
                "yea_vote_id": YEA_VOTE_ID,
                "nay_vote_id": NAY_VOTE_ID,
                "absent_vote_id": ABSENT_VOTE_ID,
            },
        )
        delinquency, bipartisanship = r.all()[0]

        return LegislatorScorecard(
            legislator_id=legislator_id,
            delinquency=round(delinquency, 3),
            bipartisanship=round(bipartisanship, 3),
        )
    except CredentialsException as e:
        raise e
    except Exception as e:
        message = f"Failed to get scores for legislator {legislator_id} with error: {str(e)}"
        logger.error(message)
        raise HTTPException(status_code=500, detail=message)

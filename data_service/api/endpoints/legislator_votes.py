from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import logging

from common.database.referendum import crud, schemas
from common.database.referendum.crud import ObjectNotFoundException, DatabaseException

from ..database import get_db
from ..schemas.interactions import ErrorResponse
from ..security import verify_system_token
from ._core import handle_general_exceptions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put(
    "/",
    status_code=status.HTTP_200_OK,
    summary=f"Create a legislator_vote",
    response_model=schemas.LegislatorVote.Record,
    responses={
        200: {
            "model": schemas.LegislatorVote.Record,
            "description": "legislator_vote successfully created",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {
            "model": ErrorResponse,
            "description": f"legislator_vote not found",
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def create_or_update_legislator_vote(
    legislator_vote: schemas.LegislatorVote.Base,
    db: Session = Depends(get_db),
    _: dict[str, Any] = Depends(verify_system_token),
):
    return crud.legislator_vote.create_or_update_vote(db, legislator_vote)


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary=f"Delete a legislator_vote",
    responses={
        204: {"description": "legislator_vote successfully deleted"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {
            "model": ErrorResponse,
            "description": f"legislator_vote not found",
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def delete_legislator_vote(
    bill_action_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: dict[str, Any] = Depends(verify_system_token),
):
    try:
        crud.legislator_vote.delete_vote(
            db=db, bill_action_id=bill_action_id, legislator_id=legislator_id
        )
        return
    except ObjectNotFoundException:
        message = f"Vote not found for bill_action {bill_action_id} for legislator {legislator_id}"
        logger.warning(message)
        raise HTTPException(
            status_code=404,
            detail=message,
        )

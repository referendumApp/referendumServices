from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from common.database.referendum import crud, schemas

from ..database import get_db
from ..schemas.interactions import ErrorResponse
from ..security import get_current_user_or_verify_system_token, verify_system_token
from ._core import EndpointGenerator, handle_crud_exceptions


logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.committee,
    create_schema=schemas.Committee.Base,
    update_schema=schemas.Committee.Record,
    response_schema=schemas.Committee.Full,
    resource_name="committee",
)


@router.get(
    "/{committee_id}/legislators",
    response_model=List[schemas.Legislator.Record],
    summary="Get committee legislators",
    responses={
        200: {
            "model": List[schemas.Legislator.Record],
            "description": "Committee legislators successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Committee not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("committee")
async def get_committee_legislators(
    committee_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    return crud.committee.get_legislators(db=db, committee_id=committee_id)


@router.post(
    "/{committee_id}/legislators/{legislator_id}",
    summary="Add legislator to committee",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Legislator successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Committee not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("committee")
async def add_legislator_membership(
    committee_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    return crud.committee.add_legislator_membership(
        db=db, committee_id=committee_id, legislator_id=legislator_id
    )


@router.delete(
    "/{committee_id}/legislators/{legislator_id}",
    summary="Remove legislator from committee",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Legislator successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Committee not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("committee")
async def remove_legislator_membership(
    committee_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    return crud.committee.remove_legislator_membership(
        db=db, committee_id=committee_id, legislator_id=legislator_id
    )

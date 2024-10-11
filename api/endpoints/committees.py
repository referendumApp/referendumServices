from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from common.database.referendum import crud, schemas
from common.database.referendum.crud import DatabaseException, ObjectNotFoundException

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user_or_verify_system_token, verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.committee,
    create_schema=schemas.CommitteeCreate,
    update_schema=schemas.Committee,
    response_schema=schemas.Committee,
    resource_name="committee",
)


@router.get(
    "/{committee_id}/legislators",
    response_model=List[schemas.LegislatorRecord],
    summary="Get committee legislators",
    responses={
        200:
            {
                "model": List[schemas.LegislatorRecord],
                "description": "Committee legislators successfully retrieved",
            },
        401: {
            "model": ErrorResponse,
            "description": "Not authorized"
        },
        404: {
            "model": ErrorResponse,
            "description": "Committee not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def get_committee_legislators(
    committee_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    try:
        return crud.committee.get_legislators(db=db, committee_id=committee_id)
    except ObjectNotFoundException:
        logger.warning(
            f"Attempt to read non-existent committee with ID: {committee_id}"
        )
        raise HTTPException(
            status_code=404, detail=f"Committee not found for id: {committee_id}"
        )
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{committee_id}/legislators/{legislator_id}",
    summary="Add legislator to committee",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Legislator successfully added"
        },
        401: {
            "model": ErrorResponse,
            "description": "Not authorized"
        },
        404: {
            "model": ErrorResponse,
            "description": "Committee not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def add_legislator_membership(
    committee_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.committee.add_legislator_membership(
            db=db, committee_id=committee_id, legislator_id=legislator_id
        )
    except ObjectNotFoundException:
        logger.warning(
            f"Attempt to read non-existent committee with ID: {committee_id}"
        )
        raise HTTPException(
            status_code=404, detail=f"Committee not found for id: {committee_id}"
        )
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{committee_id}/legislators/{legislator_id}",
    summary="Remove legislator from committee",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {
            "description": "Legislator successfully removed"
        },
        401: {
            "model": ErrorResponse,
            "description": "Not authorized"
        },
        404: {
            "model": ErrorResponse,
            "description": "Committee not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def remove_legislator_membership(
    committee_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.committee.remove_legislator_membership(
            db=db, committee_id=committee_id, legislator_id=legislator_id
        )
    except ObjectNotFoundException:
        logger.warning(
            f"Attempt to read non-existent committee with ID: {committee_id}"
        )
        raise HTTPException(
            status_code=404, detail=f"Committee not found for id: {committee_id}"
        )
    except DatabaseException as e:
        logger.error(f"Database error while retrieving user topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectAlreadyExistsException,
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..security import get_current_user_or_verify_system_token, verify_system_token
from ..schemas import ErrorResponse


router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Party],
    status_code=status.HTTP_200_OK,
    summary="Get all parties",
    responses={},
)
async def get_all_parties(
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> List[models.Party]:
    try:
        return crud.party.read_all(db=db)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/",
    response_model=schemas.Party,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new party",
    responses={
        201: {"model": schemas.Party, "description": "Party successfully created"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        409: {"model": ErrorResponse, "description": "Party already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_party(
    party: schemas.PartyCreate,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Party:
    try:
        return crud.party.create(db=db, obj_in=party)
    except ObjectAlreadyExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"Party already exists for legiscan_id: {party.legiscan_id}",
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{party_id}",
    response_model=schemas.Party,
    summary="Get party information",
    responses={
        200: {"model": schemas.Party, "description": "Party retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Party not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def read_party(
    party_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Party:
    try:
        return crud.party.read(db=db, obj_id=party_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Party not found for ID: {party_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.Party,
    summary="Update party information",
    responses={
        200: {
            "model": schemas.Party,
            "description": "Party information successfully updated",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Party not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_party(
    party: schemas.Party,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Party:
    try:
        db_party = crud.party.read(db=db, obj_id=party.id)
        return crud.party.update(db=db, db_obj=db_party, obj_in=party)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Party not found for ID: {party.id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{party_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a party",
    responses={
        204: {"description": "Party successfully deleted"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Party not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_party(
    party_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.party.delete(db=db, obj_id=party_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Party not found for ID: {party_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

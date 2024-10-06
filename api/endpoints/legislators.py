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
    response_model=List[schemas.Legislator],
    status_code=status.HTTP_200_OK,
    summary="Get all legislators",
    responses={},
)
async def get_all_legislators(
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> List[models.Legislator]:
    try:
        return crud.legislator.read_all(db=db)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/",
    response_model=schemas.Legislator,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new legislator",
    responses={
        201: {
            "model": schemas.Legislator,
            "description": "Legislator successfully created",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        409: {"model": ErrorResponse, "description": "Legislator already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_legislator(
    legislator: schemas.LegislatorCreate,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Legislator:
    try:
        return crud.legislator.create(db=db, obj_in=legislator)
    except ObjectAlreadyExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"Legislator already exists for: {legislator.name}, {legislator.district}",
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{legislator_id}",
    response_model=schemas.Legislator,
    summary="Get legislator information",
    responses={
        200: {"model": schemas.Legislator, "description": "Legislator retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def read_legislator(
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Legislator:
    try:
        return crud.legislator.read(db=db, obj_id=legislator_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Legislator not found for ID: {legislator_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put(
    "/",
    response_model=schemas.Legislator,
    summary="Update legislator information",
    responses={
        200: {
            "model": schemas.Legislator,
            "description": "Legislator information successfully updated",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_legislator(
    legislator: schemas.Legislator,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Legislator:
    try:
        db_legislator = crud.legislator.read(db=db, obj_id=legislator.id)
        return crud.legislator.update(db=db, db_obj=db_legislator, obj_in=legislator)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Legislator not found for ID: {legislator.id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a legislator",
    responses={
        204: {"description": "Legislator successfully deleted"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_legislator(
    legislator_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.legislator.delete(db=db, obj_id=legislator_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Legislator not found for ID: {legislator_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

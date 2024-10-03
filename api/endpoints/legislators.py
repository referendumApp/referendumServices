from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.database.referendum import crud, schemas, models

from ..database import get_db
from .authentication import get_current_user_or_verify_system_token

router = APIRouter()


@router.put(
    "/legislators",
    response_model=schemas.Legislator,
    summary="Add a new legislator",
    description="Add a new legislator to the system. This endpoint is restricted to system token authentication only.",
    responses={
        200: {"description": "Legislator successfully created"},
        400: {"description": "Legislator already exists"},
        403: {"description": "Only system token can create legislators"},
    },
)
async def add_legislator(
    legislator: schemas.LegislatorCreate,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Legislator:
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can create legislators.")
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        raise HTTPException(status_code=400, detail="Legislator already exists.")
    return crud.create_legislator(db=db, legislator=legislator)


@router.post(
    "/legislators",
    response_model=schemas.Legislator,
    summary="Update legislator information",
    description="Update an existing legislator's information. This endpoint is restricted to system token authentication only.",
    responses={
        200: {"description": "Legislator information successfully updated"},
        403: {"description": "Only system token can update legislators"},
        404: {"description": "Legislator not found"},
    },
)
async def update_legislator(
    legislator: schemas.Legislator,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Legislator:
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can update legislators.")
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        update_data = legislator.model_dump()
        for key, value in update_data.items():
            setattr(db_legislator, key, value)
        return crud.update_legislator(db=db, db_legislator=db_legislator)
    raise HTTPException(status_code=404, detail=f"Could not update legislator ID: {legislator.id}.")


@router.get(
    "/legislators/{legislator_id}",
    response_model=schemas.Legislator,
    summary="Get legislator information",
    description="Retrieve a legislator's information by their ID. This endpoint requires authentication.",
    responses={
        200: {"description": "Legislator information successfully retrieved"},
        404: {"description": "Legislator not found"},
    },
)
async def get_legislator(
    legislator_id: int, db: Session = Depends(get_db), _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> models.Legislator:
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator:
        return db_legislator
    raise HTTPException(status_code=404, detail=f"Legislator not found for ID: {legislator_id}.")


@router.delete(
    "/legislators/{legislator_id}",
    summary="Delete a legislator",
    description="Delete a legislator from the system. This endpoint is restricted to system token authentication only.",
    responses={
        200: {"description": "Legislator successfully deleted"},
        403: {"description": "Only system token can delete legislators"},
        404: {"description": "Legislator not found"},
    },
)
async def delete_legislator(
    legislator_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can delete legislators.")
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator is None:
        raise HTTPException(status_code=404, detail=f"Legislator not found for ID: {legislator_id}.")
    return crud.delete_legislator(db, legislator_id=legislator_id)

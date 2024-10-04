from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectNotFoundException,
    DatabaseException,
)

from ..database import get_db
from ..security import get_current_user_or_verify_system_token, verify_system_token


router = APIRouter()


@router.put(
    "/bills",
    response_model=schemas.Bill,
    summary="Add a new bill",
    description="Add a new bill to the system.",
    responses={
        200: {"description": "Bill successfully created"},
        403: {"description": "Forbidden"},
        409: {"description": "Bill already exists"},
        500: {"description": "Internal server error"},
    },
)
async def add_bill(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Bill:
    try:
        crud.bill.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
        raise HTTPException(status_code=409, detail="Bill already exists.")
    except ObjectNotFoundException:
        try:
            return crud.bill.create(db=db, obj_in=bill)
        except DatabaseException as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/bills",
    response_model=schemas.Bill,
    summary="Update bill information",
    description="Update an existing bill's information.",
    responses={
        200: {"description": "Bill information successfully updated"},
        403: {"description": "Forbidden"},
        404: {"description": "Bill not found"},
        500: {"description": "Internal server error"},
    },
)
async def update_bill(
    bill: schemas.Bill,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Bill:
    try:
        db_bill = crud.bill.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
        return crud.bill.update(db=db, db_obj=db_bill, obj_in=bill)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Bill not found for ID: {bill.id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/bills/{bill_id}",
    response_model=schemas.Bill,
    summary="Get bill information",
    description="Retrieve a bill's information by its ID.",
    responses={
        200: {"description": "Bill information successfully retrieved"},
        401: {"description": "Not authorized"},
        404: {"description": "Bill not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Bill:
    try:
        return crud.bill.read(db=db, obj_id=bill_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Bill not found for ID: {bill_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/bills/{bill_id}",
    summary="Delete a bill",
    description="Delete a bill from the system.",
    responses={
        200: {"description": "Bill successfully deleted"},
        403: {"description": "Forbidden"},
        404: {"description": "Bill not found"},
        500: {"description": "Internal server error"},
    },
)
async def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
):
    try:
        return crud.bill.delete(db=db, obj_id=bill_id)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Bill not found for ID: {bill_id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/bills/{bill_id}/text",
    response_model=dict,
    summary="Get bill text",
    description="Retrieve the text of a bill by its ID.",
    responses={
        200: {"description": "Bill text successfully retrieved"},
        401: {"description": "Not authorized"},
    },
)
async def get_bill_text(
    bill_id: str, _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> dict:
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}

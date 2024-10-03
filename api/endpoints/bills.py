from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from common.database.referendum import crud, schemas, models

from ..database import get_db
from ..security import get_current_user_or_verify_system_token

router = APIRouter()


@router.put(
    "/bills",
    response_model=schemas.Bill,
    summary="Add a new bill",
    description="Add a new bill to the system.",
    responses={
        200: {"description": "Bill successfully created"},
        400: {"description": "Bill already exists"},
    },
)
async def add_bill(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Bill:
    if not auth_info["is_system"]:
        raise HTTPException(
            status_code=403, detail="Only system token can create bills."
        )
    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        raise HTTPException(status_code=400, detail="Bill already exists.")
    return crud.create_bill(db=db, bill=bill)


@router.post(
    "/bills",
    response_model=schemas.Bill,
    summary="Update bill information",
    description="Update an existing bill's information.",
    responses={
        200: {"description": "Bill information successfully updated"},
        404: {"description": "Bill not found"},
    },
)
async def update_bill(
    bill: schemas.Bill,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Bill:
    if not auth_info["is_system"]:
        raise HTTPException(
            status_code=403, detail="Only system token can update bills."
        )
    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        db_bill.title = bill.title
        return crud.update_bill(db=db, db_bill=db_bill)
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill.id}.")


@router.get(
    "/bills/{bill_id}",
    response_model=schemas.Bill,
    summary="Get bill information",
    description="Retrieve a bill's information by its ID.",
    responses={
        200: {"description": "Bill information successfully retrieved"},
        404: {"description": "Bill not found"},
    },
)
async def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.Bill:
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill:
        return db_bill
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}.")


@router.delete(
    "/bills/{bill_id}",
    summary="Delete a bill",
    description="Delete a bill from the system.",
    responses={
        200: {"description": "Bill successfully deleted"},
        404: {"description": "Bill not found"},
    },
)
async def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    if not auth_info["is_system"]:
        raise HTTPException(
            status_code=403, detail="Only system token can update bills."
        )
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill is None:
        raise HTTPException(
            status_code=404, detail=f"Bill not found for ID: {bill_id}."
        )
    return crud.delete_bill(db, bill_id=bill_id)


@router.get(
    "/bills/{bill_id}/text",
    response_model=dict,
    summary="Get bill text",
    description="Retrieve the text of a bill by its ID.",
    responses={200: {"description": "Bill text successfully retrieved"}},
)
async def get_bill_text(
    bill_id: str, _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> dict:
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}

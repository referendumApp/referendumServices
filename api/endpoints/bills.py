from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

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


@router.post(
    "/",
    response_model=schemas.Bill,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bill",
    responses={
        201: {"model": schemas.Bill, "description": "Bill successfully created"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        409: {"model": ErrorResponse, "description": "Bill already exists"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_bill(
    bill: schemas.BillCreate,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Bill:
    try:
        return crud.bill.create(db=db, obj_in=bill)
    except ObjectAlreadyExistsException:
        raise HTTPException(
            status_code=409,
            detail=f"Bill already exists for legiscan_id: {bill.legiscan_id}",
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/{bill_id}",
    response_model=schemas.Bill,
    summary="Get bill information",
    responses={
        200: {"model": schemas.Bill, "description": "Bill retrieved"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def read_bill(
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


@router.put(
    "/",
    response_model=schemas.Bill,
    summary="Update bill information",
    responses={
        200: {
            "model": schemas.Bill,
            "description": "Bill information successfully updated",
        },
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_bill(
    bill: schemas.Bill,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.Bill:
    try:
        db_bill = crud.bill.read(db=db, obj_id=bill.id)
        return crud.bill.update(db=db, db_obj=db_bill, obj_in=bill)
    except ObjectNotFoundException:
        raise HTTPException(
            status_code=404, detail=f"Bill not found for ID: {bill.id}."
        )
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bill",
    responses={
        204: {"description": "Bill successfully deleted"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
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
    "/{bill_id}/text",
    response_model=Dict[str, str],
    summary="Get bill text",
    responses={
        200: {
            "model": Dict[str, str],
            "description": "Bill text successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_text(
    bill_id: str, _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> dict:
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from common.database.referendum import crud, schemas

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_version,
    create_schema=schemas.BillVersion.Base,
    update_schema=schemas.BillVersion.Record,
    response_schema=schemas.BillVersion.Full,
    resource_name="bill_version",
)


@router.get(
    "/{bill_version_id}/text",
    response_model=Dict[str, str],
    summary="Get bill text",
    responses={
        200: {
            "model": Dict[str, str | int],
            "description": "Bill text successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_text(
    bill_version_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> dict:
    bill_version = crud.bill_version.read(db=db, obj_id=bill_version_id)
    hash = bill_version.hash

    # TODO - extract full text from hash

    return {"text": hash}

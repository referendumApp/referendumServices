from fastapi import APIRouter, Depends
from typing import Dict, Any

from common.database.referendum import crud, schemas

from ..schemas import ErrorResponse
from ..security import get_current_user_or_verify_system_token
from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill,
    create_schema=schemas.BillCreate,
    update_schema=schemas.BillRecord,
    response_schema=schemas.Bill,
    resource="bill",
)


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

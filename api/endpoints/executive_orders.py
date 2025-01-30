import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from common.database.referendum import crud, models, schemas, utils
from common.database.referendum.crud import DatabaseException, ObjectNotFoundException

from ..database import get_db
from ..schemas import (
    ExecutiveOrderPaginationRequestBody,
    DenormalizedExecutiveOrder,
    ErrorResponse,
    PaginatedResponse,
)
from ..security import (
    get_current_user_or_verify_system_token,
    verify_system_token,
)
from .endpoint_generator import EndpointGenerator


logger = logging.getLogger(__name__)

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.executive_order,
    create_schema=schemas.ExecutiveOrder.Base,
    update_schema=schemas.ExecutiveOrder.Record,
    response_schema=schemas.ExecutiveOrder.Full,
    resource_name="executive_order",
)


@router.post(
    "/details",
    response_model=PaginatedResponse[DenormalizedExecutiveOrder],
    summary="Get all executive order details",
    responses={
        200: {
            "model": PaginatedResponse[DenormalizedExecutiveOrder],
            "description": "Executive order details successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_executive_order_details(
    request_body: ExecutiveOrderPaginationRequestBody,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    try:
        column_filter = None
        if filter_options := request_body.filter_options:
            column_filter = utils.create_column_filter(
                model=models.ExecutiveOrder,
                filter_options=filter_options.model_dump(),
            )

        order_by = (
            [getattr(models.ExecutiveOrder, request_body.order_by)] if request_body.order_by else []
        )
        search_filter = None
        if request_body.search_query:
            search_filter = utils.create_search_filter(
                search_query=request_body.search_query,
                search_config=utils.SearchConfig.ENGLISH,
                fields=[models.ExecutiveOrder.title],
            )
            order_by.append(models.ExecutiveOrder.id)

        executive_orders = crud.executive_order.read_all_denormalized(
            db=db,
            skip=request_body.skip,
            limit=request_body.limit + 1,
            column_filter=column_filter,
            search_filter=search_filter,
            order_by=order_by,
        )

        if len(executive_orders) > request_body.limit:
            has_more = True
            executive_orders.pop()
        else:
            has_more = False

        result = []
        for eo in executive_orders:
            eo_dict = {
                "executive_order_id": eo.id,
                "title": eo.title,
                "hash": eo.hash,
                "url": eo.url,
                "date": eo.date,
                "president_id": eo.president.id,
                "president_name": eo.president.name,
            }
            result.append(eo_dict)
        return {"has_more": has_more, "items": result}
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter option: {e}",
        )
    except DatabaseException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}",
        )


@router.get(
    "/{executive_order_id}/details",
    response_model=DenormalizedExecutiveOrder,
    summary="Get executive order detail",
    responses={
        200: {
            "model": DenormalizedExecutiveOrder,
            "description": "Executive order details successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_executive_order_detail(
    executive_order_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
):
    try:
        executive_orders = crud.executive_order.read_denormalized(
            db=db, executive_order_id=executive_order_id
        )
        result = []
        for eo in executive_orders:
            eo_dict = {
                "executive_order_id": eo.id,
                "identifier": eo.identifier,
                "title": eo.title,
                "description": eo.description,
                "status_id": eo.status.id,
                "status": eo.status.name,
                "status_date": eo.status_date,
                "president_id": eo.president.id,
                "president_name": eo.president.name,
                "current_version_id": eo.current_version_id,
            }
            result.append(eo_dict)
        return result
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

from fastapi import APIRouter
import logging

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_action,
    create_schema=schemas.BillActionCreate,
    update_schema=schemas.BillAction,
    response_schema=schemas.BillAction,
    resource_name="bill_action",
)

import logging

from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill_action,
    create_schema=schemas.BillAction.Base,
    update_schema=schemas.BillAction.Record,
    response_schema=schemas.BillAction.Full,
    resource_name="bill_action",
)

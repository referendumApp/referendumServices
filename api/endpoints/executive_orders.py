from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.executive_order,
    create_schema=schemas.ExecutiveOrder.Base,
    update_schema=schemas.ExecutiveOrder.Record,
    response_schema=schemas.ExecutiveOrder.Full,
    resource_name="executive_order",
)

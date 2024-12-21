from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.status,
    create_schema=schemas.Status.Base,
    update_schema=schemas.Status.Record,
    response_schema=schemas.Status.Full,
    resource_name="status",
)

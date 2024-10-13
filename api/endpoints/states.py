from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.state,
    create_schema=schemas.State.Base,
    update_schema=schemas.State.Record,
    response_schema=schemas.State.Full,
    resource_name="state",
)

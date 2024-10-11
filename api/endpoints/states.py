from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.state,
    create_schema=schemas.StateCreate,
    update_schema=schemas.State,
    response_schema=schemas.State,
    resource_name="state",
)

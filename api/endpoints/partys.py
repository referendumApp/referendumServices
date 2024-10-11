from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.party,
    create_schema=schemas.PartyCreate,
    update_schema=schemas.Party,
    response_schema=schemas.Party,
    resource_name="party",
)

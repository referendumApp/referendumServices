from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislator,
    create_schema=schemas.LegislatorCreate,
    update_schema=schemas.Legislator,
    response_schema=schemas.Legislator,
    resource="legislator",
)

from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislator,
    create_schema=schemas.Legislator.Base,
    update_schema=schemas.Legislator.Record,
    response_schema=schemas.Legislator.Full,
    resource_name="legislator",
)

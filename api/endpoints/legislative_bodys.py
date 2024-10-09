from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislative_body,
    create_schema=schemas.LegislativeBodyCreate,
    update_schema=schemas.LegislativeBody,
    response_schema=schemas.LegislativeBody,
    resource_identifier="legislative_body",
)

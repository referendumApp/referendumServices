from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislative_body,
    create_schema=schemas.LegislativeBody.Base,
    update_schema=schemas.LegislativeBody.Record,
    response_schema=schemas.LegislativeBody.Full,
    resource_name="legislative_body",
)

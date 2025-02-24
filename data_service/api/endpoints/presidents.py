from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.president,
    create_schema=schemas.President.Base,
    update_schema=schemas.President.Record,
    response_schema=schemas.President.Full,
    resource_name="president",
)

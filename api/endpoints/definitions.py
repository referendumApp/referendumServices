from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.definition,
    create_schema=schemas.Definition.Base,
    update_schema=schemas.Definition.Record,
    response_schema=schemas.Definition.Full,
    resource_name="definition",
)

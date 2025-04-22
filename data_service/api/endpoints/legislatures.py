from fastapi import APIRouter

from common.database.referendum import crud, schemas
from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislature,
    create_schema=schemas.Legislature.Base,
    update_schema=schemas.Legislature.Record,
    response_schema=schemas.Legislature.Full,
    resource_name="legislature",
)

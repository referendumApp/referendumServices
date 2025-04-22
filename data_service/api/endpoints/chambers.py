from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.chamber,
    create_schema=schemas.Chamber.Base,
    update_schema=schemas.Chamber.Record,
    response_schema=schemas.Chamber.Full,
    resource_name="chamber",
)

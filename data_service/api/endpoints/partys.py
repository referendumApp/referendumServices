from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.party,
    create_schema=schemas.Party.Base,
    update_schema=schemas.Party.Record,
    response_schema=schemas.Party.Full,
    resource_name="party",
)

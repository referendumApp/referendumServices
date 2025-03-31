from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.session,
    create_schema=schemas.Session.Base,
    update_schema=schemas.Session.Record,
    response_schema=schemas.Session.Full,
    resource_name="session",
)

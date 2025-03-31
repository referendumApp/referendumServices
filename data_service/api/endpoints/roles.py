from fastapi import APIRouter

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.role,
    create_schema=schemas.Role.Base,
    update_schema=schemas.Role.Record,
    response_schema=schemas.Role.Full,
    resource_name="role",
)

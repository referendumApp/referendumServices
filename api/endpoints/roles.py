from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.role,
    create_schema=schemas.RoleCreate,
    update_schema=schemas.Role,
    response_schema=schemas.Role,
    resource_name="role",
)

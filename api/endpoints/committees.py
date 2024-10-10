from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.committee,
    create_schema=schemas.CommitteeCreate,
    update_schema=schemas.Committee,
    response_schema=schemas.Committee,
    resource_name="committee",
)

from fastapi import APIRouter

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.vote,
    create_schema=schemas.VoteCreate,
    update_schema=schemas.VoteCreate,
    response_schema=schemas.Vote,
    resource_identifier="vote",
)

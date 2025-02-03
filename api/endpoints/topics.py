from fastapi import APIRouter

from common.database.referendum import crud, schemas
from ._core import EndpointGenerator


router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.topic,
    create_schema=schemas.Topic.Base,
    update_schema=schemas.Topic.Record,
    response_schema=schemas.Topic.Full,
    resource_name="topic",
)

from fastapi import APIRouter

from common.database.referendum import crud, schemas
from .endpoint_generator import EndpointGenerator

router = APIRouter()

EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.topic,
    create_schema=schemas.TopicCreate,
    update_schema=schemas.Topic,
    response_schema=schemas.Topic,
    resource_name="topic",
)

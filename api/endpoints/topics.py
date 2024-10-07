from fastapi import APIRouter

from common.database.referendum import crud, schemas
from .base_router import BaseRouter


router = APIRouter()


BaseRouter.add_crud_routes(
    router=router,
    crud_model=crud.topic,
    create_schema=schemas.TopicCreate,
    update_schema=schemas.Topic,
    response_schema=schemas.Topic,
    resource="topic",
)

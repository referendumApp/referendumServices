from fastapi import APIRouter
import logging

from common.database.referendum import crud, schemas
from .endpoint_generator import EndpointGenerator


logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.comment,
    create_schema=schemas.CommentCreate,
    update_schema=schemas.Comment,
    response_schema=schemas.Comment,
    resource_name="comment",
)

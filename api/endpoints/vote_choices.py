from fastapi import APIRouter
import logging

from common.database.referendum import crud, schemas

from ._core import EndpointGenerator


logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.vote_choice,
    create_schema=schemas.VoteChoice.Base,
    update_schema=schemas.VoteChoice.Record,
    response_schema=schemas.VoteChoice.Full,
    resource_name="vote_choice",
)

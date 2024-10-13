from fastapi import APIRouter
import logging

from common.database.referendum import crud, schemas

from .endpoint_generator import EndpointGenerator


logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.legislator_vote,
    create_schema=schemas.LegislatorVote.Base,
    update_schema=schemas.LegislatorVote.Record,
    response_schema=schemas.LegislatorVote.Full,
    resource_name="legislator_vote",
)

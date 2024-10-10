from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from common.database.referendum import crud, schemas
from common.database.referendum.crud import ObjectNotFoundException, DatabaseException

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user_or_verify_system_token, verify_system_token
from .endpoint_generator import EndpointGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill,
    create_schema=schemas.BillCreate,
    update_schema=schemas.BillRecord,
    response_schema=schemas.Bill,
    resource_name="bill",
)


@router.get(
    "/{bill_id}/text",
    response_model=Dict[str, str],
    summary="Get bill text",
    responses={
        200: {
            "model": Dict[str, str],
            "description": "Bill text successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_bill_text(
    bill_id: str, _: Dict[str, Any] = Depends(get_current_user_or_verify_system_token)
) -> dict:
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    logger.info(f"Fetched bill text for bill {bill_id}")
    return {"bill_id": bill_id, "text": lorem_ipsum}


@router.post(
    "/{bill_id}/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add topic to a bill",
    responses={
        204: {"description": "Topic successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def add_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to add topic {topic_id} to bill {bill_id}")
    try:
        crud.bill.add_topic(db=db, bill_id=bill_id, topic_id=topic_id)
        logger.info(f"Topic {topic_id} successfully added to bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error adding topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error adding topic: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while adding topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{bill_id}/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove topic from a bill",
    responses={
        204: {"description": "Topic successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def remove_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to remove topic {topic_id} from bill {bill_id}")
    try:
        crud.bill.remove_topic(db=db, bill_id=bill_id, topic_id=topic_id)
        logger.info(f"Topic {topic_id} successfully removed from bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error removing topic: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error unfollowing: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while removing topic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post(
    "/{bill_id}/sponsors/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add sponsor to a bill",
    responses={
        204: {"description": "Sponsor successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def add_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(
        f"Attempting to add sponsor legislator {legislator_id} to bill {bill_id}"
    )
    try:
        crud.bill.add_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
        logger.info(f"Sponsor {legislator_id} successfully added to bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error adding sponsor: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error adding sponsor: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while adding sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete(
    "/{bill_id}/sponsors/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove sponsor from a bill",
    responses={
        204: {"description": "Sponsor successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
def remove_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(
        f"Attempting to remove sponsor legislator {legislator_id} from bill {bill_id}"
    )
    try:
        crud.bill.remove_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
        logger.info(f"Sponsor {legislator_id} successfully removed from bill {bill_id}")
        return
    except ObjectNotFoundException as e:
        logger.warning(f"Error removing sponsor: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Error removing sponsor: {str(e)}")
    except DatabaseException as e:
        logger.error(f"Database error while removing sponsor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

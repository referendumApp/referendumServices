from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import DatabaseException

from ..database import get_db
from ..schemas import ErrorResponse
from ..security import get_current_user, get_current_user_or_verify_system_token

router = APIRouter()


# Cast Vote
@router.put(
    "/",
    response_model=schemas.UserVote,
    summary="Cast vote",
    responses={
        200: {
            "model": schemas.UserVote,
            "description": "Vote updated successfully",
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def cast_vote(
    vote: schemas.UserVoteCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.UserVote:
    try:
        user_vote = schemas.UserVote(**vote.model_dump(), user_id=user.id)
        return crud.user_vote.create_or_update_vote(db=db, user_vote_object=user_vote)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get(
    "/",
    response_model=List[schemas.UserVote],
    summary="Get votes for user or bill",
    responses={
        200:
            {
                "model": List[schemas.UserVote],
                "description": "List of votes retrieved successfully",
            },
        400: {
            "model": ErrorResponse,
            "description": "Bad request"
        },
        401: {
            "model": ErrorResponse,
            "description": "Unauthorized"
        },
        404: {
            "model": ErrorResponse,
            "description": "Not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        },
    },
)
async def get_votes(
    user_id: int = None,
    bill_id: int = None,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> List[models.UserVote]:
    if user_id is None and bill_id is None:
        raise HTTPException(
            status_code=400, detail="Either user_id or bill_id must be provided"
        )

    try:
        if user_id:
            if not auth_info.get("is_system"):
                if user_id != auth_info["user"].id:
                    raise HTTPException(
                        status_code=403,
                        detail=
                        f"User {auth_info['user'].id} not allowed to fetch all votes for user {user_id}",
                    )
            votes = crud.user_vote.get_votes_for_user(db=db, user_id=user_id)
        else:
            votes = crud.user_vote.get_votes_for_bill(db=db, bill_id=bill_id)

        return votes
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from common.database.referendum import crud, schemas, models
from common.database.referendum.crud import (
    ObjectNotFoundException,
)

from ..database import get_db
from ..schemas.users import (
    UserCreateInput,
    UserUpdateInput,
    PasswordResetInput,
    UserPasswordResetInput,
)
from ..schemas.interactions import (
    ErrorResponse,
    Announcement,
    BillEvent,
    Comment,
    FeedItem,
    FeedItemType,
)
from ..security import (
    get_current_user,
    get_current_user_or_verify_system_token,
    get_user_create_with_hashed_password,
    get_password_hash,
    verify_system_token,
    verify_password,
)
from ._core import handle_crud_exceptions, handle_general_exceptions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new user",
    responses={
        201: {"model": schemas.User, "description": "User successfully created"},
        400: {"model": ErrorResponse, "description": "Bad request"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can create users",
        },
        409: {"model": ErrorResponse, "description": "Email already registered"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def create_user(
    user: UserCreateInput,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> models.User:
    user_create = get_user_create_with_hashed_password(user)
    created_user = crud.user.create(db=db, obj_in=user_create)
    logger.info(f"Successfully created user with ID: {created_user.id}")
    return created_user


@router.get(
    "/admin/{user_id}",
    response_model=schemas.User,
    summary="Get user information with system token",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def admin_read_user(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(verify_system_token),
) -> models.User:
    user = crud.user.read(db=db, obj_id=user_id)
    logger.info(f"Successfully retrieved information for user ID: {user_id}")
    return user


@router.get(
    "/",
    response_model=schemas.User,
    summary="Get user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def read_user(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.User:
    user = crud.user.read(db=db, obj_id=user.id)
    logger.info(f"Successfully retrieved information for user ID: {user.id}")
    return user


@router.put(
    "/",
    response_model=schemas.User,
    summary="Update user information",
    responses={
        200: {
            "model": schemas.User,
            "description": "User information successfully updated",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this user's information",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def update_user(
    user: UserUpdateInput,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> models.User:
    logger.info(f"Attempting to update user information for email: {user.email}")
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.email != user.email:
            logger.warning(
                f"Unauthorized attempt to update user info: User {current_user.email} tried to update User {user.email}"
            )
            raise HTTPException(
                status_code=403, detail="You can only update your own user information."
            )
    db_user = crud.user.get_user_by_email(db, email=user.email)

    user_create = get_user_create_with_hashed_password(user)
    updated_user = crud.user.update(db=db, db_obj=db_user, obj_in=user_create)
    logger.info(f"Successfully updated information for user ID: {updated_user.id}")
    return updated_user


@router.patch(
    "/password_reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user password",
    responses={
        204: {"description": "User password successfully updated"},
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this user's password",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def update_user_password(
    password_reset: UserPasswordResetInput,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    logger.info(f"Attempting to update user password for email: {user.email}")
    if not verify_password(password_reset.current_password, user.hashed_password):
        logger.warning(
            f"Unsuccessful attempt to update user password: User {user.email} entered an incorrect password"
        )
        raise HTTPException(status_code=403, detail="The current password does not match")

    hashed_password = get_password_hash(password_reset.new_password)
    crud.user.update_user_password(db=db, user_id=user.id, hashed_password=hashed_password)
    logger.info(f"Successfully updated password for user ID: {user.id}")


@router.patch(
    "/admin/{user_id}/password_reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update a user's password",
    responses={
        204: {"description": "User's password successfully updated"},
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to update this user's password",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def admin_update_user_password(
    user_id: int,
    password_reset: PasswordResetInput,
    db: Session = Depends(get_db),
    _: Dict[str, any] = Depends(verify_system_token),
) -> None:
    hashed_password = get_password_hash(password_reset.new_password)
    crud.user.update_user_password(db=db, user_id=user_id, hashed_password=hashed_password)
    logger.info(f"Successfully updated password for user ID: {user_id}")


@router.delete(
    "/admin/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        204: {"description": "User successfully deleted"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can delete users",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> None:
    # TODO - make this a cascading delete of all their related records
    crud.user.delete(db=db, obj_id=user_id)
    logger.info(f"Successfully deleted user with ID: {user_id}")


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
    responses={
        204: {"description": "User successfully deleted"},
        403: {
            "model": ErrorResponse,
            "description": "Only system token can delete users",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def delete_user(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    crud.user.update_soft_delete(db=db, user_id=user.id, deleted=True)
    logger.info(f"Successfully deleted user with ID: {user.id}")


@router.get(
    "/topics",
    response_model=List[schemas.Topic.Record],
    summary="Get user's followed topics",
    responses={
        200: {
            "model": List[schemas.Topic.Record],
            "description": "User's topics successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's topics",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def get_user_topics(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Topic]:
    topics = crud.user.get_user_topics(db=db, user_id=user.id)
    logger.info(f"Successfully retrieved {len(topics)} topics for user ID: {user.id}")
    return topics


@router.get(
    "/bills",
    response_model=List[schemas.Bill.Record],
    summary="Get user's followed bills",
    responses={
        200: {
            "model": List[schemas.Bill.Record],
            "description": "User's bills successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's bills",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def get_user_bills(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Bill]:
    bills = crud.user.get_user_bills(db=db, user_id=user.id)
    logger.info(f"Successfully retrieved {len(bills)} bills for user ID: {user.id}")
    return bills


@router.get(
    "/legislators",
    response_model=List[schemas.Legislator.Record],
    summary="Get user's followed legislators",
    responses={
        200: {
            "model": List[schemas.Legislator.Record],
            "description": "User's legislators successfully retrieved",
        },
        403: {
            "model": ErrorResponse,
            "description": "Unauthorized to retrieve this user's legislators",
        },
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("user")
async def get_user_legislators(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> List[models.Legislator]:
    legislators = crud.user.get_user_legislators(db=db, user_id=user.id)
    logger.info(f"Successfully retrieved {len(legislators)} legislators for user ID: {user.id}")
    return legislators


@router.put(
    "/votes",
    response_model=schemas.UserVote,
    summary="Cast vote",
    responses={
        200: {
            "model": schemas.UserVote,
            "description": "Vote updated successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def cast_vote(
    vote: schemas.UserVoteCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> models.UserVote:
    user_vote = schemas.UserVote(**vote.model_dump(), user_id=user.id)
    return crud.user_vote.cast_vote(db=db, vote=user_vote)


@router.get(
    "/admin/{user_id}/votes",
    response_model=List[schemas.UserVote],
    summary="Get votes for user",
    responses={
        200: {
            "model": List[schemas.UserVote],
            "description": "List of votes retrieved successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def admin_get_user_votes(
    user_id: int,
    bill_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(verify_system_token),
) -> List[models.UserVote]:
    return crud.user_vote.get_votes_for_user(db=db, user_id=user_id, bill_id=bill_id)


@router.get(
    "/votes",
    response_model=List[schemas.UserVote],
    summary="Get votes for user",
    responses={
        200: {
            "model": List[schemas.UserVote],
            "description": "List of votes retrieved successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def get_user_votes(
    bill_id: Optional[int] = Query(None, alias="billId"),
    db: Session = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[models.UserVote]:
    return crud.user_vote.get_votes_for_user(db=db, user_id=user.id, bill_id=bill_id)


@router.delete(
    "/votes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uncast vote",
    responses={
        204: {"description": "Vote deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def uncast_vote(
    bill_id: int = Query(alias="billId"),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return crud.user_vote.uncast_vote(db=db, bill_id=bill_id, user_id=user.id)


@router.post(
    "/bills/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a bill",
    responses={
        204: {"description": "Bill successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def follow_bill(
    bill_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.follow_bill(db=db, user_id=user.id, bill_id=bill_id)
        logger.info(f"User {user.id} successfully followed bill {bill_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or bill not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.delete(
    "/bills/{bill_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a bill",
    responses={
        204: {"description": "Bill successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def unfollow_bill(
    bill_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.unfollow_bill(db=db, user_id=user.id, bill_id=bill_id)
        logger.info(f"User {user.id} successfully unfollowed bill {bill_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or bill not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.post(
    "/legislators/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a legislator",
    responses={
        204: {"description": "Legislator successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def follow_legislator(
    legislator_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.follow_legislator(db=db, user_id=user.id, legislator_id=legislator_id)
        logger.info(f"User {user.id} successfully followed legislator {legislator_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or legislator not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.delete(
    "/legislators/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a legislator",
    responses={
        204: {"description": "Legislator successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def unfollow_legislator(
    legislator_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.unfollow_legislator(db=db, user_id=user.id, legislator_id=legislator_id)
        logger.info(f"User {user.id} successfully unfollowed legislator {legislator_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or legislator not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.post(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a topic",
    responses={
        204: {"description": "Topic successfully followed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def follow_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.follow_topic(db=db, user_id=user.id, topic_id=topic_id)
        logger.info(f"User {user.id} successfully followed topic {topic_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or topic not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a topic",
    responses={
        204: {"description": "Topic successfully unfollowed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "User or topic not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def unfollow_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
) -> None:
    try:
        crud.user.unfollow_topic(db=db, user_id=user.id, topic_id=topic_id)
        logger.info(f"User {user.id} successfully unfollowed topic {topic_id}")
    except ObjectNotFoundException as e:
        exception_message = f"User or topic not found"
        logger.error(f"{exception_message}. Exception: {str(e)}", exc_info=True)
        raise HTTPException(status_code=404, detail=exception_message)


@router.get(
    "/feed",
    response_model=List[FeedItem],
    summary="Gets feed items for user",
    responses={
        200: {
            "model": List[FeedItem],
            "description": "User feed retrieved successfully",
        },
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def get_user_feed(
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(get_current_user),
) -> List[FeedItem]:
    feed_items = [
        FeedItem(
            type=FeedItemType.Announcement,
            content=Announcement(
                header="Welcome to Referendum and thank you for participating in our beta!",
                text="""Events that may interest you will appear here in your Feed: for now that is all comments on bills, but eventually all votes, events, and other newsworthy notifications will appear here.

The Catalog tab includes all bills and legislators from 2024-2025.
You can follow those that interest you and deep dive into the text itself, votes, sponsors, and history from the here, and we will continue to add legislation throughout the beta.

If you have any questions, concerns, or run into any issues, please let us know at one of the following:
- In App: Go to Settings -> Feedback
- Discord: https://discord.gg/yWvPYKzWZf
- Email: feedback@referendumapp.com

We're glad to have you join the conversation!
""",
            ),
        ),
        # TODO - derive this from feed items managed outside of code
        FeedItem(
            type=FeedItemType.BillEvent,
            content=BillEvent(
                bill_id=1860121,
                bill_identifier="HB7521",
                text="Spotlight: Banning TikTok",
            ),
        ),
    ]
    # TODO - restrict this to relevant comments
    all_comments = crud.comment.read_all(db=db, order_by=["created_at"])
    feed_items.extend(
        [
            FeedItem(
                type=FeedItemType.Comment,
                content=Comment(
                    id=comment.id,
                    parent_id=comment.parent_id,
                    bill_id=comment.bill_id,
                    bill_identifier=comment.bill.identifier,
                    user_id=comment.user_id,
                    comment=comment.comment,
                    user_name=comment.user.name,
                    created_at=comment.created_at,
                ),
            )
            for comment in reversed(all_comments)
        ]
    )

    return feed_items

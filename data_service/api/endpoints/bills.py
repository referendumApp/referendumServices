import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload, load_only

from common.database.referendum import crud, models, schemas, utils

from ..database import get_db
from ..schemas.interactions import (
    BillFilterOptions,
    BillPaginationRequestBody,
    ErrorResponse,
    PaginatedResponse,
    Comment,
)
from ..schemas.resources import (
    BillVotingHistory,
    DenormalizedBill,
    LegislatorVote,
    LegislatorVoteDetail,
    VoteCountByChoice,
    VoteCountByParty,
    VoteSummary,
)
from ..schemas.users import UserBillVotes
from ..security import (
    get_current_user_or_verify_system_token,
    validate_user_or_verify_system_token,
    verify_system_token,
)
from ._core import EndpointGenerator, handle_crud_exceptions, handle_general_exceptions

logger = logging.getLogger(__name__)

router = APIRouter()


EndpointGenerator.add_crud_routes(
    router=router,
    crud_model=crud.bill,
    create_schema=schemas.Bill.Base,
    update_schema=schemas.Bill.Record,
    response_schema=schemas.Bill.Full,
    resource_name="bill",
)


@router.post(
    "/details",
    response_model=PaginatedResponse[DenormalizedBill],
    summary="Get all bill details",
    responses={
        200: {
            "model": PaginatedResponse[DenormalizedBill],
            "description": "Bill details successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def get_all_bill_details(
    request_body: BillPaginationRequestBody,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(validate_user_or_verify_system_token),
):
    try:
        if request_body.federal_only:
            # federal bills have legislature_id == 52
            if request_body.filter_options:
                filter_options_dict = request_body.filter_options.model_dump(exclude_none=True)
                filter_options_dict["legislature_id"] = [52]
                request_body.filter_options = BillFilterOptions(**filter_options_dict)
            else:
                request_body.filter_options = BillFilterOptions(legislature_id=[52])

        clauses = []
        if request_body.filter_options:
            # We need this until we flatten out 'role_id' in the bills table
            filter_options = request_body.filter_options.model_dump(exclude_none=True)
            role_id = filter_options.pop("role_id", None)

            if role_id is not None:
                role_filter = models.Bill.legislative_body.has(
                    models.LegislativeBody.role_id.in_(role_id)
                )
                clauses.append(role_filter)

            if filter_options:
                non_role_filter = utils.create_column_filter(
                    model=models.Bill,
                    filter_options=filter_options,
                )
                clauses.append(non_role_filter)

        column_filter = and_(*clauses) if clauses else None

        order_by = []
        if request_body.order_by:
            sort_option = request_body.order_by.model_dump()
            order_by = utils.create_sort_column_list(model=models.Bill, sort_option=sort_option)

        order_by.append(models.Bill.id)

        search_filter = None
        if request_body.search_query:
            id_filter = utils.create_search_filter(
                search_query=request_body.search_query,
                search_config=utils.SearchConfig.SIMPLE,
                fields=[models.Bill.identifier],
                prefix=True,
            )
            title_filter = utils.create_search_filter(
                search_query=request_body.search_query,
                search_config=utils.SearchConfig.ENGLISH,
                fields=[models.Bill.title],
            )
            search_filter = or_(id_filter, title_filter)

        bills = crud.bill.read_all_denormalized(
            db=db,
            skip=request_body.skip,
            limit=request_body.limit + 1,
            column_filter=column_filter,
            search_filter=search_filter,
            order_by=order_by,
        )
        if len(bills) > request_body.limit:
            has_more = True
            bills.pop()
        else:
            has_more = False

        result = []
        for bill in bills:
            sponsors = [
                {
                    "bill_id": sponsor.bill_id,
                    "legislator_id": sponsor.legislator_id,
                    "legislator_name": sponsor.legislator.name,
                    "rank": sponsor.rank,
                    "type": sponsor.type,
                }
                for sponsor in bill.sponsors
            ]
            bill_dict = {
                "bill_id": bill.id,
                "legiscan_id": bill.legiscan_id,
                "identifier": bill.identifier,
                "title": bill.title,
                "description": bill.description,
                "status_id": bill.status.id,
                "status": bill.status.name,
                "status_date": bill.status_date,
                "session_id": bill.session.id,
                "session_name": bill.session.name,
                "state_id": bill.legislature.id,
                "state_name": bill.legislature.name,
                "current_version_id": bill.current_version_id,
                "legislative_body_id": bill.legislative_body.id,
                "role_id": bill.legislative_body.role.id,
                "legislative_body_role": bill.legislative_body.role.name,
                "sponsors": sponsors,
            }
            result.append(bill_dict)
        return {"has_more": has_more, "items": result}
    except AttributeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid filter option: {e}",
        )


@router.get(
    "/{bill_id}/details",
    response_model=DenormalizedBill,
    summary="Get bill detail",
    responses={
        200: {
            "model": DenormalizedBill,
            "description": "Bill details successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill")
async def get_bill_detail(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(validate_user_or_verify_system_token),
):
    bill = crud.bill.read_denormalized(db=db, bill_id=bill_id)
    sponsors = [
        {
            "bill_id": sponsor.bill_id,
            "legislator_id": sponsor.legislator_id,
            "legislator_name": sponsor.legislator.name,
            "rank": sponsor.rank,
            "type": sponsor.type,
        }
        for sponsor in bill.sponsors
    ]

    return {
        "bill_id": bill.id,
        "legiscan_id": bill.legiscan_id,
        "identifier": bill.identifier,
        "title": bill.title,
        "description": bill.description,
        "status_id": bill.status.id,
        "status": bill.status.name,
        "status_date": bill.status_date,
        "session_id": bill.session.id,
        "session_name": bill.session.name,
        "state_id": bill.legislature.id,
        "state_name": bill.legislature.name,
        "current_version_id": bill.current_version_id,
        "legislative_body_id": bill.legislative_body.id,
        "role_id": bill.legislative_body.role.id,
        "legislative_body_role": bill.legislative_body.role.name,
        "sponsors": sponsors,
    }


@router.get(
    "/{bill_id}/bill_versions",
    response_model=List[schemas.BillVersion.Record],
    summary="Get bill versions",
    responses={
        200: {
            "model": Dict[str, str | int],
            "description": "Bill versions successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill")
async def get_bill_versions(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(validate_user_or_verify_system_token),
) -> dict:
    bill = crud.bill.read(db=db, obj_id=bill_id)
    return bill.bill_versions


@router.get(
    "/{bill_id}/user_votes",
    response_model=UserBillVotes,
    summary="Get user vote counts for a bill",
    responses={
        200: {
            "model": UserBillVotes,
            "description": "Vote counts successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill")
async def get_bill_vote_counts(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(validate_user_or_verify_system_token),
):
    bill_votes = crud.bill.get_bill_user_votes(db, bill_id)
    return bill_votes


# TODO: Migrate to user service
@router.get(
    "/{bill_id}/comments",
    response_model=List[Comment],
    summary="Get bill comments",
    responses={
        200: {
            "model": List[Comment],
            "description": "Bill comments successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_crud_exceptions("bill")
async def get_bill_comments(
    bill_id: int,
    db: Session = Depends(get_db),
    auth_info: Dict[str, Any] = Depends(get_current_user_or_verify_system_token),
) -> List[Comment]:
    current_user_id = None
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        current_user_id = current_user.id

    bill_comments = crud.bill.get_bill_comments(db, bill_id)

    return [
        Comment(
            id=comment.id,
            parent_id=comment.parent_id,
            bill_id=comment.bill_id,
            bill_identifier=comment.bill.identifier,
            user_id=comment.user_id,
            comment=comment.comment,
            user_name=comment.user.name,
            endorsements=len(comment.likes),
            created_at=comment.created_at,
            current_user_has_endorsed=(
                any(like.id == current_user_id for like in comment.likes)
                if current_user_id
                else False
            ),
        )
        for comment in bill_comments
    ]


@router.get(
    "/{bill_id}/voting_history",
    response_model=BillVotingHistory,
    summary="Get bill voting history",
    responses={
        200: {
            "model": BillVotingHistory,
            "description": "Bill voting history successfully retrieved",
        },
        401: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def get_bill_voting_history(
    bill_id: int,
    db: Session = Depends(get_db),
    _: Dict[str, Any] = Depends(validate_user_or_verify_system_token),
) -> BillVotingHistory:
    query = (
        select(models.LegislatorVote)
        .options(
            joinedload(models.LegislatorVote.vote_choice),
            joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.party),
            joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.role),
            joinedload(models.LegislatorVote.legislator).joinedload(models.Legislator.state),
        )
        .filter(models.LegislatorVote.bill_id == bill_id)
    )

    results = db.execute(query).scalars().all()

    all_legislator_votes = {}
    vote_summaries_by_action = defaultdict(
        lambda: {
            "total_votes": 0,
            "vote_choice_counter": Counter(),
            "party_vote_counter": Counter(),
        }
    )
    for vote in results:
        all_legislator_votes.setdefault(vote.bill_action_id, []).append(
            LegislatorVote(
                legislator_id=vote.legislator.id,
                legislator_name=vote.legislator.name,
                party_name=vote.legislator.party.name,
                state_abbr=("N/A" if vote.legislator.state is None else vote.legislator.state.abbr),
                role_name=vote.legislator.role.name,
                vote_choice_id=vote.vote_choice.id,
            )
        )

        running_summary = vote_summaries_by_action[vote.bill_action_id]
        running_summary["total_votes"] += 1
        running_summary["vote_choice_counter"][vote.vote_choice_id] += 1
        running_summary["party_vote_counter"][(vote.legislator.party_id, vote.vote_choice_id)] += 1

    bill_action_query = (
        select(models.BillAction)
        .options(
            load_only(models.BillAction.id, models.BillAction.date, models.BillAction.description),
        )
        .filter(models.BillAction.id.in_(all_legislator_votes.keys()))
        .order_by(models.BillAction.id.desc(), models.BillAction.date.desc())
    )

    bill_action_results = db.execute(bill_action_query).scalars().all()

    legislator_vote_detail = []
    for bill_action in bill_action_results:
        legislator_vote_detail.append(
            LegislatorVoteDetail(
                bill_action_id=bill_action.id,
                date=bill_action.date,
                action_description=bill_action.description,
                legislator_votes=all_legislator_votes[bill_action.id],
            )
        )

    summaries = [
        VoteSummary(
            bill_action_id=action_id,
            total_votes=summary_data["total_votes"],
            vote_counts_by_choice=[
                VoteCountByChoice(vote_choice_id=choice_id, count=count)
                for choice_id, count in summary_data["vote_choice_counter"].items()
            ],
            vote_counts_by_party=[
                VoteCountByParty(vote_choice_id=vote_choice_id, party_id=party_id, count=count)
                for (party_id, vote_choice_id), count in summary_data["party_vote_counter"].items()
            ],
        )
        for action_id, summary_data in vote_summaries_by_action.items()
    ]

    return BillVotingHistory(bill_id=bill_id, votes=legislator_vote_detail, summaries=summaries)


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
@handle_general_exceptions()
async def add_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    crud.bill.add_topic(db=db, bill_id=bill_id, topic_id=topic_id)
    logger.info(f"Topic {topic_id} successfully added to bill {bill_id}")


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
@handle_general_exceptions()
async def remove_topic(
    bill_id: int,
    topic_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    crud.bill.remove_topic(db=db, bill_id=bill_id, topic_id=topic_id)
    logger.info(f"Topic {topic_id} successfully removed from bill {bill_id}")


@router.post(
    "/{bill_id}/sponsors/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add sponsor to a bill",
    responses={
        204: {"description": "Sponsor successfully added"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def add_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    crud.bill.add_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
    logger.info(f"Sponsor {legislator_id} successfully added to bill {bill_id}")


@router.delete(
    "/{bill_id}/sponsors/{legislator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove sponsor from a bill",
    responses={
        204: {"description": "Sponsor successfully removed"},
        401: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Bill or legislator not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@handle_general_exceptions()
async def remove_sponsor(
    bill_id: int,
    legislator_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_system_token),
) -> None:
    logger.info(f"Attempting to remove sponsor legislator {legislator_id} from bill {bill_id}")
    crud.bill.remove_sponsor(db=db, bill_id=bill_id, legislator_id=legislator_id)
    logger.info(f"Sponsor {legislator_id} successfully removed from bill {bill_id}")

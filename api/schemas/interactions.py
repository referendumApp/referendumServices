from enum import Enum
from datetime import datetime
from pydantic import model_serializer, field_validator
from typing import Optional, List, Generic, TypeVar, Union

from common.core.schemas import CamelCaseBaseModel


####################
# Basic API
####################


class HealthResponse(CamelCaseBaseModel):
    status: str


class ErrorResponse(CamelCaseBaseModel):
    detail: str


class FormErrorModel(CamelCaseBaseModel):
    field: str
    message: str


class FormErrorResponse(CamelCaseBaseModel):
    detail: FormErrorModel


####################
# Base Pagination
####################

T = TypeVar("T")


class BaseFilterOptions(CamelCaseBaseModel):
    party_id: Optional[List[int]] = None
    role_id: Optional[List[int]] = None
    state_id: Optional[List[int]] = None
    status_id: Optional[List[int]] = None

    @model_serializer()
    def exclude_null_fields(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class BasePaginationRequestBody(CamelCaseBaseModel):
    skip: int = 0
    limit: int = 100
    search_query: Optional[str] = None
    order_by: Optional[str] = None


class PaginatedResponse(CamelCaseBaseModel, Generic[T]):
    has_more: bool
    items: List[T]


####################
# Bill Pagination
####################


class BillFilterOptions(BaseFilterOptions):
    status_id: Optional[List[int]] = None


class BillPaginationRequestBody(BasePaginationRequestBody):
    filter_options: Optional[BillFilterOptions] = None


####################
# Executive Order Pagination
####################


class ExecutiveOrderFilterOptions(BaseFilterOptions):
    status_id: Optional[List[int]] = None


class ExecutiveOrderPaginationRequestBody(BasePaginationRequestBody):
    filter_options: Optional[BillFilterOptions] = None


####################
# Legislator Pagination
####################


class LegislatorFilterOptions(BaseFilterOptions):
    party_id: Optional[List[int]] = None
    representing_state_id: Optional[List[int]] = None


class LegislatorPaginationRequestBody(BasePaginationRequestBody):
    filter_options: Optional[LegislatorFilterOptions] = None


####################
# Chat
####################


class ChatSession(CamelCaseBaseModel):
    session_id: str


class ChatMessageRequest(ChatSession):
    message: str


class ChatMessageResponse(ChatSession):
    response: str


####################
# Feed
####################


class Comment(CamelCaseBaseModel):
    id: int
    bill_id: int
    bill_identifier: str
    user_id: int
    user_name: str
    comment: str
    endorsements: int
    parent_id: Optional[int] = None
    created_at: datetime


class Announcement(CamelCaseBaseModel):
    header: str
    text: str


class BillEvent(CamelCaseBaseModel):
    bill_id: int
    bill_identifier: str
    text: str


class FeedItemType(str, Enum):
    Comment = "comment"
    Announcement = "announcement"
    BillEvent = "bill_event"


class FeedItem(CamelCaseBaseModel):
    type: FeedItemType
    content: Union[Announcement, Comment, BillEvent]

    @field_validator("content")
    def validate_content_type(cls, v, values):
        type_to_class = {
            FeedItemType.Announcement: Announcement,
            FeedItemType.BillEvent: BillEvent,
            FeedItemType.Comment: Comment,
        }
        expected_type = type_to_class.get(values.data.get("type"))
        if expected_type and not isinstance(v, expected_type):
            raise ValueError(
                f"Content must be of type {expected_type.__name__} when type is {values.data['type']}"
            )
        return v

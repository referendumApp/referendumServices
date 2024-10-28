from datetime import date
from pydantic import BaseModel, EmailStr, Field, ConfigDict, create_model
from pydantic.alias_generators import to_camel
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional

from .models import VoteChoice, BillActionType


T = TypeVar("T")


class CamelCaseBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        protected_namespaces=(),
        arbitrary_types_allowed=True,
    )


class BaseSchema(CamelCaseBaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecordSchema(BaseSchema, Generic[T]):
    id: int


class RelationshipSchema(RecordSchema[T], Generic[T]):
    pass


class SchemaContainer(BaseModel):
    Base: Type[BaseSchema]
    Record: Type[RecordSchema]
    Full: Type[RelationshipSchema]


def create_schema_container(
    name: str,
    base_fields: Dict[str, Any],
    record_fields: Dict[str, Any] = None,
    relationship_fields: Dict[str, Any] = None,
) -> SchemaContainer:
    base_class = create_model(f"{name}Base", __base__=BaseSchema, **base_fields)

    record_class = create_model(
        f"{name}Record",
        __base__=(RecordSchema,),
        **{**base_fields, **(record_fields or {})},
    )

    relationship_class = create_model(
        name,
        __base__=(RelationshipSchema,),
        **{
            **base_fields,
            **(record_fields or {}),
            **(relationship_fields or {}),
        },
    )

    return SchemaContainer(Base=base_class, Record=record_class, Full=relationship_class)


Party = create_schema_container(
    name="Party",
    base_fields={"id": (int, ...), "name": (str, ...)},
)


Role = create_schema_container(
    name="Role",
    base_fields={"id": (int, ...), "name": (str, ...)},
)


State = create_schema_container(
    name="State",
    base_fields={"id": (int, ...), "name": (str, ...)},
)


LegislativeBody = create_schema_container(
    name="State",
    base_fields={"id": (int, ...), "role_id": (int, ...), "state_id": (int, ...)},
)


Committee = create_schema_container(
    name="Committee",
    base_fields={
        "id": (int, ...),
        "name": (str, ...),
        "legislative_body_id": (int, ...),
    },
)


Topic = create_schema_container(
    name="Topic",
    base_fields={"id": (int, ...), "name": (str, ...)},
)


Legislator = create_schema_container(
    name="Legislator",
    base_fields={
        "id": (int, ...),
        "legiscan_id": (int, ...),
        "name": (str, ...),
        "image_url": (Optional[str], None),
        "district": (str, ...),
        "party_id": (int, ...),
        "state_id": (int, ...),
        "address": (Optional[str], None),
        "facebook": (Optional[str], None),
        "instagram": (Optional[str], None),
        "phone": (Optional[str], None),
        "twitter": (Optional[str], None),
    },
    relationship_fields={"committees": (List[Committee.Record], [])},
)


BillVersion = create_schema_container(
    name="BillVersion",
    base_fields={
        "bill_id": (int, ...),
        "version": (int, ...),
    },
)


Bill = create_schema_container(
    name="Bill",
    base_fields={
        "id": (int, ...),
        "legiscan_id": (int, ...),
        "identifier": (str, ...),
        "title": (str, ...),
        "description": (str, ...),
        "session_id": (int, ...),
        "state_id": (int, ...),
        "status_id": (int, ...),
        "status_date": (date, ...),
        "briefing": (Optional[str], ...),
    },
    relationship_fields={
        "state": (Optional[State.Record], None),
        "legislative_body": (Optional[LegislativeBody.Record], None),
        "topics": (List[Topic.Record], []),
        "sponsors": (List[Legislator.Record], []),
        "versions": (List[BillVersion.Record], []),
    },
)


BillAction = create_schema_container(
    name="BillAction",
    base_fields={
        "id": (int, ...),
        "bill_id": (int, ...),
        "date": (date, ...),
        "type": (BillActionType, ...),
    },
)


LegislatorVote = create_schema_container(
    name="LegislatorVote",
    base_fields={
        "bill_id": (int, ...),
        "bill_action_id": (int, ...),
        "legislator_id": (int, ...),
        "vote_choice": (VoteChoice, ...),
    },
)


class UserBase(BaseSchema):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    hashed_password: str


class UserReference(UserBase):
    id: int


class User(UserBase):
    id: int
    followed_bills: List[Bill.Record] = []
    followed_topics: List[Topic.Record] = []
    followed_legislators: List[Legislator.Record] = []


Comment = create_schema_container(
    name="Comment",
    base_fields={
        "user_id": (int, ...),
        "bill_id": (int, ...),
        "parent_id": (Optional[int], None),
        "comment": (str, ...),
    },
    record_fields={"id": (int, ...)},
    relationship_fields={"likes": (List[UserReference], [])},
)


# UserVote
class UserVoteBase(BaseSchema):
    bill_id: int
    vote_choice: VoteChoice


class UserVoteCreate(UserVoteBase):
    pass


class UserVote(UserVoteBase):
    user_id: int

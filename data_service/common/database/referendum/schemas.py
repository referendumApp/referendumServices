from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, create_model
from typing import TypeVar, Generic, List, Type, Dict, Any, Optional

from common.core.schemas import CamelCaseBaseModel

T = TypeVar("T")


class BaseSchema(CamelCaseBaseModel):
    model_config = ConfigDict(from_attributes=True)


class RecordSchema(BaseSchema, Generic[T]):
    pass


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


# Create VoteChoice schema
VoteChoice = create_schema_container(
    name="VoteChoice",
    base_fields={"id": (int, ...), "name": (str, ...)},
)

Party = create_schema_container(
    name="Party",
    base_fields={"id": (int, ...), "name": (str, ...)},
)

Chamber = create_schema_container(
    name="Chamber",
    base_fields={"id": (int, ...), "name": (str, ...)},
)

State = create_schema_container(
    name="State",
    base_fields={"id": (int, ...), "name": (str, ...), "abbr": (str, ...)},
)

Status = create_schema_container(
    name="Status",
    base_fields={"id": (int, ...), "name": (str, ...)},
)

Legislature = create_schema_container(
    name="Legislature",
    base_fields={
        "id": (int, ...),
        "state_id": (int, ...),
    },
)

LegislativeBody = create_schema_container(
    name="State",
    base_fields={"id": (int, ...), "chamber_id": (int, ...), "legislature_id": (int, ...)},
)

Committee = create_schema_container(
    name="Committee",
    base_fields={
        "id": (int, ...),
        "name": (str, ...),
        "legislative_body_id": (int, ...),
    },
)

Session = create_schema_container(
    name="Session",
    base_fields={"id": (int, ...), "name": (str, ...), "legislature_id": (int, ...)},
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
        "legislative_body_id": (int, ...),
        "representing_state_id": (Optional[int], None),
        "address": (Optional[str], None),
        "facebook": (Optional[str], None),
        "instagram": (Optional[str], None),
        "phone": (Optional[str], None),
        "twitter": (Optional[str], None),
        "followthemoney_eid": (Optional[str], None),
    },
    relationship_fields={
        "committees": (List[Committee.Record], []),
        "legislative_body": (LegislativeBody.Record, None),
        "representing_state": (Optional[State.Record], None),
        "party": (Party.Record, None),
        "chamber": (Chamber.Record, None),
    },
)

BillVersion = create_schema_container(
    name="BillVersion",
    base_fields={
        "id": (int, ...),
        "bill_id": (int, ...),
        "url": (str, ...),
        "hash": (str, ...),
        "briefing": (Optional[str], ...),
    },
)

Sponsor = create_schema_container(
    name="Sponsor",
    base_fields={
        "bill_id": (int, ...),
        "legislator_id": (int, ...),
        "rank": (int, ...),
        "type": (str, ...),
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
        "legislative_body_id": (int, ...),
    },
    record_fields={"current_version_id": (Optional[int], None)},
    relationship_fields={
        "state": (Optional[State.Record], None),
        "status": (Optional[Status.Record], None),
        "legislative_body": (Optional[LegislativeBody.Record], None),
        "topics": (List[Topic.Record], []),
        "sponsors": (List[Sponsor.Record], []),
        "versions": (List[BillVersion.Record], []),
    },
)

BillAction = create_schema_container(
    name="BillAction",
    base_fields={
        "id": (int, ...),
        "bill_id": (int, ...),
        "legislative_body_id": (int, ...),
        "date": (date, ...),
        "description": (str, ...),
    },
)

LegislatorVote = create_schema_container(
    name="LegislatorVote",
    base_fields={
        "bill_id": (int, ...),
        "bill_action_id": (int, ...),
        "legislator_id": (int, ...),
        "vote_choice_id": (int, ...),
    },
    relationship_fields={
        "vote_choice": (VoteChoice.Record, ...),
    },
)

President = create_schema_container(
    name="President",
    base_fields={
        "id": (int, ...),
        "name": (str, ...),
        "party_id": (int, ...),
    },
)


ExecutiveOrder = create_schema_container(
    name="ExecutiveOrder",
    base_fields={
        "id": (int, ...),
        "title": (str, ...),
        "signed_date": (date, ...),
        "url": (str, ...),
        "hash": (str, ...),
        "briefing": (Optional[str], ...),
        "president_id": (int, ...),
    },
    relationship_fields={
        "president": (President.Record, ...),
    },
)


class UserBase(BaseSchema):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    hashed_password: str
    settings: Dict


class SocialUserCreate(UserBase):
    settings: Dict


class UserReference(UserBase):
    id: int


class User(UserBase):
    id: int
    settings: Dict = {}
    followed_bills: List[Bill.Record] = []
    followed_topics: List[Topic.Record] = []
    followed_legislators: List[Legislator.Record] = []


Comment = create_schema_container(
    name="Comment",
    base_fields={
        "user_id": (int, ...),
        "bill_id": (int, ...),
        "parent_id": (Optional[int], None),
        "comment": (str, Field(..., min_length=1)),
    },
    record_fields={
        "id": (int, ...),
        "created_at": (datetime, ...),
        "updated_at": (Optional[datetime], None),
    },
    relationship_fields={"likes": (List[UserReference], []), "user": (UserBase, ...)},
)


# UserVote
class UserVoteBase(BaseSchema):
    bill_id: int
    vote_choice_id: int


class UserVoteCreate(UserVoteBase):
    pass


class UserVote(UserVoteBase):
    user_id: int

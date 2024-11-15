from datetime import date
from typing import Optional, List
from pydantic import field_validator, Field

from common.database.referendum.schemas import CamelCaseBaseModel, UserBase


class ErrorResponse(CamelCaseBaseModel):
    detail: str


class HealthResponse(CamelCaseBaseModel):
    status: str


class TokenResponse(CamelCaseBaseModel):
    access_token: str
    token_type: str


class TokenData(CamelCaseBaseModel):
    email: Optional[str] = None


class UserCreateInput(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class Sponsor(CamelCaseBaseModel):
    legislator_id: int
    type: str


class DenormalizedBill(CamelCaseBaseModel):
    """Represents a denormalized view of a bill with all related information."""

    bill_id: int = Field(description="Primary identifier of the bill")
    legiscan_id: int = Field(description="External identifier from LegiScan")
    identifier: str = Field(description="Bill identifier (e.g., 'HB 123')")
    title: str = Field(description="Official title of the bill")
    description: str = Field(description="Full description of the bill")
    briefing: Optional[str] = Field(None, description="Brief summary of the bill")
    status: date = Field(description="Current status of the bill")
    status_date: date = Field(description="Date of the last status change")
    session: str = Field(description="Legislative session")
    state_id: int = Field(description="State identifier")
    state_name: str = Field(description="Name of the state")
    legislative_body_id: int = Field(description="Legislative body identifier")
    legislative_body_role: str = Field(description="Role name of the legislative body")
    sponsors: List[Sponsor] = Field(default_factory=list, description="List of all bill sponsors")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "bill_id": 1,
                "legiscan_id": 12345,
                "identifier": "HB 123",
                "title": "An Act Related to Education",
                "description": "A bill to improve educational standards",
                "briefing": "Reforms education standards",
                "status": "Passed",
                "status_date": "2024-01-15",
                "session": 2024,
                "state_id": 1,
                "state_name": "California",
                "legislative_body_id": 1,
                "legislative_body_role": "House",
                "primary_sponsor": {
                    "id": 1,
                    "name": "John Smith",
                    "party": "Democratic",
                    "district": "District 1",
                    "state_id": 1,
                },
                "all_sponsors": [
                    {"id": 1, "name": "John Smith", "party": "Democratic", "is_primary": True}
                ],
            }
        },
    }

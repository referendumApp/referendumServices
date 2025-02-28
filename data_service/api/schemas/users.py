from typing import Optional, Dict

from pydantic import field_validator, Field

from common.core.schemas import CamelCaseBaseModel
from common.database.referendum.schemas import UserBase


####################
# User Management
####################


class UserCreateInput(UserBase):
    password: str
    settings: Optional[Dict] = {}

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class UserUpdateInput(CamelCaseBaseModel):
    name: str | None = Field(default=None)
    email: str | None = Field(default=None)
    settings: Dict | None = Field(default=None)

    model_config = {"extra": "forbid"}


####################
# Authentication
####################


class RefreshToken(CamelCaseBaseModel):
    refresh_token: str


class TokenResponse(RefreshToken):
    user_id: int
    access_token: str
    token_type: str


class TokenData(CamelCaseBaseModel):
    email: Optional[str] = None


class PasswordResetInput(CamelCaseBaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class UserPasswordResetInput(PasswordResetInput):
    current_password: str


####################
# User Activity
####################


class UserBillVotes(CamelCaseBaseModel):
    yea: int
    nay: int
    yea_pct: float
    nay_pct: float
    total: int


class CommentDetail(CamelCaseBaseModel):
    id: int
    bill_id: int
    user_id: int
    user_name: str
    comment: str
    parent_id: Optional[int] = None

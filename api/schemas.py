from typing import Optional

from pydantic import BaseModel, field_validator

from common.database.referendum import schemas


class ErrorResponse(BaseModel):
    detail: str


class HealthResponse(BaseModel):
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreateInput(schemas.UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class LegislatorUpdateInput(schemas.LegislatorCreate):
    id: int

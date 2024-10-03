from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=100)
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 100:
            raise ValueError("Password must not exceed 100 characters")
        return v


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


### BILLS ###
class BillBase(BaseModel):
    legiscan_id: int
    identifier: str
    title: str
    description: str
    state: str
    body: str
    session: str
    briefing: str
    status: str
    latest_action: str
    # topics:


class BillCreate(BillBase):
    pass


class Bill(BillBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ### LEGISLATORS ###
class LegislatorBase(BaseModel):
    chamber: str
    district: str
    email: str
    facebook: str
    image_url: str
    instagram: str
    name: str
    office: str
    party: str
    phone: str
    state: str
    twitter: str


class LegislatorCreate(LegislatorBase):
    pass


class Legislator(LegislatorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, ConfigDict
from typing import List


### USERS ###
class UserBase(BaseModel):
    email: str
    name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


### BILLS ###
class BillBase(BaseModel):
    legiscanID: int
    identifier: str
    title: str
    description: str
    state: str
    body: str
    session: str
    briefing: str
    status: str
    latestAction: str


#    topics:


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
    imageUrl: str
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

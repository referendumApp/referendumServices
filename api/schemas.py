from pydantic import BaseModel
from typing import List


### USERS ###
class UserBase(BaseModel):      
    email: str
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True



### BILLS ###
class BillBase(BaseModel):
    identifier: str
    title: str
    description: str
    state: str
    body: str
    session: str
    briefing: str
    sponsorIds: int
    status: str
    latestAction: str
    yesVotes: int
    noVotes: int
    userVote: str
#    topics: 

class BillCreate(BillBase):
    pass

class Bill(BillBase):
    id: int

    class Config:
        orm_mode = True



# ### LEGISLATORS ###
class LegislatorBase(BaseModel):
    chamber = str
    district = str
    email = str
    facebook = str
#    fundingRecord = []
    imageUrl = str
    instagram = str
    name = str
    office = str
    party = str
    phone = str
    state = str
#    topIssues = []
    twitter = str

class LegislatorCreate(LegislatorBase):
    pass

class Legislator(LegislatorBase):
    id: int

    class Config:
        orm_mode = True















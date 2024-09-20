import json
import boto3
import logging
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path

from api import schemas, crud, database, models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client('s3')

BUCKET_NAME = 'referendum-app-alpha'
FILE_NAME = 'feedback.json'

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# TODO - replace this with database creation/seeding
current_dir = Path(__file__).parent
sample_data = {}
for table in ["Bills", "Legislators", "LegislatorVotes", "LegislatorVoteEvents", "UserVotes", "Comments"]:
    filepath = f"{current_dir}/sample_data/{table}.json"
    with open(filepath, 'r') as f:
        sample_data[table] = json.load(f)


########################################################################################################

@app.put("/user")                                                       ### ADDS USER ###
async def add_user(user: schemas.UserCreate, db = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)                      
    if db_user:                                                         
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/user")                                                      ### UPDATES USER ###
async def update_user(user: schemas.UserCreate, db = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        fake_hashed_password = user.password + "notreallyhashed"
        db_user.hashed_password = fake_hashed_password
        db_user.name = user.name
        return crud.update_user(db=db, db_user=db_user)
    raise HTTPException(status_code=404, detail=f"User not found for email: {user.email}")

@app.get("/users/{user_id}")                                            ### GETS USER ###
async def get_user(user_id: int,db = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/{user_id}")                                         ### DELETES USER ###
async def delete_user(user_id: int, db = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.delete_user(db, user_id=user_id)

@app.post("/feedback")                                                  ### ADDS FEEDBACK ###
async def add_feedback(feedback: dict):
    try:
        try:
            response = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
            file_content = json.loads(response['Body'].read().decode('utf-8'))
        except s3.exceptions.NoSuchKey:
            logger.warning(f"File {FILE_NAME} not found in bucket {BUCKET_NAME}. Creating new file.")
            file_content = {"feedbackMessages": []}

        file_content['feedbackMessages'].append(feedback)

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=FILE_NAME,
            Body=json.dumps(file_content),
            ContentType='application/json'
        )
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

#############################################################################################################


@app.put("/bill")                                                       ### ADDS BILL ###
async def add_bill(bill: schemas.BillCreate, db = Depends(get_db)):     ### figure out how to check if bill exists ###
    return crud.create_bill(db=db, bill=bill)

@app.post("/bill")                                                      ### UPDATES BILL ###
async def update_bill(bill: schemas.Bill, db = Depends(get_db)):        ### figure out how to check if bill exists ###
    db_bill = crud.get_bill(db, bill_id=bill)
    if db_bill:
        return crud.update_bill(db=db, db_bill=db_bill)
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill.id}")

@app.get("/bills/{bill_id}")                                            ### GETS BILL ###
async def get_bill(bill_id: int,db = Depends(get_db)):                  ### THIS DOESNT WORK ###
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill:    
        return db_bill
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}")

@app.get("/bills/{bill_id}/text")                                       ### GETS BILL TEXT ###
async def get_bill_text(bill_id: str):                                  ### THIS ISNT DONE ###
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}

@app.delete("/bills/{bill_id}")                                         ### DELETES USER ###
async def delete_bill(bill_id: int, db = Depends(get_db)):
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill is None:
        raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}")
    return crud.delete_bill(db, user_id=bill_id)


# @app.get("/bills")
# async def get_bills(
#     limit: int = Query(10, ge=1, le=100),
#     offset: int = Query(0, ge=0),
#     tags: Optional[List[str]] = Query(None)
# ):
#     bills = sample_data["Bills"]

#     if tags:
#         bills = [bill for bill in bills if any(tag in bill.get('tags', []) for tag in tags)]

#     total = len(bills)
#     bills = bills[offset:offset + limit]

#     return {
#         "bills": bills,
#         "total": total,
#         "limit": limit,
#         "offset": offset
#     }











@app.get("/legislators")
async def get_legislators():
    return sample_data["Legislators"]

@app.get("/legislator-vote-events")
async def get_legislator_vote_events():
    return sample_data["LegislatorVoteEvents"]

@app.get("/legislator-votes")
async def get_legislator_votes():
    return sample_data["LegislatorVotes"]

@app.get("/user-votes")
async def get_user_votes(user_id: str = Query(...)):
    return [vote for vote in sample_data["UserVotes"] if vote.get("user_id") == user_id]

@app.get("/comments")
async def get_comments():
    return sample_data["Comments"]



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)

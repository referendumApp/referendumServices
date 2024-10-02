import boto3
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

from common.database.referendum import connection, crud, schemas

from .auth import authenticate_user, create_access_token, get_user_for_token, get_token, get_password_hash
from .schemas import Token
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client("s3")


def get_db():
    db = connection.SessionLocal()
    try:
        yield db
    finally:
        db.close()


########################################################################################################
# Auth
########################################################################################################


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


########################################################################################################
# Health
########################################################################################################


@app.get("/health")
async def healthcheck(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return
    except Exception:
        raise HTTPException(status_code=500, detail="Database is not connected")


########################################################################################################
# Users
########################################################################################################


@app.put("/users")
async def add_user(user: schemas.UserCreate, db=Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


@app.post("/users")
async def update_user(user: schemas.UserCreate, db=Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        db_user.hashed_password = get_password_hash(user.password)
        db_user.name = user.name
        return crud.update_user(db=db, db_user=db_user)
    raise HTTPException(status_code=404, detail=f"User not found for email: {user.email}.")


@app.get("/users/{user_id}")
async def get_user(user_id: int, db=Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return db_user


@app.get("/users/me")
async def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)):
    current_user = await get_user_for_token(token, db)
    return current_user


@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db=Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return crud.delete_user(db, user_id=user_id)


########################################################################################################
# User Feedback
########################################################################################################


@app.post("/feedback")
async def add_feedback(feedback: dict):
    try:
        try:
            response = s3.get_object(Bucket=settings.ALPHA_BUCKET_NAME, Key=settings.FEEDBACK_FILE_NAME)
            file_content = json.loads(response["Body"].read().decode("utf-8"))
        except s3.exceptions.NoSuchKey:
            logger.warning(
                f"File {settings.FEEDBACK_FILE_NAME} not found in bucket {settings.ALPHA_BUCKET_NAME}. Creating new file."
            )
            file_content = {"feedbackMessages": []}

        file_content["feedbackMessages"].append(feedback)

        s3.put_object(
            Bucket=settings.ALPHA_BUCKET_NAME,
            Key=settings.FEEDBACK_FILE_NAME,
            Body=json.dumps(file_content),
            ContentType="application/json",
        )
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}.")


#############################################################################################################


@app.put("/bills")  ### ADDS BILL ###
async def add_bill(bill: schemas.BillCreate, db=Depends(get_db)):
    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        raise HTTPException(status_code=400, detail="Bill already exists.")
    return crud.create_bill(db=db, bill=bill)


@app.post("/bills")  ### UPDATES BILL ###
async def update_bill(bill: schemas.Bill, db=Depends(get_db)):

    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        db_bill.title = bill.title
        return crud.update_bill(db=db, db_bill=db_bill)
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill.id}.")


@app.get("/bills/{bill_id}")  ### GETS BILL ###
async def get_bill(bill_id: int, db=Depends(get_db)):
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill:
        return db_bill
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}.")


@app.get("/bills/{bill_id}/text")  ### GETS BILL TEXT ###
async def get_bill_text(bill_id: str):  ### THIS ISNT DONE ###
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}


@app.delete("/bills/{bill_id}")  ### DELETES BILL ###
async def delete_bill(bill_id: int, db=Depends(get_db)):
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill is None:
        raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}.")
    return crud.delete_bill(db, bill_id=bill_id)


######################################################################################


@app.put("/legislators")  ### ADDS LEGISLATOR ###
async def add_legislator(legislator: schemas.LegislatorCreate, db=Depends(get_db)):
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        raise HTTPException(status_code=400, detail="Legislator already exists.")
    return crud.create_legislator(db=db, legislator=legislator)


@app.post("/legislators")  ### UPDATES LEGISLATOR ###
async def update_legislator(legislator: schemas.Legislator, db=Depends(get_db)):
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        update_data = legislator.model_dump()
        for key, value in update_data.items():
            setattr(db_legislator, key, value)
        return crud.update_legislator(db=db, db_legislator=db_legislator)
    raise HTTPException(status_code=404, detail=f"Could not update legislator ID: {legislator.id}.")


@app.get("/legislators/{legislator_id}")  ### GETS LEGISLATOR ###
async def get_legislator(legislator_id: int, db=Depends(get_db)):
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator:
        return db_legislator
    raise HTTPException(status_code=404, detail=f"legislator not found for ID: {legislator_id}.")


@app.delete("/legislators/{legislator_id}")  ### DELETES LEGISLATOR ###
async def delete_legislator(legislator_id: int, db=Depends(get_db)):
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator is None:
        raise HTTPException(status_code=404, detail=f"Legislator not found for ID: {legislator_id}.")
    return crud.delete_legislator(db, legislator_id=legislator_id)


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

# @app.get("/legislators")
# async def get_legislators():
#     return sample_data["Legislators"]

# @app.get("/legislator-vote-events")
# async def get_legislator_vote_events():
#     return sample_data["LegislatorVoteEvents"]

# @app.get("/legislator-votes")
# async def get_legislator_votes():
#     return sample_data["LegislatorVotes"]

# @app.get("/user-votes")
# async def get_user_votes(user_id: str = Query(...)):
#     return [vote for vote in sample_data["UserVotes"] if vote.get("user_id") == user_id]

# @app.get("/comments")
# async def get_comments():
#     return sample_data["Comments"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)

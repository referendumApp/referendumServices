import boto3
from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text

from common.database.referendum import connection, crud, schemas

from .auth import authenticate_user, create_access_token, get_user_for_token, get_password_hash, oauth2_scheme
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


async def get_current_user_or_verify_system_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token == settings.SYSTEM_ACCESS_TOKEN:
        return {"is_system": True}
    try:
        user = await get_user_for_token(token, db)
        return {"is_system": False, "user": user}
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


########################################################################################################
# Auth
########################################################################################################


@app.post("/signup", response_model=schemas.User)
async def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


# @app.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = authenticate_user(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token = create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}


########################################################################################################
# Health
########################################################################################################


@app.get("/health")
async def healthcheck(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database is not connected")


########################################################################################################
# Users
########################################################################################################


@app.put("/users")
async def add_user(
    user: schemas.UserCreate, db: Session = Depends(get_db), auth_info: dict = Depends(get_current_user_or_verify_system_token)
):
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can create users.")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed_password = get_password_hash(user.password)
    return crud.create_user(db=db, user=user, hashed_password=hashed_password)


@app.post("/users")
async def update_user(
    user: schemas.UserCreate, db: Session = Depends(get_db), auth_info: dict = Depends(get_current_user_or_verify_system_token)
):
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.email != user.email:
            raise HTTPException(status_code=403, detail="You can only update your own user information.")
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        hashed_password = get_password_hash(user.password)
        db_user.hashed_password = hashed_password
        db_user.name = user.name
        return crud.update_user(db=db, db_user=db_user)
    raise HTTPException(status_code=404, detail=f"User not found for email: {user.email}.")


@app.get("/users/{user_id}")
async def get_user(
    user_id: int, db: Session = Depends(get_db), auth_info: dict = Depends(get_current_user_or_verify_system_token)
):
    if not auth_info["is_system"]:
        current_user = auth_info["user"]
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="You can only retrieve your own user information.")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return db_user


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int, db: Session = Depends(get_db), auth_info: dict = Depends(get_current_user_or_verify_system_token)
):
    if not auth_info["is_system"]:
        raise HTTPException(status_code=403, detail="Only system token can delete users.")
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


@app.put("/bills")
async def add_bill(bill: schemas.BillCreate, db=Depends(get_db)):
    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        raise HTTPException(status_code=400, detail="Bill already exists.")
    return crud.create_bill(db=db, bill=bill)


@app.post("/bills")
async def update_bill(bill: schemas.Bill, db=Depends(get_db)):

    db_bill = crud.get_bill_by_legiscan_id(db, legiscan_id=bill.legiscan_id)
    if db_bill:
        db_bill.title = bill.title
        return crud.update_bill(db=db, db_bill=db_bill)
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill.id}.")


@app.get("/bills/{bill_id}")
async def get_bill(bill_id: int, db=Depends(get_db)):
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill:
        return db_bill
    raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}.")


@app.get("/bills/{bill_id}/text")
async def get_bill_text(bill_id: str):
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}


@app.delete("/bills/{bill_id}")
async def delete_bill(bill_id: int, db=Depends(get_db)):
    db_bill = crud.get_bill(db, bill_id=bill_id)
    if db_bill is None:
        raise HTTPException(status_code=404, detail=f"Bill not found for ID: {bill_id}.")
    return crud.delete_bill(db, bill_id=bill_id)


######################################################################################


@app.put("/legislators")
async def add_legislator(legislator: schemas.LegislatorCreate, db=Depends(get_db)):
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        raise HTTPException(status_code=400, detail="Legislator already exists.")
    return crud.create_legislator(db=db, legislator=legislator)


@app.post("/legislators")
async def update_legislator(legislator: schemas.Legislator, db=Depends(get_db)):
    db_legislator = crud.get_legislator_by_name_and_state(db, name=legislator.name, state=legislator.state)
    if db_legislator:
        update_data = legislator.model_dump()
        for key, value in update_data.items():
            setattr(db_legislator, key, value)
        return crud.update_legislator(db=db, db_legislator=db_legislator)
    raise HTTPException(status_code=404, detail=f"Could not update legislator ID: {legislator.id}.")


@app.get("/legislators/{legislator_id}")
async def get_legislator(legislator_id: int, db=Depends(get_db)):
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator:
        return db_legislator
    raise HTTPException(status_code=404, detail=f"legislator not found for ID: {legislator_id}.")


@app.delete("/legislators/{legislator_id}")
async def delete_legislator(legislator_id: int, db=Depends(get_db)):
    db_legislator = crud.get_legislator(db, legislator_id=legislator_id)
    if db_legislator is None:
        raise HTTPException(status_code=404, detail=f"Legislator not found for ID: {legislator_id}.")
    return crud.delete_legislator(db, legislator_id=legislator_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)

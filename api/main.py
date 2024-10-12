import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging

from .config import settings
from .endpoints import (
    health,
    authentication,
    users,
    bills,
    topics,
    follow,
    legislative_bodys,
    legislators,
    partys,
    roles,
    states,
    committees,
    bill_actions,
    legislator_votes,
    comments,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(authentication.router, tags=["authentication"], prefix="/auth")
app.include_router(bills.router, tags=["bills"], prefix="/bills")
app.include_router(bill_actions.router, tags=["bill_actions"], prefix="/bill_actions")
app.include_router(comments.router, tags=["comments"], prefix="/comments")
app.include_router(committees.router, tags=["committees"], prefix="/committees")
app.include_router(follow.router, tags=["follow"], prefix="/follow")
app.include_router(legislators.router, tags=["legislators"], prefix="/legislators")
app.include_router(
    legislator_votes.router, tags=["legislator_votes"], prefix="/legislator_votes"
)
app.include_router(
    legislative_bodys.router, tags=["legislative_bodys"], prefix="/legislative_bodys"
)
app.include_router(partys.router, tags=["partys"], prefix="/partys")
app.include_router(roles.router, tags=["roles"], prefix="/roles")
app.include_router(states.router, tags=["states"], prefix="/states")
app.include_router(topics.router, tags=["topics"], prefix="/topics")
app.include_router(users.router, tags=["users"], prefix="/users")


########################################################################################################
# User Feedback
########################################################################################################


@app.post("/feedback")
async def add_feedback(feedback: dict):
    try:
        try:
            response = s3.get_object(
                Bucket=settings.ALPHA_BUCKET_NAME, Key=settings.FEEDBACK_FILE_NAME
            )
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
        logger.info(f"Feedback added successfully: {feedback}")
        return
    except Exception as e:
        logger.error(f"Error adding feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}.")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting application")
    uvicorn.run(app, host="0.0.0.0", port=80, reload=True)

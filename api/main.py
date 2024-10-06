import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging

from .config import settings
from .endpoints import health, authentication, users, bills, topics, follow

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
app.include_router(follow.router, tags=["follow"], prefix="/follow")
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
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80, reload=True)

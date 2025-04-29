import boto3
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import json
import logging

from common.database.referendum import models

from .security import get_current_user
from .settings import settings
from .endpoints import (
    _core,
    health,
    authentication,
    users,
    bills,
    topics,
    legislative_bodys,
    legislators,
    partys,
    roles,
    states,
    committees,
    bill_actions,
    legislator_votes,
    comments,
    bill_versions,
    vote_choices,
    sessions,
    statuses,
    executive_orders,
    presidents,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")
ses = boto3.client("ses", region_name=settings.AWS_REGION)

app = FastAPI(root_path=f"/{settings.ENVIRONMENT}")
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
app.include_router(bill_versions.router, tags=["bill_versions"], prefix="/bill_versions")
app.include_router(comments.router, tags=["comments"], prefix="/comments")
app.include_router(committees.router, tags=["committees"], prefix="/committees")
app.include_router(executive_orders.router, tags=["executive_orders"], prefix="/executive_orders")
app.include_router(legislators.router, tags=["legislators"], prefix="/legislators")
app.include_router(legislator_votes.router, tags=["legislator_votes"], prefix="/legislator_votes")
app.include_router(
    legislative_bodys.router, tags=["legislative_bodys"], prefix="/legislative_bodys"
)
app.include_router(partys.router, tags=["partys"], prefix="/partys")
app.include_router(presidents.router, tags=["presidents"], prefix="/presidents")
app.include_router(roles.router, tags=["roles"], prefix="/roles")
app.include_router(sessions.router, tags=["sessions"], prefix="/sessions")
app.include_router(states.router, tags=["states"], prefix="/states")
app.include_router(statuses.router, tags=["statuses"], prefix="/statuses")
app.include_router(topics.router, tags=["topics"], prefix="/topics")
app.include_router(users.router, tags=["users"], prefix="/users")
app.include_router(vote_choices.router, tags=["vote_choices"], prefix="/vote_choices")


########################################################################################################
# User Feedback
########################################################################################################


@app.post("/feedback")
@_core.handle_general_exceptions()
async def add_feedback(
    feedback: dict,
    user: models.User = Depends(get_current_user),
):
    feedback = {**feedback, "user": user.email}

    feedback_filename = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    s3.put_object(
        Bucket=settings.FEEDBACK_BUCKET_NAME,
        Key=f"feedback/{feedback_filename}",
        Body=json.dumps(feedback, indent=2),
        ContentType="application/json",
    )
    logger.info(f"Feedback saved to s3 as {feedback_filename}: {feedback}")

    email_body = json.dumps(feedback, indent=2)
    ses.send_email(
        Source="admin@referendumapp.com",
        Destination={"ToAddresses": ["feedback@referendumapp.com"]},
        Message={
            "Subject": {
                "Data": f"New(ish) User Feedback Received ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
            },
            "Body": {"Text": {"Data": email_body}},
        },
    )
    logger.info(f"Feedback email sent")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting application")
    uvicorn.run(app, host="0.0.0.0", port=80, reload=True)

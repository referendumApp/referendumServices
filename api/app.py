import json
import boto3
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from . import sample_data

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

s3 = boto3.client('s3')

BUCKET_NAME = 'referendum-app-alpha'
FILE_NAME = 'feedback.json'


@app.post("/feedback")
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

@app.get("/bills")
async def get_bills(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tags: Optional[List[str]] = Query(None)
):
    bills = sample_data.bills

    if tags:
        bills = [bill for bill in bills if any(tag in bill.get('tags', []) for tag in tags)]

    total = len(bills)
    bills = bills[offset:offset + limit]

    return {
        "bills": bills,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/bills/{bill_id}/text")
async def get_bill_text(bill_id: str):
    lorem_ipsum = "Lorem ipsum dolor sit amet"
    return {"bill_id": bill_id, "text": lorem_ipsum}

@app.get("/legislators")
async def get_legislators():
    return sample_data.legislators

@app.get("/legislator-vote-events")
async def get_legislator_vote_events():
    return sample_data.legislator_vote_events

@app.get("/legislator-votes")
async def get_legislator_votes():
    return sample_data.legislators

@app.get("/user-votes")
async def get_user_votes(user_id: str = Query(...)):
    return sample_data.user_votes.get(user_id, [])

@app.get("/comments")
async def get_comments():
    return [
        {
            "user": "John Doe",
            "text": "This bill seems promising. I particularly like the focus on environmental protection.",
            "timestamp": "2024-09-16T14:00:00Z",
            "parentId": None,
            "billId": 1,
            "upvotes": [3,5,2] # These are user IDs of users that have upvoted
        },
        {
            "user": "Jane Smith",
            "text": "I agree, but I'm concerned about the potential economic impact. Has there been an analysis?",
            "timestamp": "2024-09-16T15:00:00Z",
            "parentId": None,
            "billId": 1,
            "upvotes": [3,5,2]
        }
    ]



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=80)

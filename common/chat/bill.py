from datetime import datetime
import uuid
from typing import Dict, Optional, List
from pydantic import BaseModel
from fastapi import HTTPException


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ChatSession(BaseModel):
    session_id: str
    bill_version_id: int
    initial_prompt: str
    text: str
    chat_history: List[ChatMessage]
    session_start_time: datetime
    last_activity: datetime


class ChatSessionManager:
    def __init__(self, max_bill_length: int, session_timeout_seconds: int):
        self._sessions: Dict[str, ChatSession] = {}
        self.max_bill_length = max_bill_length
        self.session_timeout_seconds = session_timeout_seconds
        self.default_prompt = (
            "Your name is Bill and you are an expert in analyzing legislative bills. "
            "You are helping a concerned citizen understand the following bill. "
            "Please provide clear, accurate information based on the bill's content. "
            "If you're unsure about something, you must say so."
        )

    def create_session(self, bill_version_id: int, bill_text: str) -> str:
        if len(bill_text.split()) > self.max_bill_length:
            raise HTTPException(
                status_code=400,
                detail=f"Bill exceeds maximum length of {self.max_bill_length} words",
            )

        session_id = str(uuid.uuid4())
        current_time = datetime.utcnow()

        self._sessions[session_id] = ChatSession(
            session_id=session_id,
            bill_version_id=bill_version_id,
            initial_prompt=self.default_prompt,
            text=bill_text,
            chat_history=[],
            session_start_time=current_time,
            last_activity=current_time,
        )

        return session_id

    def get_session(self, session_id: str) -> ChatSession:
        session = self._sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        if (datetime.utcnow() - session.last_activity).seconds > self.session_timeout_seconds:
            self._sessions.pop(session_id)
            raise HTTPException(status_code=404, detail="Chat session has expired")

        return session

    def send_llm_request(self, llm_request: List[Dict]) -> str:
        return "LLM says: ..."

    def send_message(self, session_id: str, user_message: str) -> str:
        session = self.get_session(session_id)

        # Get formatted payload for LLM
        payload = self.create_llm_payload(session_id, user_message)

        ai_response = self.send_llm_request(payload)

        current_time = datetime.utcnow()
        session.chat_history.append(
            ChatMessage(role="user", content=user_message, timestamp=current_time)
        )
        session.chat_history.append(
            ChatMessage(role="assistant", content=ai_response, timestamp=current_time)
        )
        session.last_activity = current_time

        return ai_response

    def create_llm_payload(self, session_id: str, message: str) -> List[Dict[str, str]]:
        session = self.get_session(session_id)
        return [
            {"role": "system", "content": session.initial_prompt},
            {"role": "system", "content": f"Bill text: {session.text}"},
            *[{"role": msg.role, "content": msg.content} for msg in session.chat_history],
            {"role": "user", "content": message},
        ]

    def terminate_session(self, session_id: str) -> None:
        self._sessions.pop(session_id)

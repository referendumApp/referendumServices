from typing import Optional, List, Dict
from datetime import datetime
from uuid import uuid4

from common.core.schemas import CamelCaseBaseModel
from common.chat.service import OpenAIException, LLMService


class ChatMessage(CamelCaseBaseModel):
    role: str
    content: str
    timestamp: datetime


class BillChatSession:
    """Manages an individual chat session about a bill"""

    DEFAULT_SYSTEM_PROMPT = (
        "Your name is Bill and you are an expert in analyzing legislative bills. "
        "You are helping a concerned citizen understand the following bill. "
        "Please provide clear, accurate information based on the bill's content. "
        "If you're unsure about something, you must say so."
    )

    def __init__(
        self,
        session_id: str,
        bill_version_id: int,
        bill_text: str,
        llm_service: LLMService,
        system_prompt: Optional[str] = None,
    ):
        self.session_id = session_id
        self.bill_version_id = bill_version_id
        self.bill_text = bill_text
        self.chat_history: List[ChatMessage] = []
        self.session_start_time = datetime.utcnow()
        self.last_activity = self.session_start_time

        self.chain = llm_service.create_conversation_chain(
            system_prompt or self.DEFAULT_SYSTEM_PROMPT, initial_context=f"Bill text: {bill_text}"
        )

    def send_message(self, user_message: str) -> str:
        try:
            response = self.chain.predict(input=user_message)
        except OpenAIException as e:
            raise ConnectionError(f"Failed to fetch LLM response with error: {str(e)}")

        current_time = datetime.utcnow()
        self.chat_history.extend(
            [
                ChatMessage(role="user", content=user_message, timestamp=current_time),
                ChatMessage(role="assistant", content=response, timestamp=current_time),
            ]
        )
        self.last_activity = current_time

        return response


class BillChatSessionManager:
    def __init__(
        self,
        openai_api_key: str,
        max_bill_length: int,
        session_timeout_seconds: int,
        model_name: str = "gpt-3.5-turbo",
    ):
        self._sessions: Dict[str, BillChatSession] = {}
        self.max_bill_length = max_bill_length
        self.session_timeout_seconds = session_timeout_seconds
        self.llm_service = LLMService(openai_api_key=openai_api_key, model_name=model_name)

    def create_session(self, bill_version_id: int, bill_text: str) -> str:
        self._cleanup_expired_sessions()

        if len(bill_text.split()) > self.max_bill_length:
            raise ValueError(f"Bill exceeds maximum length of {self.max_bill_length} words")

        session_id = str(uuid4())
        session = BillChatSession(
            session_id=session_id,
            bill_version_id=bill_version_id,
            bill_text=bill_text,
            llm_service=self.llm_service,
        )

        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> BillChatSession:
        self._cleanup_expired_sessions()

        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Chat session {session_id} not found")

        if (datetime.utcnow() - session.last_activity).seconds > self.session_timeout_seconds:
            self.terminate_session(session_id)
            raise ValueError(f"Chat session {session_id} has expired")

        return session

    def send_message(self, session_id: str, user_message: str) -> str:
        session = self.get_session(session_id)
        return session.send_message(user_message)

    def terminate_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session.chain:
            del session.chain

    def _cleanup_expired_sessions(self) -> None:
        """Remove all sessions that have exceeded the timeout period."""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if (current_time - session.last_activity).seconds > self.session_timeout_seconds
        ]
        for session_id in expired_sessions:
            self.terminate_session(session_id)

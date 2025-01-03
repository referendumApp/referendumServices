from datetime import datetime
import uuid
from typing import Dict, Optional, List
from pydantic import BaseModel
from fastapi import HTTPException

from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import SystemMessage


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ChatSession(BaseModel):
    session_id: str
    bill_version_id: int
    text: str
    chat_history: List[ChatMessage]
    session_start_time: datetime
    last_activity: datetime
    chain: ConversationChain = None
    model_name: str = "gpt-3.5-turbo"

    def __init__(self, **data):
        super().__init__(**data)
        self.chain = self._create_conversation_chain()

    def _create_conversation_chain(self) -> ConversationChain:
        llm = ChatOpenAI(model_name=self.model_name)

        default_prompt = (
            "Your name is Bill and you are an expert in analyzing legislative bills. "
            "You are helping a concerned citizen understand the following bill. "
            "Please provide clear, accurate information based on the bill's content. "
            "If you're unsure about something, you must say so."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(default_prompt),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        memory = ConversationBufferMemory(return_messages=True)
        chain = ConversationChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

        chain.memory.chat_memory.add_message(SystemMessage(content=f"Bill text: {self.text}"))

        return chain

    def send_message(self, user_message: str) -> str:
        try:
            response = self.chain.predict(input=user_message)

            current_time = datetime.utcnow()
            self.chat_history.extend(
                [
                    ChatMessage(role="user", content=user_message, timestamp=current_time),
                    ChatMessage(role="assistant", content=response, timestamp=current_time),
                ]
            )
            self.last_activity = current_time

            return response

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


class ChatSessionManager:
    def __init__(
        self, max_bill_length: int, session_timeout_seconds: int, model_name: str = "gpt-3.5-turbo"
    ):
        self._sessions: Dict[str, ChatSession] = {}
        self.max_bill_length = max_bill_length
        self.session_timeout_seconds = session_timeout_seconds
        self.model_name = model_name

    def create_session(self, bill_version_id: int, bill_text: str) -> str:
        if len(bill_text.split()) > self.max_bill_length:
            raise HTTPException(
                status_code=400,
                detail=f"Bill exceeds maximum length of {self.max_bill_length} words",
            )

        session_id = str(uuid.uuid4())
        current_time = datetime.utcnow()

        session = ChatSession(
            session_id=session_id,
            bill_version_id=bill_version_id,
            text=bill_text,
            chat_history=[],
            session_start_time=current_time,
            last_activity=current_time,
            model_name=self.model_name,
        )

        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> ChatSession:
        session = self._sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        if (datetime.utcnow() - session.last_activity).seconds > self.session_timeout_seconds:
            self.terminate_session(session_id)
            raise HTTPException(status_code=404, detail="Chat session has expired")

        return session

    def send_message(self, session_id: str, user_message: str) -> str:
        session = self.get_session(session_id)
        return session.send_message(user_message)

    def terminate_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session.chain:
            del session.chain

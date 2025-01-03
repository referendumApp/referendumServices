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
from langchain.schema import SystemMessage, HumanMessage, AIMessage


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


class ChatSessionManager:
    def __init__(
        self, max_bill_length: int, session_timeout_seconds: int, model_name: str = "gpt-3.5-turbo"
    ):
        self._sessions: Dict[str, ChatSession] = {}
        self._chains: Dict[str, ConversationChain] = {}
        self.max_bill_length = max_bill_length
        self.session_timeout_seconds = session_timeout_seconds
        self.model_name = model_name

        self.default_prompt = (
            "Your name is Bill and you are an expert in analyzing legislative bills. "
            "You are helping a concerned citizen understand the following bill. "
            "Please provide clear, accurate information based on the bill's content. "
            "If you're unsure about something, you must say so."
        )

    def _create_conversation_chain(self, bill_text: str) -> ConversationChain:
        llm = ChatOpenAI(model_name=self.model_name)

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.default_prompt),
                SystemMessagePromptTemplate.from_template("Bill text: {bill_text}"),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        memory = ConversationBufferMemory(return_messages=True)

        chain = ConversationChain(llm=llm, prompt=prompt, memory=memory, verbose=True)

        chain.memory.chat_memory.add_message(SystemMessage(content=f"Bill text: {bill_text}"))

        return chain

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
            text=bill_text,
            chat_history=[],
            session_start_time=current_time,
            last_activity=current_time,
        )

        self._chains[session_id] = self._create_conversation_chain(bill_text)

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
        chain = self._chains.get(session_id)

        if not chain:
            raise HTTPException(status_code=404, detail="Chat chain not found")

        # Get response from LangChain conversation chain
        response = chain.predict(input=user_message)

        # Update session
        current_time = datetime.utcnow()
        session.chat_history.extend(
            [
                ChatMessage(role="user", content=user_message, timestamp=current_time),
                ChatMessage(role="assistant", content=response, timestamp=current_time),
            ]
        )
        session.last_activity = current_time

        return response

    def terminate_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._chains.pop(session_id, None)

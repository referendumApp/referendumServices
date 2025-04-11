from typing import Optional

from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_openai import ChatOpenAI


class OpenAIException(Exception):
    pass


class LLMService:
    """Base service for interacting with Language Models"""

    def __init__(
        self,
        openai_api_key: str,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ):
        self.llm = ChatOpenAI(
            model_name=model_name, temperature=temperature, api_key=openai_api_key
        )

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        try:
            response = await self.llm.agenerate(messages=[messages])
        except Exception as e:
            raise OpenAIException(str(e))

        return response.generations[0][0].text

    def create_conversation_chain(
        self, system_prompt: str, initial_context: Optional[str] = None
    ) -> ConversationChain:
        """Creates a conversation chain with optional initial context"""
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_prompt),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        memory = ConversationBufferMemory(return_messages=True)
        chain = ConversationChain(llm=self.llm, prompt=prompt, memory=memory, verbose=False)

        if initial_context:
            chain.memory.chat_memory.add_message(SystemMessage(content=initial_context))

        return chain

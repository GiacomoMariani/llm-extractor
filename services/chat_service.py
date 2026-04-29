import logging

from models.chat import ChatResponse
from services.exceptions import AppServiceError
from services.rule_based_chatbot import RuleBasedChatbot

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, chatbot: RuleBasedChatbot):
        self.chatbot = chatbot

    async def chat(self, message: str) -> ChatResponse:
        normalized_message = message.strip()

        try:
            return await self.chatbot.reply(normalized_message)
        except Exception as ex:
            logger.exception("Chat failed for input message.")
            raise AppServiceError("Failed to generate chat reply.") from ex
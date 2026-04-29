from models.chat import ChatResponse


class RuleBasedChatbot:
    async def reply(self, message: str) -> ChatResponse:
        normalized_message = message.strip()
        lower_message = normalized_message.lower()

        if lower_message in {"hello", "hi", "hey"}:
            return ChatResponse(reply="Hello! How can I help?")

        return ChatResponse(reply=f"You said: {normalized_message}")
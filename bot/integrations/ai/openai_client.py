import logging
from typing import Optional

from bot.config import settings
from bot.integrations.ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.error("openai package not installed")
                raise
        return self._client

    async def send_message(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> Optional[str]:
        if not settings.openai_api_key:
            return "OpenAI xizmati hozirda sozlanmagan."

        client = self._get_client()
        messages = [{"role": "system", "content": system_prompt or SYSTEM_PROMPT}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=settings.ai_max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI API error: %s", e)
            return "AI xizmatida xato yuz berdi. Keyinroq urinib ko'ring."


openai_client = OpenAIClient()

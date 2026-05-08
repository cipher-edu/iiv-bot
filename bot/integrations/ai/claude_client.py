import logging
from typing import Optional

from bot.config import settings
from bot.integrations.ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                logger.error("anthropic package not installed")
                raise
        return self._client

    async def send_message(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None,
        system_prompt: str | None = None,
    ) -> Optional[str]:
        if not settings.anthropic_api_key:
            return "AI xizmati hozirda sozlanmagan."

        client = self._get_client()
        messages = []

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        try:
            response = await client.messages.create(
                model=settings.ai_model,
                max_tokens=settings.ai_max_tokens,
                system=system_prompt or SYSTEM_PROMPT,
                messages=messages,
            )
            return response.content[0].text
        except Exception as e:
            logger.error("Claude API error: %s", e)
            return "AI xizmatida xato yuz berdi. Keyinroq urinib ko'ring."

    async def generate_test(self, topic: str, count: int = 5) -> Optional[str]:
        from bot.integrations.ai.prompts import TEST_GENERATION_PROMPT
        prompt = TEST_GENERATION_PROMPT.format(topic=topic, count=count)
        return await self.send_message(prompt)

    async def summarize_content(self, content: str) -> Optional[str]:
        from bot.integrations.ai.prompts import COURSE_SUMMARY_PROMPT
        prompt = COURSE_SUMMARY_PROMPT.format(content=content)
        return await self.send_message(prompt)


claude_client = ClaudeClient()

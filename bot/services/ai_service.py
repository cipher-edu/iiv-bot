import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.repositories.base import BaseRepository
from bot.models.ai_history import AIConversation, AIMessage

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, user_id: int) -> AIConversation:
        from sqlalchemy import select
        stmt = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id, AIConversation.is_active == True)
            .order_by(AIConversation.created_at.desc())
        )
        result = await self.session.execute(stmt)
        conv = result.scalar_one_or_none()

        if not conv:
            from bot.config import settings
            conv = AIConversation(user_id=user_id, is_active=True, model_used=settings.ai_model)
            self.session.add(conv)
            await self.session.flush()

        return conv

    async def get_history(self, conversation_id: int, limit: int = 20) -> list[dict]:
        from sqlalchemy import select
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content} for m in messages]

    async def save_message(
        self, conversation_id: int, role: str, content: str,
    ) -> AIMessage:
        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def chat(self, user_id: int, user_message: str) -> str:
        conv = await self.get_or_create_conversation(user_id)
        await self.save_message(conv.id, "user", user_message)

        history = await self.get_history(conv.id)

        if settings.anthropic_api_key:
            from bot.integrations.ai.claude_client import claude_client
            response = await claude_client.send_message(user_message, history[:-1])
        elif settings.openai_api_key:
            from bot.integrations.ai.openai_client import openai_client
            response = await openai_client.send_message(user_message, history[:-1])
        else:
            response = "AI xizmati hozirda sozlanmagan. Admin bilan bog'laning."

        await self.save_message(conv.id, "assistant", response)
        return response

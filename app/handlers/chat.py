import asyncio
import logging
from aiogram import F, Router
from aiogram.types import Message
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramNetworkError

logger = logging.getLogger(__name__)


def _format_user_identity(message: Message) -> str:
    user = message.from_user
    if not user:
        return "User: unknown"

    parts = [
        f"id={user.id}",
        f"username=@{user.username}" if user.username else "username=none",
    ]
    full_name = " ".join(filter(None, [user.first_name, user.last_name])).strip()
    parts.append(f"name={full_name}" if full_name else "name=none")
    parts.append(f"language={user.language_code or 'unknown'}")
    return "User: " + ", ".join(parts)


def _session_key(message: Message, is_private: bool) -> str:
    if is_private:
        uid = message.from_user.id if message.from_user else message.chat.id
        return f"user:{uid}"
    return f"chat:{message.chat.id}"


def register_chat_handlers(router: Router, llm_client, context_store) -> None:
    async def _send_with_retry(message: Message, text: str, attempts: int = 3) -> None:
        for attempt in range(1, attempts + 1):
            try:
                await message.answer(text)
                return
            except TelegramNetworkError as exc:
                if attempt == attempts:
                    logger.exception("Failed to send message after retries: %s", exc)
                    raise
                logger.warning("Telegram network error, retry %s/%s: %s", attempt, attempts, exc)
                await asyncio.sleep(1)

    @router.message(F.text)
    async def handle_free_text(message: Message):
        if not message.text or message.text.startswith("/"):
            return

        is_private = message.chat.type == "private"
        session_key = _session_key(message, is_private)
        user_identity = _format_user_identity(message)
        text = message.text.strip()
        enriched_text = f"{user_identity}\nMessage: {text}"

        await context_store.append(session_key, "user", enriched_text)
        history = await context_store.history(session_key)

        if not is_private and "мерс" not in text.lower():
            return

        try:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        except Exception:
            pass

        try:
            reply = await llm_client.generate(history, temperature=0.3)
            if not reply:
                reply = "❌ Не удалось получить ответ от модели."
        except Exception as e:
            logger.exception("LLM error: %s", e)
            reply = "❌ Ошибка при обращении к модели. Попробуйте позже."

        await context_store.append(session_key, "assistant", reply)
        try:
            await _send_with_retry(message, reply)
        except TelegramNetworkError:
            # Если не удалось отправить даже после ретраев, просто выходим
            pass



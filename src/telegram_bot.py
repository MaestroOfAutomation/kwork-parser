import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from loguru import logger


class TelegramBot:
    """Транспорт: умеет отправить текст в чат и закрыться. О заказах ничего не знает."""

    def __init__(self, token: str) -> None:
        self._bot = Bot(
            token=token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML,
                link_preview_is_disabled=True,
            )
        )

    async def __aenter__(self) -> "TelegramBot":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def send_message(self, chat_id: str | int, text: str) -> bool:
        """
        Отправляет сообщение, при флуд-лимите ждёт и делает одну повторную попытку.
        Неудача — это предупреждение в логе, а не исключение: воркер должен жить дальше.
        """
        for attempt in (1, 2):
            try:
                await self._bot.send_message(chat_id, text)
                return True
            except TelegramRetryAfter as e:
                if attempt == 2:
                    logger.warning("Telegram снова просит подождать, сообщение пропущено")
                    return False
                logger.warning(f"Telegram просит подождать {e.retry_after} с, повторю")
                await asyncio.sleep(e.retry_after)
            except TelegramAPIError as e:
                logger.warning(f"Не удалось отправить сообщение в Telegram: {e.message}")
                return False

        return False

    async def close(self) -> None:
        await self._bot.session.close()

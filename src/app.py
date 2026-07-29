import asyncio

import aiohttp
from loguru import logger

from src.configuration import Settings
from src.parser import KworkParser
from src.telegram_bot import TelegramBot


class CategoryWatcher:
    """Опрашивает одну категорию и отправляет новые заказы в Telegram."""

    def __init__(
            self,
            parser: KworkParser,
            bot: TelegramBot,
            chat_id: int,
            poll_interval: int,
    ) -> None:
        self._parser = parser
        self._bot = bot
        self._chat_id = chat_id
        self._poll_interval = poll_interval

    async def run(self) -> None:
        while True:
            await self._poll_once()
            await asyncio.sleep(self._poll_interval)

    async def _poll_once(self) -> None:
        try:
            orders = await self._parser.fetch_new_orders()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Категория {self._parser.category_id}: запрос к kwork не удался — {e}")
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(f"Категория {self._parser.category_id}: непредвиденная ошибка")
            return

        for order in orders:
            logger.success(order.to_log_line())
            await self._bot.send_message(self._chat_id, order.to_message())


class Application:
    """Владеет жизненным циклом: HTTP-сессия, бот и воркеры по категориям."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def run(self) -> None:
        async with aiohttp.ClientSession() as session, TelegramBot(self._settings.tg_token) as bot:
            watchers = [
                CategoryWatcher(
                    parser=KworkParser(
                        session=session,
                        category_id=category_id,
                        timeout_seconds=self._settings.request_timeout_seconds,
                    ),
                    bot=bot,
                    chat_id=self._settings.tg_chat_id,
                    poll_interval=self._settings.poll_interval,
                )
                for category_id in self._settings.category_ids
            ]

            logger.info(f"Запуск, категорий в работе: {len(watchers)}")
            await asyncio.gather(*(watcher.run() for watcher in watchers))

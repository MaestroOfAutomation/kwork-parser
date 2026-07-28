import aiohttp
import asyncio

from aiogram import Bot
from loguru import logger

from src.configuration import Settings
from src.parser import fetch_new_orders
from src.telegram_notifier import send_orders


async def fetch_worker(bot: Bot, settings: Settings, category_id: str) -> None:
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                orders: list[dict] = await fetch_new_orders(
                    session=session,
                    category_id=category_id,
                    timeout_seconds=settings.request_timeout_seconds,
                )
                if orders:
                    await send_orders(bot=bot, chat_id=settings.tg_chat_id, orders=orders)
            except Exception:
                logger.exception(f"При проверке новых заказов {category_id=} произошла ошибка")

            await asyncio.sleep(settings.poll_interval)


async def runner() -> None:
    settings = Settings()
    if not settings.tg_token:
        logger.error("Заполните переменную TELEGRAM_BOT_TOKEN в .env")
        return

    logger.add("parser.log", rotation="1 week")  # файл-лог

    bot = Bot(token=settings.tg_token)

    fetch_worker_tasks = [
        fetch_worker(bot=bot, settings=settings, category_id=category_id)
        for category_id in settings.categories.split(',')
    ]

    await asyncio.gather(*fetch_worker_tasks)


if __name__ == "__main__":
    asyncio.run(runner())

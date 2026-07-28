from aiogram import Bot
from loguru import logger

from src.constants import MESSAGE_TEMPLATE


def _format_price(value: int | str) -> str:
    value_int = int(float(value))
    return f"{value_int:,}".replace(",", " ")


async def send_orders(bot: Bot, chat_id: int | str, orders: list[dict]) -> None:
    for order in orders:
        title = order["name"]
        url: str = f"https://kwork.ru/projects/{order['id']}"
        title_with_url: str = f"<a href='{url}'>{title}</a>"

        want_price: str = order.get("priceLimit", "unknown")
        max_price: str = order.get('possiblePriceLimit', "unknown")

        description: str = order.get("description", "")

        text: str = MESSAGE_TEMPLATE.format(
            title=title_with_url,
            description=description,
            price_from=_format_price(want_price),
            price_to=_format_price(max_price),
        )

        logger.success(text)

        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception:
            logger.exception('Не удалось отправить уведомление в Telegram')

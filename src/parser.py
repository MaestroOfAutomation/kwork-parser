from collections import defaultdict

import aiohttp
from loguru import logger
import orjson

from src.constants import HEADERS, KWORK_URL

SEEN_IDS_BY_CATEGORY_ID: dict[str, set[int]] = defaultdict(set)


async def fetch_new_orders(
        session: aiohttp.ClientSession,
        category_id: str,
        timeout_seconds: int,
) -> list[dict]:
    """
    Возвращает новые заказы (кроме тех, что уже были замечены).
    Первая итерация только инициализирует SEEN_IDS по категории и ничего не отдает,
    чтобы не спамить уже существующими задачами при первом запуске.
    """
    seen_ids: set[int] = SEEN_IDS_BY_CATEGORY_ID[category_id]

    form = aiohttp.FormData()
    form.add_field("c", category_id)
    form.add_field("page", "1")

    async with session.post(
            url=KWORK_URL,
            data=form,
            headers=HEADERS,
            timeout=timeout_seconds,
    ) as response:
        response.raise_for_status()
        data = await response.json(loads=orjson.loads)

    wants: list[dict] = data["data"]["wants"]

    if not seen_ids:
        seen_ids.update({want["id"] for want in wants})
        logger.info(f"Инициализация списка seen для {category_id=}, первую выборку пропускаем")
        return []

    fresh: list[dict] = [
        want for want in wants
        if want["id"] not in seen_ids
    ]
    if fresh:
        logger.info(f"Найдено новых заказов для {category_id=}: {len(fresh)}")
        seen_ids.update(want["id"] for want in fresh)

    return fresh

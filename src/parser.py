import aiohttp
from loguru import logger
import orjson
from pydantic import ValidationError

from src.models import Order


class KworkParser:
    """
    Опрашивает одну категорию kwork и отдаёт только те заказы, которых ещё не видел.

    Дедупликация идёт по максимальному id: идентификаторы на kwork монотонно растут,
    поэтому «поднятые» заказчиком старые заказы повторно не приходят.
    """

    URL = "https://kwork.ru/projects"

    HEADERS = {
        'sec-ch-ua-platform': '"macOS"',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'Origin': 'https://kwork.ru',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Language': 'en',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    def __init__(
            self,
            session: aiohttp.ClientSession,
            category_id: str,
            timeout_seconds: int,
    ) -> None:
        self._session = session
        self._category_id = category_id
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._last_seen_id: int | None = None

    @property
    def category_id(self) -> str:
        return self._category_id

    async def fetch_new_orders(self) -> list[Order]:
        """
        Возвращает новые заказы, от старых к новым.
        Первый вызов только запоминает текущее состояние доски и отдаёт пустой список,
        чтобы при запуске не прислать пачку уже существующих заказов.
        """
        orders = await self._fetch_orders()
        if not orders:
            return []

        newest_id = max(order.id for order in orders)

        if self._last_seen_id is None:
            self._last_seen_id = newest_id
            logger.info(f"Категория {self._category_id}: первая выборка пропущена")
            return []

        fresh = sorted(
            (order for order in orders if order.id > self._last_seen_id),
            key=lambda order: order.id,
        )
        self._last_seen_id = newest_id

        if fresh:
            logger.info(f"Категория {self._category_id}: новых заказов — {len(fresh)}")

        return fresh

    async def _fetch_orders(self) -> list[Order]:
        form = aiohttp.FormData()
        form.add_field("c", self._category_id)
        form.add_field("page", "1")

        async with self._session.post(
                url=self.URL,
                data=form,
                headers=self.HEADERS,
                timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            data = await response.json(loads=orjson.loads)

        parsed = (self._parse_order(want) for want in data["data"]["wants"])
        return [order for order in parsed if order is not None]

    def _parse_order(self, want: dict) -> Order | None:
        try:
            return Order.model_validate(want)
        except ValidationError as e:
            fields = ", ".join(str(error["loc"][0]) for error in e.errors())
            logger.warning(f"Заказ {want.get('id')} пропущен, проблемные поля: {fields}")
            return None

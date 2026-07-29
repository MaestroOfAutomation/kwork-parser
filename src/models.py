import html
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DESCRIPTION_LIMIT = 700
LOG_DESCRIPTION_LIMIT = 110

MESSAGE_TEMPLATE = (
    "📌 {title}\n"
    "<blockquote>{description}</blockquote>\n"
    "〰️〰️〰️〰️\n"
    "💳 Бюджет: от {price_from} ₽ до {price_to} ₽\n"
    "📨 Откликов: {offers_count}   ⏳ {time_left}\n"
    "〰️〰️〰️〰️"
)


def _format_price(value: Decimal) -> str:
    return f"{int(value):,}".replace(",", " ")


def _escape(text: str) -> str:
    """Telegram понимает только &lt; &gt; &amp;, кавычки экранировать не нужно."""
    return html.escape(text, quote=False)


class Order(BaseModel):
    """Заказ с kwork.ru. Лишние поля ответа API отбрасываются."""

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str
    price_from: Decimal = Field(validation_alias="priceLimit")
    price_to: Decimal = Field(validation_alias="possiblePriceLimit")
    offers_count: int = Field(validation_alias="kwork_count")
    time_left: str = Field(validation_alias="timeLeft")

    @field_validator("description")
    @classmethod
    def _decode_entities(cls, value: str) -> str:
        """В описании приходят HTML-сущности вида &laquo; и &mdash;."""
        return html.unescape(value).strip()

    @property
    def url(self) -> str:
        return f"https://kwork.ru/projects/{self.id}"

    @property
    def price(self) -> str:
        if self.price_from == self.price_to:
            return f"{_format_price(self.price_from)} ₽"
        return f"{_format_price(self.price_from)}–{_format_price(self.price_to)} ₽"

    def shorten_description(self, limit: int, one_line: bool = False) -> str:
        text = " ".join(self.description.split()) if one_line else self.description
        if len(text) <= limit:
            return text
        return text[:limit].rstrip() + "…"

    def to_message(self) -> str:
        """Готовый текст уведомления в разметке Telegram HTML."""
        return MESSAGE_TEMPLATE.format(
            title=f"<a href='{self.url}'>{_escape(self.name)}</a>",
            description=_escape(self.shorten_description(DESCRIPTION_LIMIT)),
            price_from=_format_price(self.price_from),
            price_to=_format_price(self.price_to),
            offers_count=self.offers_count,
            time_left=self.time_left,
        )

    def to_log_line(self) -> str:
        """Компактная карточка заказа для консоли — та же информация, без разметки."""
        return f"""
        📌 {self.name}
        💰 {self.price}   📨 откликов: {self.offers_count}   ⏳ {self.time_left}
        📝 {self.shorten_description(LOG_DESCRIPTION_LIMIT, one_line=True)}
        🔗 {self.url}
        """

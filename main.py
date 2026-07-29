import asyncio
import sys

from loguru import logger

from src.app import Application
from src.configuration import Settings


LOG_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>"
)


def _setup_logging() -> None:
    """Только консоль. Запись в файл пока не нужна — добавить сюда logger.add('parser.log')."""
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # эмодзи на Windows-консоли
    logger.remove()
    logger.add(sys.stderr, format=LOG_FORMAT, level="INFO")


def main() -> None:
    _setup_logging()

    settings = Settings()

    problem = settings.find_problem()
    if problem:
        logger.error(problem)
        return

    try:
        asyncio.run(Application(settings).run())
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")


if __name__ == "__main__":
    main()

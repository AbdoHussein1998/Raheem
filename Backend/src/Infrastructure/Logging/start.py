import sys
from pathlib import Path

from loguru._logger import Logger
from loguru import logger as loguru_logger


class LoggerManager:
    """Centralized application logging manager using Loguru."""

    def __init__(
        self,
        log_dir: str | Path = "logs",
        logger: Logger | None = None,
    ) -> None:
        self.logger = logger or loguru_logger
        self.log_dir = Path(log_dir)
        self._configured = False

    def configure_logger(self, level: str = "INFO") -> None:
        """Configure colored console logging and persistent file logging."""

        # Create the logs directory if it doesn't exist.
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing sinks to prevent duplicate log messages.
        self.logger.remove()

        # Default context for messages that aren't bound to a context.
        self.logger.configure(extra={"context": "application"})

        # Colored console format.
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[context]}</cyan> | "
            "<cyan>{name}:{function}:{line}</cyan> - "
            "<level>{message}</level>"
        )

        # Plain-text format for log files.
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{extra[context]} | "
            "{name}:{function}:{line} - "
            "{message}"
        )

        # 1. Console sink: colored output.
        self.logger.add(
            sys.stderr,
            level=level,
            format=console_format,
            colorize=True,
            backtrace=False,
            diagnose=False,
        )

        # 2. File sink: persistent logs.
        self.logger.add(
            str(self.log_dir / "application_{time:YYYY-MM-DD}.log"),
            level=level,
            format=file_format,
            rotation="00:00",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            colorize=False,
            backtrace=False,
            diagnose=False,
        )

        self._configured = True

    def get_logger(self, context_name: str) -> Logger:
        """Return a logger bound to a specific application context."""

        if not context_name.strip():
            raise ValueError("context_name cannot be empty.")

        # Initialize logging automatically on the first call.
        if not self._configured:
            self.configure_logger()

        return self.logger.bind(context=context_name)




        
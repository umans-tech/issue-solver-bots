import json
import logging
import sys


class StructuredLogRecord(logging.LogRecord):
    """
    Custom LogRecord class for structured logging.
    This will be useful in the future when you enable structured logging.
    """

    def getMessage(self) -> str:
        """
        Return the formatted message, formatted according
        to whether it's in structured logging mode or not.
        """
        msg = super().getMessage()

        # Return the message as is if not using structured logging
        if not hasattr(self, "structured_logging") or not self.structured_logging:
            return msg

        # If we reach here, we're using structured logging
        # and need to format the log as JSON
        log_data = {
            "timestamp": self.created,
            "level": self.levelname,
            "message": msg,
            "module": self.module,
            "function": self.funcName,
            "line": self.lineno,
        }

        # Add extra attributes passed to the logger
        if hasattr(self, "extra") and self.extra:
            log_data.update(self.extra)

        return json.dumps(log_data)


class LoggingConfig:
    """Centralized logging configuration."""

    def __init__(
        self,
        default_level: int = logging.INFO,
        format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        use_structured_logging: bool = False,
    ):
        """
        Initialize logging configuration.

        Args:
            default_level: Default logging level
            format_string: Format string for logs (only used when not in structured mode)
            use_structured_logging: Whether to enable structured JSON logging
        """
        self.default_level = default_level
        self.format_string = format_string
        self.use_structured_logging = use_structured_logging
        self.configured = False

    def configure(self):
        """Set up the basic configuration for logging."""
        if self.configured:
            return

        # If structured logging is enabled, we'll use our custom LogRecord
        if self.use_structured_logging:
            logging.setLogRecordFactory(StructuredLogRecord)

        # Configure the root logger
        handlers = [logging.StreamHandler(sys.stdout)]

        logging.basicConfig(
            level=self.default_level,
            format=self.format_string,
            handlers=handlers,
        )

        self.configured = True

    def get_logger(
        self, name: str, level: int | None = None
    ) -> logging.Logger | logging.LoggerAdapter:
        """
        Get a configured logger for the specified module.

        Args:
            name: The logger name (typically __name__ from the calling module)
            level: Optional specific level for this logger

        Returns:
            Configured logger instance, which might be a Logger or LoggerAdapter
            if structured logging is enabled
        """
        if not self.configured:
            self.configure()

        base_logger = logging.getLogger(name)
        base_logger.setLevel(level or self.default_level)

        # Enable propagation to the root logger
        base_logger.propagate = True

        # Set a flag to indicate if we're using structured logging
        if self.use_structured_logging:
            # This will be accessible in the LogRecord
            return logging.LoggerAdapter(base_logger, {"structured_logging": True})

        return base_logger


# Default singleton instance to use across the application
default_logging_config = LoggingConfig(
    default_level=logging.INFO,
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    use_structured_logging=False,  # Default to standard logging for now
)

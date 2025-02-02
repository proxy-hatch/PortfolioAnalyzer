import logging
import sys

from lib.model.enum.stage import Stage

_log_instance = None


def get_logger() -> logging.Logger:
    """
    Retrieves the global logger instance. Initializes it if it hasn't been created yet.

    :param stage: The current environment stage (DEV, UAT, PROD).
    :return: A logger instance.
    """
    global _log_instance
    if _log_instance is None:
        print("Logger is not initialized! Initializing in debug setting", file=sys.stderr)
        _log_instance = initialize_logger(Stage.DEV)
    return _log_instance


def initialize_logger(stage: Stage) -> logging.Logger:
    """
    Initializes the logger with the appropriate logging level based on the stage.

    :param stage: The current environment stage (DEV, UAT, PROD).
    :return: An initialized logger instance.
    """
    logger = logging.getLogger(__name__)
    logging_level = logging.INFO if stage == Stage.PROD else logging.DEBUG
    logger.setLevel(logging_level)

    if not logger.hasHandlers():
        console_handler: logging.Handler = logging.StreamHandler()
        console_handler.setLevel(logging_level)

        formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    global _log_instance
    _log_instance = logger
    return logger

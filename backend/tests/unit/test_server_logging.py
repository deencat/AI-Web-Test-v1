import logging

from app.utils.server_logging import suppress_noisy_file_loggers


def test_suppress_noisy_file_loggers_sets_watchfiles_loggers_to_warning():
    watchfiles_logger = logging.getLogger("watchfiles")
    watchfiles_main_logger = logging.getLogger("watchfiles.main")
    original_levels = (watchfiles_logger.level, watchfiles_main_logger.level)

    try:
        watchfiles_logger.setLevel(logging.INFO)
        watchfiles_main_logger.setLevel(logging.INFO)

        suppress_noisy_file_loggers()

        assert watchfiles_logger.level == logging.WARNING
        assert watchfiles_main_logger.level == logging.WARNING
    finally:
        watchfiles_logger.setLevel(original_levels[0])
        watchfiles_main_logger.setLevel(original_levels[1])
import logging


NOISY_FILE_LOGGERS = (
    "watchfiles",
    "watchfiles.main",
)


def suppress_noisy_file_loggers(level: int = logging.WARNING) -> None:
    """Reduce noise from dev-server reload loggers in file-backed server logs."""
    for logger_name in NOISY_FILE_LOGGERS:
        logging.getLogger(logger_name).setLevel(level)
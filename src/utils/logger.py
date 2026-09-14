import logging
import os
from datetime import datetime


def get_logger(context: str = "ammeter_test_framework") -> logging.Logger:
    """
    Returns a configured logging.Logger for the given context, attaching
    file + console handlers the first time this context is used (same
    logger name -> same handlers, so one log file per process, not per call).
    """
    logger = logging.getLogger(f"test_{context}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        log_dir = "results/logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/{timestamp}_{context}.log"

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)
        logger.addHandler(stream_handler)

    return logger

import logging
import os
from datetime import datetime

class TestLogger:
    def __init__(self, test_name: str):
        self._test_name = test_name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        הגדרת הלוגר עם פורמט מותאם וכתיבה לקובץ
        """
        # יצירת תיקיית הלוגים
        log_dir = "results/logs"
        os.makedirs(log_dir, exist_ok=True)

        # הגדרת שם הקובץ עם תאריך ומזהה הבדיקה
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{log_dir}/{timestamp}_{self._test_name}.log"

        # הגדרת הלוגר
        logger = logging.getLogger(f"test_{self._test_name}")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if not logger.handlers:
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

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message) 
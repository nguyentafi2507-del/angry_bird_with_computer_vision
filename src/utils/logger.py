"""
src/utils/logger.py
Ghi log sự kiện game ra console (dùng để debug va chạm, bắn, trạng thái level...).
"""
import logging
import sys

_LOGGER_NAME = "angry_bird"


def get_logger():
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
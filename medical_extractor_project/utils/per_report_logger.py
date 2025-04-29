import os
import logging

def setup_report_logger(log_path: str):
    """
    Set up a file-based logger for a specific report.
    """
    logger = logging.getLogger(f"report_logger_{log_path}")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger

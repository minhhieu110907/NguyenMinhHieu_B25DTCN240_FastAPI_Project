import logging
import sys

def setup_global_logging():
    # Delete old handler
    logging.root.handlers = []
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler]
    )
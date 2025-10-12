import logging
import os
from logging.handlers import RotatingFileHandler
from from_root import from_root
from datetime import datetime

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    # fallback if colorama isn't available
    class DummyColor:
        def __getattr__(self, name): return ''
    Fore = Style = DummyColor()


# === Log directory setup ===
LOG_DIR = 'logs'
LOG_FILE = f"{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

log_dir_path = os.path.join(from_root(), LOG_DIR)
os.makedirs(log_dir_path, exist_ok=True)
log_file_path = os.path.join(log_dir_path, LOG_FILE)


# === Custom Formatter ===
class ContextFormatter(logging.Formatter):
    def format(self, record):
        # Add context if available (like startup name)
        context = getattr(record, "context", "")
        if context:
            record.msg = f"[{context}] {record.msg}"
        return super().format(record)


# === Logger Configuration ===
def configure_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler (for CI, long-term logs)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
    file_formatter = ContextFormatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler (colored output for local or CI runs)
    console_handler = logging.StreamHandler()

    class ColorFormatter(ContextFormatter):
        COLORS = {
            "INFO": Fore.CYAN,
            "DEBUG": Fore.WHITE,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "CRITICAL": Fore.MAGENTA,
        }

        def format(self, record):
            color = self.COLORS.get(record.levelname, "")
            message = super().format(record)
            return f"{color}{message}{Style.RESET_ALL}"

    console_formatter = ColorFormatter("[%(asctime)s] %(levelname)s - %(message)s", "%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Reset previous handlers (avoid duplicate logs)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


# === Initialize Logger ===
configure_logger()
logging.info("Structured logger initialized successfully.")

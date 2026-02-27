import logging
from .config import config

# Define log file paths
playback_log_file = config.log_path / "playback.log"
error_log_file = config.log_path / "error.log"

# --- Playback Logger Setup ---
playback_logger = logging.getLogger("Playback")
playback_logger.setLevel(logging.INFO)
p_handler = logging.FileHandler(playback_log_file, encoding='utf-8')
p_handler.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
if not playback_logger.handlers:
    playback_logger.addHandler(p_handler)

# --- Error Logger Setup ---
error_logger = logging.getLogger("Error")
error_logger.setLevel(logging.ERROR)
e_handler = logging.FileHandler(error_log_file, encoding='utf-8')
e_handler.setFormatter(logging.Formatter('%(asctime)s | ERROR | %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
if not error_logger.handlers:
    error_logger.addHandler(e_handler)

# --- Helper Functions ---
def log_playback(title, url):
    """Logs successfully started media"""
    playback_logger.info(f"PLAYING: {title} -> {url}")

def log_error(error_msg):
    """Logs system crashes or network failures"""
    error_logger.error(error_msg)

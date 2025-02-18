import logging
import os
from logging.handlers import RotatingFileHandler

# log info level logs to stdout and debug to debug file

debug_log_format = "%(levelname)s %(asctime)s - [%(filename)s:%(lineno)d] - %(message)s"
logging.basicConfig(
    handlers=[RotatingFileHandler(f"{os.getenv('BOT_CONFIG_DIR', './config')}/debug.log", maxBytes=500000, backupCount=10)],
    level=logging.DEBUG,
    format=debug_log_format)

console_output = logging.StreamHandler()
console_output.setLevel(logging.INFO)
console_format = logging.Formatter(debug_log_format)
console_output.setFormatter(console_format)

info_log_file = RotatingFileHandler(f"{os.getenv('BOT_CONFIG_DIR', './config')}/info.log", maxBytes=100000, backupCount=10)
info_log_file.setLevel(logging.INFO)
info_log_format = logging.Formatter(debug_log_format)
info_log_file.setFormatter(info_log_format)

logging.root.addHandler(console_output)
logging.root.addHandler(info_log_file)


def get_logger(name):
    l = logging.getLogger(name)
    return l

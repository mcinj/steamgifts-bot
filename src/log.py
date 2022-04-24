import logging
from logging.handlers import RotatingFileHandler

# log info level logs to stdout and debug to debug file

log_format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(
        handlers=[RotatingFileHandler('../config/debug.log', maxBytes=100000, backupCount=10)],
        level=logging.DEBUG,
        format=log_format)

stream = logging.StreamHandler()
stream.setLevel(logging.INFO)
stream_format = logging.Formatter(log_format)
stream.setFormatter(stream_format)

def get_logger(name):
    l = logging.getLogger(name)
    l.addHandler(stream)
    return l

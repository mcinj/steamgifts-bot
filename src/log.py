import logging
from logging.handlers import RotatingFileHandler

# log info level logs to stdout and debug to debug file

log_format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(
    handlers=[RotatingFileHandler('../config/debug.log', maxBytes=500000, backupCount=10)],
    level=logging.DEBUG,
    format=log_format)

console_output = logging.StreamHandler()
console_output.setLevel(logging.INFO)
console_format = logging.Formatter(log_format)
console_output.setFormatter(console_format)

info_log_file = RotatingFileHandler('../config/info.log', maxBytes=500000, backupCount=10)
info_log_file.setLevel(logging.INFO)
info_log_format = logging.Formatter(log_format)
info_log_file.setFormatter(info_log_format)

logging.root.addHandler(console_output)
logging.root.addHandler(info_log_file)

logging.info("""
-------------------------------------------------------------------------------------
   _____  _                                  _   __  _          ____          _   
  / ____|| |                                (_) / _|| |        |  _ \        | |  
 | (___  | |_  ___   __ _  _ __ ___    __ _  _ | |_ | |_  ___  | |_) |  ___  | |_ 
  \___ \ | __|/ _ \ / _` || '_ ` _ \  / _` || ||  _|| __|/ __| |  _ <  / _ \ | __|
  ____) || |_|  __/| (_| || | | | | || (_| || || |  | |_ \__ \ | |_) || (_) || |_ 
 |_____/  \__|\___| \__,_||_| |_| |_| \__, ||_||_|   \__||___/ |____/  \___/  \__|
                                       __/ |                                      
                                      |___/                                       
-------------------------------------------------------------------------------------
""")


def get_logger(name):
    l = logging.getLogger(name)
    return l

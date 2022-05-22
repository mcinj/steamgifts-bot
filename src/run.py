import os
from time import sleep

from src.bot.log import get_logger
from src.bot.config_reader import ConfigReader, ConfigException
from src.bot.enter_giveaways import SteamGiftsException
from src.bot.giveaway_thread import GiveawayThread
from src.bot.notification import Notification
from src.bot.database import run_db_migrations
from src.web.webserver_thread import WebServerThread

logger = get_logger(__name__)
config_file_name = f"{os.getenv('BOT_CONFIG_DIR', './config')}/config.ini"
db_url = f"{os.getenv('BOT_DB_URL', 'sqlite:///./config/sqlite.db')}"
alembic_migration_files = os.getenv('BOT_ALEMBIC_CONFIG_DIR', './src/alembic')


def run():
    logger.info("Starting Steamgifts bot.")

    config = None
    try:
        config = ConfigReader(config_file_name)
    except IOError:
        txt = f"{config_file_name} doesn't exist. Rename {config_file_name}.example to {config_file_name} and fill out."
        logger.warning(txt)
        exit(-1)
    except ConfigException as e:
        logger.error(e)
        exit(-1)

    config.read(config_file_name)

    notification = Notification(config['NOTIFICATIONS'].get('notification.prefix'))
    pushover_enabled = config['NOTIFICATIONS'].getboolean('pushover.enabled')
    pushover_token = config['NOTIFICATIONS'].get('pushover.token')
    pushover_user_key = config['NOTIFICATIONS'].get('pushover.user_key')
    if pushover_enabled:
        notification.enable_pushover(pushover_token, pushover_user_key)
    try:
        g = GiveawayThread(config, notification)
        g.setName("Giveaway Enterer")
        g.start()

        w = WebServerThread(config)
        w.setName("WebServer")
        # if the giveaway thread dies then this daemon thread will die by design
        w.setDaemon(True)
        w.start()

        g.join()
    except SteamGiftsException as e:
        notification.send_error(e)
        sleep(5)
        exit(-1)
    except Exception as e:
        logger.error(e)
        notification.send_error("Something happened and the bot had to quit!")
        sleep(10)
        exit(-1)


def entry():
    logger.info("""
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
    run_db_migrations(alembic_migration_files, db_url)
    run()


if __name__ == '__main__':
    entry()

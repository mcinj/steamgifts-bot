from time import sleep

import log
from config_reader import ConfigReader, ConfigException
from enter_giveaways import SteamGiftsException
from giveaway_thread import GiveawayThread
from notification import Notification
from webserver_thread import WebServerThread

logger = log.get_logger(__name__)


def run():
    logger.info("Starting Steamgifts bot.")
    file_name = '../config/config.ini'
    config = None
    try:
        config = ConfigReader(file_name)
    except IOError:
        txt = f"{file_name} doesn't exist. Rename {file_name}.example to {file_name} and fill out."
        logger.warning(txt)
        exit(-1)
    except ConfigException as e:
        logger.error(e)
        exit(-1)

    config.read(file_name)

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


if __name__ == '__main__':
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
    run()

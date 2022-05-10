from random import randint
from time import sleep

import log
from ConfigReader import ConfigReader, ConfigException
from SteamGifts import SteamGifts, SteamGiftsException
from notification import Notification


logger = log.get_logger(__name__)


def run():
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
        cookie = config['DEFAULT'].get('cookie')

        enabled = config['DEFAULT'].getboolean('enabled')
        minimum_points = config['DEFAULT'].getint('minimum_points')
        max_entries = config['DEFAULT'].getint('max_entries')
        max_time_left = config['DEFAULT'].getint('max_time_left')
        minimum_game_points = config['DEFAULT'].getint('minimum_game_points')
        blacklist = config['DEFAULT'].get('blacklist_keywords')

        all_page = SteamGifts(cookie, 'All', False, minimum_points, max_entries,
                              max_time_left, minimum_game_points, blacklist, notification)

        wishlist_enabled = config['WISHLIST'].getboolean('wishlist.enabled')
        wishlist_minimum_points = config['WISHLIST'].getint('wishlist.minimum_points')
        wishlist_max_entries = config['WISHLIST'].getint('wishlist.max_entries')
        wishlist_max_time_left = config['WISHLIST'].getint('wishlist.max_time_left')

        wishlist_page = SteamGifts(cookie, 'Wishlist', False, wishlist_minimum_points,
                                   wishlist_max_entries, wishlist_max_time_left, 0, '', notification)

        if not enabled and not wishlist_enabled:
            logger.error("Both 'Default' and 'Wishlist' configurations are disabled. Nothing will run. Exiting...")
            sleep(10)
            exit(-1)

        while True:
            if wishlist_enabled:
                wishlist_page.start()
            if enabled:
                all_page.start()

            random_seconds = randint(1740, 3540)  # sometime between 29-59 minutes
            logger.info(f"Going to sleep for {random_seconds / 60} minutes.")
            sleep(random_seconds)
    except SteamGiftsException as e:
        notification.send_error(e)
        sleep(5)
        exit(-1)
    except Exception as e:
        logger.error(e)
        notification.send_error("Something happened and the bot had to quit!")
        sleep(5)
        exit(-1)


if __name__ == '__main__':
    run()

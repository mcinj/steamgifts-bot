import datetime
import threading
from datetime import timedelta, datetime
from random import randint
from threading import Thread
from time import sleep

from dateutil import tz

from .log import get_logger
from .enter_giveaways import EnterGiveaways

logger = get_logger(__name__)


class GiveawayThread(threading.Thread):

    def __init__(self, config, notification):
        Thread.__init__(self)
        self.exc = None
        self.config = config
        self.notification = notification

    def run_steam_gifts(self, config, notification):
        cookie = config['DEFAULT'].get('cookie')
        user_agent = config['DEFAULT'].get('user_agent')
        main_page_enabled = config['DEFAULT'].getboolean('enabled')
        minimum_points = config['DEFAULT'].getint('minimum_points')
        max_entries = config['DEFAULT'].getint('max_entries')
        max_time_left = config['DEFAULT'].getint('max_time_left')
        minimum_game_points = config['DEFAULT'].getint('minimum_game_points')
        blacklist = config['DEFAULT'].get('blacklist_keywords')

        all_page = EnterGiveaways(cookie, user_agent, 'All', False, minimum_points, max_entries,
                                  max_time_left, minimum_game_points, blacklist, notification)

        wishlist_page_enabled = config['WISHLIST'].getboolean('wishlist.enabled')
        wishlist_minimum_points = config['WISHLIST'].getint('wishlist.minimum_points')
        wishlist_max_entries = config['WISHLIST'].getint('wishlist.max_entries')
        wishlist_max_time_left = config['WISHLIST'].getint('wishlist.max_time_left')

        wishlist_page = EnterGiveaways(cookie, user_agent, 'Wishlist', False, wishlist_minimum_points,
                                       wishlist_max_entries, wishlist_max_time_left, 0, '', notification)

        if not main_page_enabled and not wishlist_page_enabled:
            logger.error("⁉️ Both 'Default' and 'Wishlist' configurations are disabled. Nothing will run. Exiting...")
            sleep(10)
            exit(-1)

        while True:
            logger.info("🟢 Evaluating giveaways.")
            if wishlist_page_enabled:
                wishlist_page.start()
            if main_page_enabled:
                all_page.start()

            logger.info("🔴 All giveaways evaluated.")
            random_seconds = randint(1740, 3540)  # sometime between 29-59 minutes
            when_to_start_again = datetime.now(tz=tz.tzlocal()) + timedelta(seconds=random_seconds)
            logger.info(f"🛋 Going to sleep for {random_seconds / 60} minutes. "
                        f"Will start again at {when_to_start_again}")
            sleep(random_seconds)

    def run(self):
        # Variable that stores the exception, if raised by someFunction
        self.exc = None
        try:
            self.run_steam_gifts(self.config, self.notification)
        except BaseException as e:
            self.exc = e

    def join(self):
        threading.Thread.join(self)
        # Since join() returns in caller thread
        # we re-raise the caught exception
        # if any was caught
        if self.exc:
            raise self.exc

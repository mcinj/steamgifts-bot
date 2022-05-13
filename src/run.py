import threading
from random import randint
from time import sleep

import log
from ConfigReader import ConfigReader, ConfigException
from SteamGifts import SteamGifts, SteamGiftsException
from notification import Notification
from threading import Thread


logger = log.get_logger(__name__)


class WebServerThread(threading.Thread):

    def run_webserver(self):
        import http.server
        import socketserver

        PORT = 8000

        class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.path = 'index.html'
                return http.server.SimpleHTTPRequestHandler.do_GET(self)

        Handler = MyHttpRequestHandler

        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("Http Server Serving at port", PORT)
            httpd.serve_forever()

    def run(self):
        # Variable that stores the exception, if raised by someFunction
        self.exc = None
        try:
            self.run_webserver()
        except BaseException as e:
            self.exc = e

    def join(self):
        threading.Thread.join(self)
        # Since join() returns in caller thread
        # we re-raise the caught exception
        # if any was caught
        if self.exc:
            raise self.exc


class GiveawayEntererThread(threading.Thread):

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

        all_page = SteamGifts(cookie, user_agent, 'All', False, minimum_points, max_entries,
                              max_time_left, minimum_game_points, blacklist, notification)

        wishlist_page_enabled = config['WISHLIST'].getboolean('wishlist.enabled')
        wishlist_minimum_points = config['WISHLIST'].getint('wishlist.minimum_points')
        wishlist_max_entries = config['WISHLIST'].getint('wishlist.max_entries')
        wishlist_max_time_left = config['WISHLIST'].getint('wishlist.max_time_left')

        wishlist_page = SteamGifts(cookie, user_agent, 'Wishlist', False, wishlist_minimum_points,
                                   wishlist_max_entries, wishlist_max_time_left, 0, '', notification)

        if not main_page_enabled and not wishlist_page_enabled:
            logger.error("Both 'Default' and 'Wishlist' configurations are disabled. Nothing will run. Exiting...")
            sleep(10)
            exit(-1)

        while True:
            if wishlist_page_enabled:
                wishlist_page.start()
            if main_page_enabled:
                all_page.start()

            random_seconds = randint(1740, 3540)  # sometime between 29-59 minutes
            logger.info(f"Going to sleep for {random_seconds / 60} minutes.")
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
        g = GiveawayEntererThread(config, notification)
        g.setName("Giveaway Enterer")
        g.start()

        w = WebServerThread()
        w.setName("WebServer")
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
        sleep(5)
        exit(-1)


if __name__ == '__main__':
    run()

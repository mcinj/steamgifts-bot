import threading
from random import randint
from time import sleep

from flask_basicauth import BasicAuth

import log
from ConfigReader import ConfigReader, ConfigException
from SteamGifts import SteamGifts, SteamGiftsException
from notification import Notification
from threading import Thread


logger = log.get_logger(__name__)


class WebServerThread(threading.Thread):

    def __init__(self, config):
        Thread.__init__(self)
        self.exc = None
        self.config = config
        self.port = config['WEB'].getint('web.port')
        self.ssl = config['WEB'].getboolean('web.ssl')
        self.enabled = config['WEB'].getboolean('web.enabled')
        self.app_root = config['WEB'].get('web.app_root')
        self.basic_auth = config['WEB'].getboolean('web.basic_auth')
        self.basic_auth_username = config['WEB'].get('web.basic_auth.username')
        self.basic_auth_password = config['WEB'].get('web.basic_auth.password')

    def run_webserver(self):
        from flask import Flask
        from flask import render_template

        app = Flask(__name__)

        if self.basic_auth:
            app.config['BASIC_AUTH_USERNAME'] = self.basic_auth_username
            app.config['BASIC_AUTH_PASSWORD'] = self.basic_auth_password

        app.config['BASIC_AUTH_FORCE'] = self.basic_auth
        basic_auth = BasicAuth(app)

        @app.route(f"{self.app_root}")
        def config():
            with open('../config/config.ini', 'r') as f:
                content = f.read()
            return render_template('configuration.html', config=content)

        @app.route(f"{self.app_root}log")
        def logs():
            return render_template('log.html')

        @app.route(f"{self.app_root}stream")
        def stream():
            def generate():
                with open('../config/info.log') as f:
                    while True:
                        yield f.read()
                        sleep(10)

            return app.response_class(generate(), mimetype='text/plain')

        if self.enabled:
            logger.info("Webserver Enabled. Running")
            if self.ssl:
                app.run(port=self.port, host="0.0.0.0", ssl_context='adhoc')
            else:
                app.run(port=self.port, host="0.0.0.0")
        else:
            logger.info("Webserver NOT Enabled.")

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
            logger.info(f"🛋 Going to sleep for {random_seconds / 60} minutes.")
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

        w = WebServerThread(config)
        w.setName("WebServer")
        # if the giveaway thread dies then this daemon thread will die by definition
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

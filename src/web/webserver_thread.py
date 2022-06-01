import os
import threading
from threading import Thread

from flask_basicauth import BasicAuth

from src.bot.database import NotificationHelper, GiveawayHelper
from src.bot.log import get_logger

logger = get_logger(__name__)


class WebServerThread(threading.Thread):

    def __init__(self, config):
        Thread.__init__(self)
        self.exc = None
        self.config = config
        self.prefix = config['NOTIFICATIONS'].get('notification.prefix')
        self.host = config['WEB'].get('web.host')
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
            with open(f"{os.getenv('BOT_CONFIG_DIR', './config')}/config.ini", 'r') as f:
                data = f.read()
            return render_template('configuration.html', name=self.prefix, data=data)

        @app.route(f"{self.app_root}log_info")
        def log_info():
            with open(f"{os.getenv('BOT_CONFIG_DIR', './config')}/info.log", 'r') as f:
                data = f.read()
                return render_template('log.html', name=self.prefix, log_type='info', data=data)

        @app.route(f"{self.app_root}log_debug")
        def log_debug():
            with open(f"{os.getenv('BOT_CONFIG_DIR', './config')}/debug.log", 'r') as f:
                data = f.read()
                return render_template('log.html', name=self.prefix, log_type='debug', data=data)

        @app.route(f"{self.app_root}alive")
        def alive():
            return 'OK'

        @app.route(f"{self.app_root}notifications")
        def db_notifications():
            return render_template('notifications.html', name=self.prefix, data=NotificationHelper.get())

        @app.route(f"{self.app_root}giveaways", methods=['GET'], defaults={"page": 1})
        @app.route(f"{self.app_root}giveaways/<int:page>", methods=['GET'])
        def db_giveaways(page):
            return render_template('giveaways.html', name=self.prefix, data=GiveawayHelper.paginate(page=page))

        @app.route(f"{self.app_root}stats")
        def stats():
            totals = GiveawayHelper.total_giveaways()
            entered = GiveawayHelper.total_entered()
            return render_template('stats.html', name=self.prefix, totals=totals, entered=entered)

        if self.enabled:
            logger.info("Webserver Enabled. Running")
            if self.ssl:
                app.run(port=self.port, host=self.host, ssl_context='adhoc')
            else:
                app.run(port=self.port, host=self.host)
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

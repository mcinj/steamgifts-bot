import threading
from threading import Thread
from time import sleep

from flask_basicauth import BasicAuth

import log

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

        @app.route(f"{self.app_root}alive")
        def alive():
            return 'OK'

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
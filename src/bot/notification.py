import http.client
import urllib

from .log import get_logger
from .database import NotificationHelper

logger = get_logger(__name__)


class Notification:

    def __init__(self, message_prefix):
        self.pushover = False
        self.pushover_token = None
        self.pushover_user_key = None
        self.message_prefix = f"{message_prefix}: "

    def send_won(self, message, number_won):
        self.__send('won', message, number_won)

    def send_error(self, message):
        self.__send('error', message, number_won=None)

    def enable_pushover(self, token, user_key):
        logger.debug("Enabling pushover notifications.")
        self.pushover = True
        self.pushover_token = token
        self.pushover_user_key = user_key

    def __send(self, type_of_error, message, number_won=None):
        logger.debug(f"Attempting to notify: '{message}'. Won: {number_won}")
        if self.pushover:
            logger.debug("Pushover enabled. Sending message.")
            self.__pushover(type_of_error, message, number_won)

    def __pushover(self, type_of_error, message, number_won=None):
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
                     urllib.parse.urlencode({
                         "token": self.pushover_token,
                         "user": self.pushover_user_key,
                         "message": f"{self.message_prefix}{message}",
                     }), {"Content-type": "application/x-www-form-urlencoded"})
        response = conn.getresponse()
        logger.debug(f"Pushover response code: {response.getcode()}")
        if response.getcode() == 200:
            success = True
        else:
            logger.error(f"Pushover notification failed. Code {response.getcode()}: {response.read().decode()}")
            success = False
        NotificationHelper.insert(type_of_error, f"{message}", 'pushover', success, number_won)

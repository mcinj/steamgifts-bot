import http.client
import urllib

from sqlalchemy.orm import Session

from tables import engine, TableNotification
import log

logger = log.get_logger(__name__)


class Notification:

    def __init__(self):
        self.pushover = False
        self.pushover_token = None
        self.pushover_user_key = None
        self.message_prefix = "SG-bot: "

    def send(self, type_of_error, message):
        logger.debug(f"Attempting to notify: {message}")
        if self.pushover:
            logger.debug("Pushover enabled. Sending message.")
            self.__pushover(type_of_error, message)

    def enable_pushover(self, token, user_key):
        logger.debug("Enabling pushover notifications.")
        self.pushover = True
        self.pushover_token = token
        self.pushover_user_key = user_key

    def __pushover(self, type_of_error, message):
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
            n = TableNotification(type=type_of_error, message=f"{message}", medium='pushover', success=True)
        else:
            logger.error(f"Pushover notification failed. Code {response.getcode()}: {response.read().decode()}")
            n = TableNotification(type=type_of_error, message=f"{message}", medium='pushover', success=False)
        with Session(engine) as session:
            session.add(n)
            session.commit()



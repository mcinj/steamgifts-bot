import re
from .log import get_logger
import time

logger = get_logger(__name__)


class WonEntry:

    def __init__(self, soup_item):
        self.game_name = None
        self.giveaway_game_id = None
        self.giveaway_uri = None

        logger.debug(f"Won Giveaway html: {soup_item}")
        self.game_name = soup_item.find('a', {'class': 'table__column__heading'}).text
        self.giveaway_game_id = soup_item.find('a', {'class': 'table__column__heading'})['href'].split('/')[2]
        self.giveaway_uri = soup_item.select_one('a.table__column__heading')['href']
        logger.debug(f"Scraped Won Giveaway: {self}")

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

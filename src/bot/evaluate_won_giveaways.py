import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .database import GiveawayHelper
from .log import get_logger
from .won_entry import WonEntry

logger = get_logger(__name__)


class SteamGiftsException(Exception):
    pass


class EvaluateWonGiveaways:

    def __init__(self, cookie, user_agent, notification):
        self._contributor_level = None
        self._xsrf_token = None
        self._cookie = {
            'PHPSESSID': cookie
        }
        self._user_agent = user_agent
        self._notification = notification

        self._base = "https://www.steamgifts.com/giveaways/won"
        self._session = requests.Session()

    def start(self):
        self._evaluate_won_giveaways()

    def _requests_retry_session(
            self,
            retries=5,
            backoff_factor=0.3
    ):
        session = self._session or requests.Session()
        retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=(500, 502, 504),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_soup_from_page(self, url):
        headers = {
            'User-Agent': self._user_agent
        }
        self._requests_retry_session().get(url, headers=headers)
        r = requests.get(url, cookies=self._cookie)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def _evaluate_won_giveaways(self, page=1):
        soup = self._get_soup_from_page(self._base)

        try:
            self._xsrf_token = soup.find('input', {'name': 'xsrf_token'})['value']
            self._points = int(soup.find('span', {'class': 'nav__points'}).text)  # storage points
            self._contributor_level = int(float(soup.select_one('nav a>span[title]')['title']))
        except TypeError:
            logger.error("⛔⛔⛔  Cookie is not valid. A new one must be added.⛔⛔⛔")
            raise SteamGiftsException("Cookie is not valid. A new one must be added.")

        won_game_list = soup.select('div[class=table__row-inner-wrap]')

        if not len(won_game_list):
            txt = f"🟡 No won games to evaluate"
            logger.info(txt)

        logger.info("Evaluating won giveaways")
        for item in won_game_list:
            won_giveaway = WonEntry(item)
            w = GiveawayHelper.get_by_giveaway_id(won_giveaway.giveaway_game_id)
            logger.debug(f"Giveaway in db: {w}")
            if w and not w.won and w.entered:
                logger.info(f"Marking {won_giveaway.game_name} as won.")
                logger.debug(f"Marking: {w}")
                GiveawayHelper.mark_game_as_won(won_giveaway.giveaway_game_id)


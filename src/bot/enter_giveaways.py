import json
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .log import get_logger
from .database import NotificationHelper, GiveawayHelper
from .giveaway_entry import GiveawayEntry

logger = get_logger(__name__)


class SteamGiftsException(Exception):
    pass


class EnterGiveaways:

    def __init__(self, cookie, user_agent, gifts_type, pinned, min_points, max_entries,
                 max_time_left, minimum_game_points, blacklist, notification):
        self._contributor_level = None
        self._xsrf_token = None
        self._points = None
        self._cookie = {
            'PHPSESSID': cookie
        }
        self._user_agent = user_agent
        self._gifts_type = gifts_type
        self._pinned = pinned
        self._min_points = int(min_points)
        self._max_entries = int(max_entries)
        self._max_time_left = int(max_time_left)
        self._minimum_game_points = int(minimum_game_points)
        self._blacklist = blacklist.split(',')
        self._notification = notification

        self._base = "https://www.steamgifts.com"
        self._session = requests.Session()

        self._filter_url = {
            'All': "search?page=%d",
            'Wishlist': "search?page=%d&type=wishlist",
            'Recommended': "search?page=%d&type=recommended",
            'Copies': "search?page=%d&copy_min=2",
            'DLC': "search?page=%d&dlc=true",
            'New': "search?page=%d&type=new"
        }

    def start(self):
        self._update_info()
        if self._points >= self._min_points:
            txt = f"〰 You have {self._points} points. Evaluating '{self._gifts_type}' giveaways..."
            logger.info(txt)
            self._evaluate_giveaways()
        else:
            txt = f"🟡 You have {self._points} points which is below your minimum point threshold of " \
                  f"{self._min_points} points for '{self._gifts_type}' giveaways. Not evaluating right now."
            logger.info(txt)

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

    def _update_info(self):
        soup = self._get_soup_from_page(self._base)

        try:
            self._xsrf_token = soup.find('input', {'name': 'xsrf_token'})['value']
            self._points = int(soup.find('span', {'class': 'nav__points'}).text)  # storage points
            self._contributor_level = int(float(soup.select_one('nav a>span[title]')['title']))
        except TypeError:
            logger.error("⛔⛔⛔  Cookie is not valid. A new one must be added.⛔⛔⛔")
            raise SteamGiftsException("Cookie is not valid. A new one must be added.")

        won = soup.select("a[title='Giveaways Won'] div")
        if won:
            number_won = int(soup.select_one("a[title='Giveaways Won'] div").text)
            won_notifications = NotificationHelper.get_won_notifications_today()
            if won_notifications and len(won_notifications) >= 1:
                if number_won == won_notifications[-1].games_won:
                    logger.info("🆒️ Win(s) detected, but we have already notified that there are won games waiting "
                                "to be received. Doing nothing.")
                elif number_won > won_notifications[-1].games_won:
                    logger.info("🔥🔥 MORE win(s) detected. Notifying again.")
                    self._notification.send_won(f"You won ANOTHER game. You now have {number_won} game(s) "
                                               f"waiting to be claimed.", number_won)
                else:  # we have less games waiting to be claimed than notified, meaning some have been claimed
                    logger.info("🆒️ Win(s) detected, but we have already notified that there are won games waiting "
                                "to be received. Some have been claimed. Doing nothing.")
            else:
                logger.info(f"💰💰 WINNER! You have {number_won} game(s) waiting to be claimed. 💰💰")
                self._notification.send_won(f"WINNER! You have {number_won} game(s) waiting to be claimed.", number_won)
        else:
            logger.debug('No wins detected. Doing nothing.')

    def _should_we_enter_giveaway(self, giveaway):
        if giveaway.time_remaining_in_minutes is None:
            return False
        if giveaway.time_created_in_minutes is None:
            return False

        if self._blacklist is not None and self._blacklist != ['']:
            for keyword in self._blacklist:
                if giveaway.game_name.lower().find(keyword.lower()) != -1:
                    txt = f"〰️ Game {giveaway.game_name} contains the blacklisted keyword {keyword}"
                    logger.info(txt)
                    return False
        if giveaway.contributor_level is None or self._contributor_level < giveaway.contributor_level:
            txt = f"〰️ Game {giveaway.game_name} requires at least level {giveaway.contributor_level} contributor " \
                  f"level to enter. Your level: {self._contributor_level}"
            logger.info(txt)
            return False
        if giveaway.time_remaining_in_minutes > self._max_time_left:
            txt = f"〰️ Game {giveaway.game_name} has {giveaway.time_remaining_in_minutes} minutes left and is " \
                  f"above your cutoff of {self._max_time_left} minutes."
            logger.info(txt)
            return False
        if giveaway.game_entries / giveaway.copies > self._max_entries:
            txt = f"〰️ Game {giveaway.game_name} has {giveaway.game_entries} entries and is above your cutoff " \
                  f"of {self._max_entries} entries."
            logger.info(txt)
            return False
        if self._points - int(giveaway.cost) < 0:
            txt = f"〰️ Not enough points to enter: {giveaway.game_name}"
            logger.info(txt)
            return False
        if giveaway.cost < self._minimum_game_points:
            txt = f"〰️ Game {giveaway.game_name} costs {giveaway.cost}P and is below your cutoff of " \
                  f"{self._minimum_game_points}P."
            logger.info(txt)
            return False

        return True

    def _enter_giveaway(self, giveaway):
        headers = {
            'User-Agent': self._user_agent
        }
        payload = {'xsrf_token': self._xsrf_token, 'do': 'entry_insert', 'code': giveaway.giveaway_game_id}
        logger.debug(f"Sending enter giveaway payload: {payload}")
        entry = requests.post('https://www.steamgifts.com/ajax.php', data=payload, cookies=self._cookie,
                              headers=headers)
        json_data = json.loads(entry.text)

        if json_data['type'] == 'success':
            logger.debug(f"Successfully entered giveaway {giveaway.giveaway_game_id}: {json_data}")
            return True
        else:
            logger.error(f"❌ Failed entering giveaway {giveaway.giveaway_game_id}: {json_data}")
            return False

    def _evaluate_giveaways(self, page=1):
        n = page
        run = True
        while run and n < 3:  # hard stop safety net at page 3 as idk why we would ever get to this point
            txt = "〰️ Retrieving games from %d page." % n
            logger.info(txt)

            filtered_url = self._filter_url[self._gifts_type] % n
            paginated_url = f"{self._base}/giveaways/{filtered_url}"

            soup = self._get_soup_from_page(paginated_url)

            pinned_giveaway_count = len(soup.select('div.pinned-giveaways__outer-wrap div.giveaway__row-inner-wrap'))
            all_games_list_count = len(soup.select('div.giveaway__row-inner-wrap'))
            # this matches on a div with the exact class value so we discard ones
            # that also have a class 'is-faded' containing already entered giveaways
            unentered_game_list = soup.select('div[class=giveaway__row-inner-wrap]')
            # game_list = soup.find_all('div', {'class': 'giveaway__row-inner-wrap'})

            if not len(unentered_game_list) or (all_games_list_count == pinned_giveaway_count):
                txt = f"🟡 We have run out of gifts to consider."
                logger.info(txt)
                break

            for item in unentered_game_list:
                giveaway = GiveawayEntry(item)
                txt = f"〰 {giveaway.game_name} - {giveaway.cost}P - {giveaway.game_entries} entries " \
                      f"(w/ {giveaway.copies} copies) - Created {giveaway.time_created_string} ago " \
                      f"with {giveaway.time_remaining_string} remaining by {giveaway.user}."
                logger.info(txt)
                if giveaway.pinned and not self._pinned:
                    logger.info(f"〰️ Giveaway {giveaway.game_name} is pinned. Ignoring.")
                    continue

                if self._points == 0 or self._points < self._min_points:
                    txt = f"🟡 We have {self._points} points, but we need {self._min_points} to start."
                    logger.info(txt)
                    run = False
                    break

                if not giveaway.cost:
                    logger.error(f"Cost could not be determined for '{giveaway.game_name}'")
                    continue
                if_enter_giveaway = self._should_we_enter_giveaway(giveaway)
                if if_enter_giveaway:
                    res = self._enter_giveaway(giveaway)
                    if res:
                        GiveawayHelper.upsert_giveaway_with_details(giveaway, True, False)
                        self._points -= int(giveaway.cost)
                        txt = f"✅ Entered giveaway '{giveaway.game_name}'"
                        logger.info(txt)
                        sleep(randint(4, 15))
                    else:
                        GiveawayHelper.upsert_giveaway_with_details(giveaway, False, False)
                else:
                    GiveawayHelper.upsert_giveaway(giveaway)
                # if we are on any filter type except New and we get to a giveaway that exceeds our
                # max time left amount, then we don't need to continue to look at giveaways as any
                # after this point will also exceed the max time left
                if self._gifts_type != "New" and not giveaway.pinned and \
                        giveaway.time_remaining_in_minutes > self._max_time_left:
                    logger.info("🟡 We have run out of gifts to consider.")
                    run = False
                    break

            n = n + 1

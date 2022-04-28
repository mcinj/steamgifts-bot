import json
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import log
from giveaway import Giveaway

logger = log.get_logger(__name__)


class SteamGifts:
    def __init__(self, cookie, gifts_type, pinned, min_points, max_entries,
                 max_time_left, minimum_game_points, blacklist):
        self.cookie = {
            'PHPSESSID': cookie
        }
        self.gifts_type = gifts_type
        self.pinned = pinned
        self.min_points = int(min_points)
        self.max_entries = int(max_entries)
        self.max_time_left = int(max_time_left)
        self.minimum_game_points = int(minimum_game_points)
        self.blacklist = blacklist.split(',')

        self.base = "https://www.steamgifts.com"
        self.session = requests.Session()

        self.filter_url = {
            'All': "search?page=%d",
            'Wishlist': "search?page=%d&type=wishlist",
            'Recommended': "search?page=%d&type=recommended",
            'Copies': "search?page=%d&copy_min=2",
            'DLC': "search?page=%d&dlc=true",
            'New': "search?page=%d&type=new"
        }

    def requests_retry_session(
        self,
        retries=5,
        backoff_factor=0.3
    ):
        session = self.session or requests.Session()
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

    def get_soup_from_page(self, url):
        r = self.requests_retry_session().get(url)
        r = requests.get(url, cookies=self.cookie)
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def update_info(self):
        soup = self.get_soup_from_page(self.base)

        try:
            self.xsrf_token = soup.find('input', {'name': 'xsrf_token'})['value']
            self.points = int(soup.find('span', {'class': 'nav__points'}).text)  # storage points
        except TypeError:
            logger.error("⛔  Cookie is not valid.")
            sleep(10)
            exit()

    def should_we_enter_giveaway(self, giveaway):
        if giveaway.time_remaining_in_minutes is None:
            return False
        if giveaway.time_created_in_minutes is None:
            return False
        txt = f"{giveaway.game_name} - {giveaway.game_cost}P - {giveaway.game_entries} entries (w/ {giveaway.copies} " \
              f"copies) - Created {giveaway.time_created_string} ago with {giveaway.time_remaining_string} remaining."
        logger.debug(txt)

        if self.blacklist is not None and self.blacklist != ['']:
            for keyword in self.blacklist:
                if giveaway.game_name.lower().find(keyword.lower()) != -1:
                    txt = f"Game {giveaway.game_name} contains the blacklisted keyword {keyword}"
                    logger.debug(txt)
                    return False
        if self.points - int(giveaway.game_cost) < 0:
            txt = f"⛔ Not enough points to enter: {giveaway.game_name}"
            logger.debug(txt)
            return False
        if giveaway.game_cost < self.minimum_game_points:
            txt = f"Game {giveaway.game_name} costs {giveaway.game_cost}P and is below your cutoff of " \
                  f"{self.minimum_game_points}P."
            logger.debug(txt)
            return False
        if giveaway.time_remaining_in_minutes > self.max_time_left:
            txt = f"Game {giveaway.game_name} has {giveaway.time_remaining_in_minutes} minutes left and is " \
                  f"above your cutoff of {self.max_time_left} minutes."
            logger.debug(txt)
            return False
        if giveaway.game_entries / giveaway.copies > self.max_entries:
            txt = f"Game {giveaway.game_name} has {giveaway.game_entries} entries and is above your cutoff " \
                  f"of {self.max_entries} entries."
            logger.debug(txt)
            return False

        return True

    def enter_giveaway(self, game_id):
        payload = {'xsrf_token': self.xsrf_token, 'do': 'entry_insert', 'code': game_id}
        entry = requests.post('https://www.steamgifts.com/ajax.php', data=payload, cookies=self.cookie)
        json_data = json.loads(entry.text)

        if json_data['type'] == 'success':
            return True

    def evaluate_giveaways(self, page=1):
        n = page
        run = True
        while run:
            txt = "⚙️  Retrieving games from %d page." % n
            logger.info(txt)

            filtered_url = self.filter_url[self.gifts_type] % n
            paginated_url = f"{self.base}/giveaways/{filtered_url}"

            soup = self.get_soup_from_page(paginated_url)

            # this matches on a div with the exact class value so we discard ones
            # that also have a class 'is-faded' containing already entered giveaways
            game_list = soup.select('div[class=giveaway__row-inner-wrap]')
            # game_list = soup.find_all('div', {'class': 'giveaway__row-inner-wrap'})

            if not len(game_list):
                txt = f"We have run out of gifts to consider."
                logger.info(txt)
                run = False
                break

            for item in game_list:
                giveaway = Giveaway(item)
                if giveaway.pinned and not self.pinned:
                    continue

                if self.points == 0 or self.points < self.min_points:
                    txt = f"🛋️  We have {self.points} points, but we need {self.min_points} to start."
                    logger.info(txt)
                    run = False
                    break

                if not giveaway.game_cost:
                    continue
                if_enter_giveaway = self.should_we_enter_giveaway(giveaway)
                # if we are on any filter type except New and we get to a giveaway that exceeds our
                # max time left amount, then we don't need to continue to look at giveaways as any
                # after this point will also exceed the max time left
                if self.gifts_type != "New" and not giveaway.pinned and \
                        giveaway.time_remaining_in_minutes > self.max_time_left:
                    run = False
                    break

                if if_enter_giveaway:
                    res = self.enter_giveaway(giveaway.game_id)
                    if res:
                        self.points -= int(giveaway.game_cost)
                        txt = f"🎉 One more game! Has just entered {giveaway.game_name}"
                        logger.info(txt)
                        sleep(randint(4, 15))
                else:
                    continue
        n = n + 1

    def start(self):
        self.update_info()

        if self.points >= self.min_points:
            txt = "🤖 You have %d points. Evaluating giveaways..." % self.points
            logger.info(txt)
        else:
            random_seconds = randint(900, 1400)
            txt = f"You have {self.points} points which is below your minimum point threshold of " \
                  f"{self.min_points} points. Sleeping for {random_seconds / 60} minutes."
            logger.info(txt)
            sleep(random_seconds)

        while True:
            self.evaluate_giveaways()
            random_seconds = randint(900, 1400)
            logger.info(f"Going to sleep for {random_seconds / 60 } minutes.")
            sleep(random_seconds)
            self.update_info()


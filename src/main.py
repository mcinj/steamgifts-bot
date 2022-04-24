import json
import re
from random import randint
from time import sleep

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import log

logger = log.get_logger(__name__)


class SteamGifts:
    def __init__(self, cookie, gifts_type, pinned, min_points, max_entries, max_time_left, minimum_game_points):
        self.cookie = {
            'PHPSESSID': cookie
        }
        self.gifts_type = gifts_type
        self.pinned = pinned
        self.min_points = int(min_points)
        self.max_entries = int(max_entries)
        self.max_time_left = int(max_time_left)
        self.minimum_game_points = int(minimum_game_points)

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

    # this isn't exact because 'a week' could mean 8 days or 'a day' could mean 27 hours
    def determine_time_in_minutes(self, string_time):
        if not string_time:
            logger.error(f"Could not determine time from string {string_time}")
            return None
        match = re.search('(?P<number>[0-9]+) (?P<time_unit>(hour|day|minute|second|week))', string_time)
        if match:
            number = int(match.group('number'))
            time_unit = match.group('time_unit')
            if time_unit == 'hour':
                return number * 60
            elif time_unit == 'day':
                return number * 24 * 60
            elif time_unit == 'minute':
                return number
            elif time_unit == 'second':
                return 1
            elif time_unit == 'week':
                return number * 7 * 24 * 60
            else:
                logger.error(f"Unknown time unit displayed in giveaway: {string_time}")
                return None
        else:
            return None

    def determine_cost_and_copies(self, item, game_name, game_id):
        item_headers = item.find_all('span', {'class': 'giveaway__heading__thin'})
        if len(item_headers) == 1:  # then no multiple copies
            game_cost = item_headers[0].getText().replace('(', '').replace(')', '').replace('P', '')
            if not re.search('^[0-9]+$', game_cost):
                txt = f"Unable to determine cost of {game_name} with id {game_id}. Cost string: {item_headers[0]}"
                logger.error(txt)
                return None, None
            game_cost = int(game_cost)
            return game_cost, 1
        elif len(item_headers) == 2:  # then multiple copies
            game_cost = item_headers[1].getText().replace('(', '').replace(')', '').replace('P', '')
            if not re.search('^[0-9]+$', game_cost):
                txt = f"Unable to determine cost of {game_name} with id {game_id}. Cost string: {item_headers[1].getText()}"
                logger.error(txt)
                return None, None
            game_cost = int(game_cost)

            match = re.search('(?P<copies>[0-9]+) Copies', item_headers[0].getText(), re.IGNORECASE)
            if match:
                num_copies_str = match.group('copies')
                num_copies = int(num_copies_str)
                return game_cost, num_copies
            else:
                txt = f"It appears there are multiple copies of {game_name} with id {game_id}, but we could not " \
                      f"determine that. Copy string: {item_headers[0].getText()}"
                logger.error(txt)
                return game_cost, None
        else:
            txt = f"Unable to determine cost or num copies of {game_name} with id {game_id}."
            logger.error(txt)
            return None, None

    def should_we_enter_giveaway(self, item, game_name, game_cost, copies):
        times = item.select('div span[data-timestamp]')
        game_remaining = times[0].text
        game_remaining_in_minutes = self.determine_time_in_minutes(game_remaining)
        if game_remaining_in_minutes is None:
            return False
        game_created = times[1].text
        game_created_in_minutes = self.determine_time_in_minutes(game_created)
        if game_created_in_minutes is None:
            return False
        game_entries = int(item.select('div.giveaway__links span')[0].text.split(' ')[0].replace(',', ''))

        txt = f"{game_name} - {game_cost}P - {game_entries} entries (w/ {copies} copies) - " \
              f"Created {game_created} ago with {game_remaining} remaining."
        logger.debug(txt)

        if self.points - int(game_cost) < 0:
            txt = f"⛔ Not enough points to enter: {game_name}"
            logger.debug(txt)
            return False
        if game_cost < self.minimum_game_points:
            txt = f"Game {game_name} costs {game_cost}P and is below your cutoff of {self.minimum_game_points}P."
            logger.debug(txt)
            return False
        if game_remaining_in_minutes > self.max_time_left:
            txt = f"Game {game_name} has {game_remaining_in_minutes} minutes left and is above your cutoff of {self.max_time_left} minutes."
            logger.debug(txt)
            return False
        if game_entries / copies > self.max_entries:
            txt = f"Game {game_name} has {game_entries} entries and is above your cutoff of {self.max_entries} entries."
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

            # this matches on a div with the exact class value so we discard ones that also have a class 'is-faded' containing already entered giveaways
            game_list = soup.select('div[class=giveaway__row-inner-wrap]')
            # game_list = soup.find_all('div', {'class': 'giveaway__row-inner-wrap'})

            if not len(game_list):
                txt = f"We have run out of gifts to consider."
                logger.info(txt)
                run = False
                break

            for item in game_list:
                if len(item.get('lass', [])) == 2 and not self.pinned:
                    continue

                if self.points == 0 or self.points < self.min_points:
                    txt = f"🛋️  We have {self.points} points, but we need {self.min_points} to start."
                    logger.info(txt)
                    run = False
                    break

                game_name = item.find('a', {'class': 'giveaway__heading__name'}).text
                game_id = item.find('a', {'class': 'giveaway__heading__name'})['href'].split('/')[2]

                game_cost, copies = self.determine_cost_and_copies(item, game_name, game_id)

                if not game_cost:
                    continue
                if_enter_giveaway = self.should_we_enter_giveaway(item, game_name, game_cost, copies)

                if if_enter_giveaway:
                    res = self.enter_giveaway(game_id)
                    if res:
                        self.points -= int(game_cost)
                        txt = f"🎉 One more game! Has just entered {game_name}"
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
            txt = f"You have {self.points} points which is below your minimum point threshold of {self.min_points} points. Sleeping for {random_seconds} seconds."
            logger.info(txt)
            sleep(random_seconds)

        while True:
            self.evaluate_giveaways()
            random_seconds = randint(900, 1400)
            logger.info(f"Going to sleep for {random_seconds} seconds.")
            sleep(random_seconds)


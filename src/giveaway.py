import re
import log
import time

logger = log.get_logger(__name__)


class Giveaway:

    def __init__(self, soup_item):
        self.soup_item = soup_item
        self.steam_app_id = None
        self.steam_url = None
        self.game_name = None
        self.giveaway_game_id = None
        self.giveaway_uri = None
        self.pinned = False
        self.cost = None
        self.game_entries = None
        self.user = None
        self.copies = None
        self.time_created_timestamp = None
        self.time_remaining_string = None
        self.time_remaining_in_minutes = None
        self.time_remaining_timestamp = None
        self.time_created_string = None
        self.time_created_in_minutes = None

        icons = soup_item.select('a.giveaway__icon')
        self.steam_url = icons[0]['href']
        self.steam_app_id = self.get_steam_app_id(self.steam_url)
        self.game_name = soup_item.find('a', {'class': 'giveaway__heading__name'}).text
        self.giveaway_game_id = soup_item.find('a', {'class': 'giveaway__heading__name'})['href'].split('/')[2]
        self.giveaway_uri = soup_item.select_one('a.giveaway__heading__name')['href']
        pin_class = soup_item.parent.parent.get("class")
        self.pinned = pin_class is not None and len(pin_class) > 0 and pin_class[0].find('pinned') != -1
        self.cost, self.copies = self.determine_cost_and_copies(self.soup_item, self.game_name, self.giveaway_game_id)
        self.game_entries = int(soup_item.select('div.giveaway__links span')[0].text.split(' ')[0].replace(',', ''))
        self.user = soup_item.select_one('a.giveaway__username').text
        times = soup_item.select('div span[data-timestamp]')
        self.time_remaining_timestamp = int(times[0]['data-timestamp'])
        self.time_remaining_string = times[0].text
        self.time_remaining_in_minutes = self.determine_time_in_minutes(times[0]['data-timestamp'])
        self.time_created_timestamp = int(times[1]['data-timestamp'])
        self.time_created_string = times[1].text
        self.time_created_in_minutes = self.determine_time_in_minutes(times[1]['data-timestamp'])

    def get_steam_app_id(self, steam_url):
        match = re.search('^.+/app/(?P<steam_app_id>[0-9]+)/', steam_url, re.IGNORECASE)
        if match:
            return match.group('steam_app_id')
        else:
            return None

    def determine_time_in_minutes(self, timestamp):
        if not timestamp or not re.search('^[0-9]+$', timestamp):
            logger.error(f"Could not determine time from string {timestamp}")
            return None
        now = time.localtime()
        giveaway_endtime = time.localtime(int(timestamp))
        return int(abs((time.mktime(giveaway_endtime) - time.mktime(now)) / 60))

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
                return game_cost, 1
        else:
            txt = f"Unable to determine cost or num copies of {game_name} with id {game_id}."
            logger.error(txt)
            return None, None

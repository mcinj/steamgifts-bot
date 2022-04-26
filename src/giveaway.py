import re
import log

logger = log.get_logger(__name__)


class Giveaway:

    def __init__(self, soup_item):
        self.soup_item = soup_item
        self.game_name = None
        self.game_id = None
        self.pinned = False
        self.game_cost = None
        self.game_entries = None
        self.copies = None
        self.time_remaining_string = None
        self.time_remaining_in_minutes = None
        self.time_created_string = None
        self.time_created_in_minutes = None

        self.game_name = soup_item.find('a', {'class': 'giveaway__heading__name'}).text
        self.game_id = soup_item.find('a', {'class': 'giveaway__heading__name'})['href'].split('/')[2]
        pin_class = soup_item.parent.parent.get("class")
        self.pinned = pin_class is not None and len(pin_class) > 0 and pin_class[0].find('pinned') != -1
        self.game_cost, self.copies = self.determine_cost_and_copies(self.soup_item, self.game_name, self.game_id)
        self.game_entries = int(soup_item.select('div.giveaway__links span')[0].text.split(' ')[0].replace(',', ''))
        times = soup_item.select('div span[data-timestamp]')
        self.time_remaining_string = times[0].text
        self.time_remaining_in_minutes = self.determine_time_in_minutes(self.time_remaining_string)
        self.time_created_string = times[1].text
        self.time_created_in_minutes = self.determine_time_in_minutes(self.time_created_string)

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
                return game_cost, 1
        else:
            txt = f"Unable to determine cost or num copies of {game_name} with id {game_id}."
            logger.error(txt)
            return None, None
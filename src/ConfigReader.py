from configparser import ConfigParser
from random import randint, randrange

import log

logger = log.get_logger(__name__)


class ConfigException(Exception):
    pass


def value_range(min, max):
    return [str(x) for x in [*range(min, max + 1)]]


def choose_user_agent():
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36'
    ]
    return user_agents[randrange(0, len(user_agents))]


class ConfigReader(ConfigParser):

    required_values = {
        'DEFAULT': {
            'enabled': ('true', 'false'),
            'minimum_points': '%s' % (value_range(0, 400)),
            'max_entries': '%s' % (value_range(0, 100000)),
            'max_time_left': '%s' % (value_range(0, 21600)),
            'minimum_game_points': '%s' % (value_range(0, 50))
        },
        'WISHLIST': {
            'wishlist.enabled': ('true', 'false'),
            'wishlist.minimum_points': '%s' % (value_range(0, 400)),
            'wishlist.max_entries': '%s' % (value_range(0, 100000)),
            'wishlist.max_time_left': '%s' % (value_range(0, 21600))
        },
        'NOTIFICATIONS': {
            'pushover.enabled': ('true', 'false'),
        },
        'WEB': {
            'web.enabled': ('true', 'false'),
            'web.port': '%s' % (value_range(1, 65535))
        }
    }
    default_values = {
        'DEFAULT':  {
            'cookie': '',
            'user_agent': f"{choose_user_agent()}",
            'enabled': 'true',
            'minimum_points': f"{randint(20, 50)}",
            'max_entries': f"{randint(1000, 2500)}",
            'max_time_left': f"{randint(180,500)}",
            'minimum_game_points': "0",
            'blacklist_keywords': 'hentai,adult'
        },
        'WISHLIST': {
            'wishlist.enabled': 'true',
            'wishlist.minimum_points': '1',
            'wishlist.max_entries': f"{randint(10000, 100000)}",
            'wishlist.max_time_left': f"{randint(180,500)}"
        },
        'NOTIFICATIONS': {
            'notification.prefix': '',
            'pushover.enabled': 'false',
            'pushover.token': '',
            'pushover.user_key': '',
        },
        'WEB': {
            'web.enabled': 'false',
            'web.port': '9647'
        }
    }
    deprecated_values = {
        'DEFAULT': {
            'pinned': 'false',
            'gift_types': 'All'
        }
    }

    def __init__(self, config_file):
        super(ConfigReader, self).__init__()
        self.read(config_file)
        modified = self.create_defaults()
        if modified:
            with open(config_file, 'w+') as file:
                self.write(file)
        self.find_deprecated()
        self.validate_config()

    def create_defaults(self):
        modified = False
        for section, keys in self.default_values.items():
            if section not in self:
                self.add_section(section)
                modified = True
            for key, value in keys.items():
                if key not in self[section]:
                    self.set(section, key, value)
                    modified = True
        return modified

    def find_deprecated(self):
        for section, keys in self.deprecated_values.items():
            for key, values in keys.items():
                if key in self[section]:
                    logger.warn(f"config.ini : Key '{key}' in {section} is no longer used. Please remove.")

    def validate_config(self):
        for section, keys in self.required_values.items():
            if section not in self:
                raise ConfigException(
                    'Missing section "%s" in the config file' % section)

            for key, values in keys.items():
                if key not in self[section] or self[section][key] == '':
                    raise ConfigException((
                                              'Missing value for "%s" under section "%s" in ' +
                                              'the config file') % (key, section))

                if values:
                    if self[section][key] not in values:
                        raise ConfigException((
                                                  'Invalid value for "%s" under section "%s" in ' +
                                                  'the config file') % (key, section))

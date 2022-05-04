from configparser import ConfigParser
from random import randint
import log

logger = log.get_logger(__name__)

class ConfigException(Exception):
    pass


class ConfigReader(ConfigParser):
    def value_range(min, max):
        return [str(x) for x in [*range(min, max + 1)]]

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
        }
    }
    default_values = {
        'DEFAULT':  {
            'cookie': '',
            'enabled': 'true',
            'minimum_points': f"{randint(20, 100)}",
            'max_entries': f"{randint(1000, 2500)}",
            'max_time_left': f"{randint(180,500)}",
            'minimum_game_points': '1',
            'blacklist_keywords': 'hentai,adult'
        },
        'WISHLIST': {
            'wishlist.enabled': 'true',
            'wishlist.minimum_points': f"{randint(20, 100)}",
            'wishlist.max_entries': f"{randint(10000, 100000)}",
            'wishlist.max_time_left': f"{randint(180,500)}"
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
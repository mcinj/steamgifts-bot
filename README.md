### About
The bot is specially designed for [SteamGifts.com](https://www.steamgifts.com/)

### Features
- Automatically enters giveaways.
- Undetectable.
- Сonfigurable
  - Can look at your steam wishlist games or the main page for games to enter
  - When evaluating a giveaway
    - `max_time_left` - if the time left on giveaway is > max time left, then don't enter it
    - `max_entries` - if the entries on a giveaway are > than max entries, then don't enter it
    - `minimum_points` - minimum number of points **in your account** needed before considering any giveaway
    - `minimum_game_points` - if steamgifts.com point cost (ex. 1P, 5P, etc) is below this, don't enter it
    - `blacklist_keywords` - if the giveaway name contains any of these words, don't enter it. this list can be blank.
  - Notifications
    - A pushover notifications can be sent to you when a win is detected.
  - Webserver - A simple, simple, simple webserver than can be enabled (disabled by default) to show the config and logs
    - `web.host` - the IP to listen on (ex. localhost, 0.0.0.0, 192.168.1.1, etc)
    - `web.port` - the port to listen on
    - `web.app_root` - the folder to serve up which can be used for reverse proxying this behind nginx/apache/etc
    - `web.ssl` - if the traffic will be encrypted (http or https) using a self-signed cert
    - `web.basic_auth` - simple basic auth settings can be enabled
- Sleeps to restock the points.
- Can run 24/7.


## Instructions
1. Sign in on SteamGifts.com by Steam. 
2. Find PHPSESSID cookie in your browser.
3. Rename `config/config.ini.example` to `config/config.ini`. 
4. Add your PHPSESSION cookie to `cookie` in `config/config.ini`
5. Modifying the other settings is optional as defaults are set.

### Run from sources

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python main.py
```

### Docker
#### Run it
```bash
# Run the container
# Set TZ based on your timezone: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
docker run --name steamgifts -e TZ=America/New_York -d -v /path/to/the/config/folder:/config mcinj/docker-steamgifts-bot:latest
```

#### Or build it yourself locally
```bash
# Build the image
docker build -t steamgifts:latest .
# Run the container
# Set TZ based on your timezone: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
docker run --name steamgifts -e TZ=America/New_York -d -v /path/to/the/config/folder:/config steamgifts:latest
```



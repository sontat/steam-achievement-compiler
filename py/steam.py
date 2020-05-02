import json
import os
import threading
from datetime import datetime, timezone
from xml.etree import ElementTree
from requests import get
from exceptions import ProfileNotFoundException

API_KEY = os.getenv("STEAM_API_KEY")
NOT_PUBLIC_ERROR = "Profile is not public"


def get_base_64_id(steam_id):
    if len(steam_id) == 17 and steam_id.isdigit():
        return steam_id
    uri = "https://steamcommunity.com/id/{0}/?xml=1".format(steam_id)
    id_element = ElementTree.fromstring(get(uri).content).find("steamID64")
    if id_element is None:
        raise ProfileNotFoundException
    return id_element.text


def format_row(num, row):
    date = datetime.fromtimestamp(row['unlocktime'], tz=timezone.utc).date()
    return "#{0}\t{1}\t{2}\t{3}\t{4}".format(num + 1, row['name'], row['description'], row['game_name'], date)


class SteamProxy(threading.Thread):
    def __init__(self, steam_id, interval):
        super().__init__()
        self.steam_id = get_base_64_id(steam_id)
        self.interval = interval
        self.done_games = 0
        self.total_games = 1
        self.is_done = False
        self.achievements = []
        self.exception = None

    def get_progress(self):
        return 100.0 * self.done_games / self.total_games

    def run(self):
        uri = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={0}&steamid={1}".format(
            API_KEY, self.steam_id)
        data = json.loads(get(uri).content)
        try:
            games = [game['appid'] for game in data['response']['games']]
        except KeyError:
            self.exception = ProfileNotFoundException()
            return
        self.total_games = len(games)

        master_achievements = []
        for game in games:
            uri = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?l=en&appid={0}&key={1}&steamid={2}".format(
                game, API_KEY, self.steam_id)
            data = json.loads(get(uri).content)
            if data and 'playerstats' in data and 'error' in data['playerstats'] \
                    and data['playerstats']['error'] == NOT_PUBLIC_ERROR:
                self.exception = ProfileNotFoundException()
                return
            if data and 'playerstats' in data and 'achievements' in data['playerstats'] \
                    and data['playerstats']['success']:
                game_name_dict = {"game_name": data['playerstats']['gameName']}
                master_achievements.extend({**x, **game_name_dict}
                                           for x in data['playerstats']['achievements'] if x['achieved'])
            self.done_games += 1

        master_achievements.sort(key=lambda x: x['unlocktime'])
        self.is_done = True
        self.achievements = "\n".join(format_row(num, a) for num, a in enumerate(master_achievements)
                                      if ((num + 1) % self.interval == 0
                                          or num == 0 or num == len(master_achievements) - 1))

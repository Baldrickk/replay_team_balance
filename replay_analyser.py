#!/usr/bin/python3
import sys
from utils import OverWriter as OW
from replay_parser import ReplayParser as RP
from api import API
from cache import PlayerCache as PC
from statistics import mean

import code


def names_ids_to_get(replays, cache):
    names_to_id = set()
    ids_to_stat = set()
    for battle in replays:
        standard = battle.get('std')
        extended = battle.get('ext')
        if extended:
            for player_id, player in extended[0].get('players').items():
                if not cache.cached_player(player.get('name')):
                    ids_to_stat.add(player_id)
        elif standard:
            for player in standard.get('vehicles').values():
                name = player.get('name')
                if not cache.cached_player(name):
                    names_to_id.add(name)
    return names_to_id, ids_to_stat


def cache_players(replays, cache, api):
    names_to_id, ids_to_stat = names_ids_to_get(replays, cache)
    query_pool = list()
    query_pool.append(api.ratings_from_ids(api.ids_from_names(names_to_id)))
    query_pool.append(api.ratings_from_ids(ids_to_stat))
    for player_set in query_pool:
        for player in player_set:
            cache.add_to_cache(player)


def team_average_ratings(replays, cache):
    """returns an array containing a dict of the average rating of the green and red teams"""
    team_ratings = []
    for battle in replays:
        teams = [[], []]
        std = battle.get('std')
        for player in std.get('vehicles').values():
            name = player.get('name')
            cached_player = cache.cached_player(name)
            if cached_player:
                rating = int(cached_player.get('global_rating'))
                team_num = player.get('team') - 1 # 1-indexed -> 0-indexed
                if name == std.get('playerName'):
                    # note player's team and eliminate them from the calculation
                    replay_team = team_num
                else:
                    teams[team_num].append(rating)
        team_ratings.append({'green': mean(teams[replay_team]),
                             'red': mean(teams[1 - replay_team])})
    return team_ratings


def temp():
    a_list = [[], []]
    value = int(5)
    a_list[1].append(value)
    print(a_list)


def main():
    if not len(sys.argv) == 3:
        print('Usage = replay_analyser.py replay_path application_id')
        exit()
    with OW(sys.stderr) as ow, PC('cache.csv') as cache:
        rp = RP(sys.argv[1], ow)
        a = API(sys.argv[2], ow)
        replays = rp.read_replays()
        cache_players(replays, cache, a)
        team_ratings = team_average_ratings(replays, cache)

        # code.interact(local=locals())



if __name__ == "__main__":
    main()

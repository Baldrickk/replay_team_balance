#!/usr/bin/python3
import sys
from utils import OverWriter as OW
from replay_parser import ReplayParser as RP
from api import API
from cache import PlayerCache as PC


def names_ids_to_get(replays, cache):
    names_to_id = set()
    ids_to_stat = set()
    for battle in replays:
        for vehicle, details in battle[0].get('vehicles').items():
            name = details.get('name')
            player_data = cache.cached_player(name)
            if player_data:
                continue
            if len(battle) == 1:
                names_to_id.add(name)
            else:
                player_id = battle[1].get('vehicles').get(vehicle)[0].get('accountDBID')
                ids_to_stat.add(player_id)
    return names_to_id, ids_to_stat


def cache_players(replays, cache, api):
    names_to_id, ids_to_stat = names_ids_to_get(replays, cache)
    query_pool = list()
    query_pool.append(api.ratings_from_ids(api.ids_from_names(names_to_id)))
    query_pool.append(api.ratings_from_ids(ids_to_stat))
    for player_set in query_pool:
        for player in player_set:
            cache.add_to_cache(player)


def main():
    if not len(sys.argv) == 3:
        print('Usage = replay_analyser.py replay_path application_id')
        exit()
    with OW() as ow, PC('cache.csv') as cache:
        rp = RP('./testreplays/', ow)
        a = API('f9f772382b14bf0bad8b14d2d5dfd852', ow)
        replays = rp.read_replays()
        cache_players(replays, cache, a)


if __name__ == "__main__":
    main()

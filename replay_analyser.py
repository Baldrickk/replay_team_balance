#!/usr/bin/python3
from utils import OverWriter as OW
from replay_parser import ReplayParser as RP
from api import API
from cache import PlayerCache as PC
from statistics import mean, pstdev
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import sys


def names_ids_to_get(replays, cache):
    names_to_id = set()
    ids_to_stat = set()
    for battle in replays:
        standard = battle.get('std')
        extended = battle.get('ext')
        if extended and extended[0].get('players'):
            for player_id, player in extended[0].get('players').items():
                if not cache.cached_record(player.get('name')):
                    ids_to_stat.add(player_id)
        elif standard:
            for player in standard.get('vehicles').values():
                name = player.get('name')
                if not cache.cached_record(name):
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
    # add blank records for non-existent players to prevent searching for them again
    for name in names_to_id:
        if not cache.cached_record(name):
            cache.add_to_cache({'nickname': name, 'id': None, 'global_rating': None})


def team_average_ratings(replays, cache):
    team_ratings = []
    for battle in replays:
        teams = [[], []]
        std = battle.get('std')
        for player in std.get('vehicles').values():
            name = player.get('name')
            cached_player = cache.cached_record(name)
            if cached_player and cached_player.get('global_rating'):
                rating = float(cached_player.get('global_rating'))
                team_num = player.get('team') - 1  # 1-indexed -> 0-indexed
                if name == std.get('playerName'):
                    # note player's team and eliminate them from the calculation
                    replay_team = team_num
                else:
                    teams[team_num].append(rating)
        team_ratings.append({'green team': mean(teams[replay_team]),
                             'red team': mean(teams[1 - replay_team])})
    return team_ratings


def result(replay):
    extended = replay.get('ext')
    if extended:
        for key, val in extended[0].get('personal').items():
            if not key == 'avatar':
                player_team = val.get('team')
                winner = extended[0].get('common').get('winnerTeam')
                if winner == 0:
                    return 'draw'
                return 'win' if player_team == winner else 'loss'
    return 'unknown'


def output_xy(replays, team_ratings):
    plt.plot([0, 8000], [0, 8000], 'blue')
    # create array xs, ys, colours
    colours = {'win': 'green',
               'loss': 'red',
               'draw': 'orange',
               'unknown': 'grey'}

    plt.scatter([x.get('red team') for x in team_ratings],
                [y.get('green team') for y in team_ratings],
                color=[colours.get(result(replay)) for replay in replays],
                marker='.', s=1,
                label='green / red')
    plt.xlabel('rating: red team')
    plt.ylabel('rating: green team')
    plt.title("Average team rating distribution")
    plt.show()


def percent_diff(a, b):
    return 100*(float(a)-float(b))/float(a)


def output_rating_histogram(team_ratings):
    p_diffs = [percent_diff(b.get('green team'), b.get('red team')) for b in team_ratings]
    output_histogram(p_diffs, -100, 100, 3,
                     'percentage difference',
                     'frequency',
                     'Histogram of team rating differences')


def output_histogram(data, min, max, bin_size, xlabel, ylabel, title):
    sigma = pstdev(data)
    mu = mean(data)
    plt.hist(data, range(min, max+1, bin_size), rwidth=0.9, normed=True)
    plt.plot(range(min, max+1), mlab.normpdf(np.array(range(min, max+1)), mu, sigma), '--')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()


def output_score_histogram(replays):
    results = []
    for battle in replays:
        team_score = [0, 0]
        extended = battle.get('ext')
        if not extended:
            continue
        for tank in extended[0].get('vehicles').values():
            tank = tank[0]
            alive = tank.get('health') > 0
            if alive:
                team = tank.get('team') - 1
                team_score[team] += 1
        results.append(abs(team_score[1]-team_score[0]))
    output_histogram(results, 0, 15, 1, 'difference in score', 'count', 'Distribution of results')


def team_averages(team_ratings):
    g = mean(t.get('green team') for t in team_ratings)
    r = mean(t.get('red team') for t in team_ratings)
    print(f'Total replays:\n\t\t\t{len(team_ratings)}\n'
          f'Green team average rating:\n\t\t\t{g:.6}\n'
          f'Red team average rating:\n\t\t\t{r:.6}\n'
          f'Percentage difference:\n\t\t\t{percent_diff(g, r):+.3}%')


def outputs(replays, team_ratings):
    if not replays:
        return
    team_averages(team_ratings)
    output_xy(replays, team_ratings)
    output_rating_histogram(team_ratings)
    output_score_histogram(replays)


def main():
    if len(sys.argv) < 2:
        print('Usage = replay_analyser.py replay_path [application_id]')
        exit()
    replay_dir = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) >= 3 else '48cef51dca87be6a244bd55566907d56'
    with OW(sys.stderr) as ow, PC('cache.csv', ['nickname', 'id', 'global_rating']) as cache:
        rp = RP(replay_dir, ow)
        a = API(api_key, ow)
        replays = rp.read_replays()
        cache_players(replays, cache, a)
        team_ratings = team_average_ratings(replays, cache)
    outputs(replays, team_ratings)


if __name__ == "__main__":
    main()

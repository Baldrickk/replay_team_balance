#!/usr/bin/python3
from utils import OverWriter as Ow
from replay_parser import ReplayParser as Rp
from api import API
from cache import PlayerCache as Pc
from statistics import mean, pstdev
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import sys
import argparse

# import code

"""global variables"""
args = None


def parse_input_args():
    global args
    parser = argparse.ArgumentParser(description='A tool to analyse replays.')
    parser.add_argument('dirs', metavar='dir', type=str, nargs='+',
                        help='path to directory(s) containing replays')
    parser.add_argument('-w', '--weighted', dest="weighted", action='store_true',
                        help='Weight player ratings by position on team')
    """parser.add_argument('--output', metavar='OUTPUT', type=str,
                        help="specify a particular output. Default is to output all\n"
                             "options are: 'all', 'rating_scatter', 'rating_histogram', 'result_histogram'")"""
    parser.add_argument('-k', '--key', type=str,
                        default='48cef51dca87be6a244bd55566907d56',
                        help="application id (key) from https://developers.wargaming.net/applications/ (optional)")
    args = parser.parse_args()


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


def weighted_team_rating(teams, replay_team):
    top_tier = max(tier for team in teams for rating, tier in team)
    weights = [1., 1./2, 1./3]
    return {'green team': mean(rating * weights[top_tier - tier] for rating, tier in teams[replay_team]),
            'red team': mean(rating * weights[top_tier - tier] for rating, tier in teams[1 - replay_team])}


def team_rating(teams, replay_team):
    return ({'green team': mean(rating for rating, tier in teams[replay_team]),
             'red team': mean(rating for rating, tier in teams[1 - replay_team])})


def tank_tier(vehicle_type, tank_info):
    if not tank_info:
        return None
    tank_name = vehicle_type.split(':', 1)[1]
    tier = tank_info.get(tank_name, {}).get('tier')
    if not tier:
        print(f'Missing tank info: {tank_name}')
    return tier


def team_average_ratings(replays, cache, tank_info=None):
    global args
    team_ratings = []
    replay_team = None
    for battle in replays:
        teams = [[], []]
        std = battle.get('std')
        for player in std.get('vehicles').values():
            name = player.get('name')
            tier = tank_tier(player.get('vehicleType'), tank_info)
            cached_player = cache.cached_record(name)
            if cached_player and cached_player.get('global_rating'):
                rating = float(cached_player.get('global_rating'))
                team_num = player.get('team') - 1  # 1-indexed -> 0-indexed
                if name == std.get('playerName'):
                    # note player's team and eliminate them from the calculation
                    replay_team = team_num
                else:
                    teams[team_num].append((rating, tier))

        func = weighted_team_rating if tank_info and args.weighted else team_rating
        team_ratings.append(func(teams, replay_team))
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


def output_team_ratings(team_ratings):
    data = [r for team_r in team_ratings for r in team_r.values()]
    output_histogram(data, int(min(data)), int(max(data)), 100,
                     'team average rating',
                     'frequency',
                     'All teams rating distribution')


def output_histogram(data, minval, maxval, bin_size, xlabel='', ylabel='', title=''):
    maxval += 1
    sigma = pstdev(data)
    mu = mean(data)
    print(f'{title}: μ={mu:.6} σ={sigma:.6}')
    plt.hist(data,
             range(minval, maxval, bin_size),
             rwidth=0.9,
             normed=True)
    plt.plot(range(minval, maxval),
             mlab.normpdf(np.array(range(minval, maxval)), mu, sigma),
             '--')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.show()


def output_pc_diff_per_battle(team_ratings):
    ys = [0.]
    for i, battle in enumerate(team_ratings):
        ys.append((percent_diff(battle.get('green team'), battle.get('red team')) + ys[-1])/(i+1))
    plt.plot(range(len(ys)), ys)
    plt.xlabel('battle count')
    plt.ylabel('cumulative % difference per battle')
    plt.title('Percentage difference over time')
    plt.grid()
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


def output_player_ratings(cache):
    all_player_ratings = [int(player.get('global_rating')) for player in cache.data.values() if
                          player.get('global_rating') and
                          int(player.get('global_rating')) > 100]
    output_histogram(all_player_ratings,
                     int(min(all_player_ratings)),
                     int(max(all_player_ratings)),
                     100,
                     'player rating',
                     'frequency',
                     'Histogram of all players > 100 rating')


def outputs(replays, team_ratings, cache):
    if not replays:
        return
    team_averages(team_ratings)
    output_xy(replays, team_ratings)
    output_rating_histogram(team_ratings)
    output_score_histogram(replays)
    output_pc_diff_per_battle(team_ratings)
    output_team_ratings(team_ratings)
    output_player_ratings(cache)


def main():
    global args
    parse_input_args()
    with Ow(sys.stderr) as ow, Pc('cache.csv', ['nickname', 'id', 'global_rating']) as cache:
        rp = Rp(args.dirs, ow)
        a = API(args.key, ow)
        replays = rp.read_replays()
        cache_players(replays, cache, a)
        tank_info = a.tank_tiers() if args.weighted else None
        team_ratings = team_average_ratings(replays, cache, tank_info)
        outputs(replays, team_ratings, cache)


if __name__ == "__main__":
    main()

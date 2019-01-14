#!/usr/bin/python3
from utils import OverWriter as Ow
from replay_parser import ReplayParser as Rp
from collections import Counter
from api import API
from cache import PlayerCache as Pc
from statistics import mean, pstdev
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import sys
import argparse
import csv

# import code

"""global variables"""
args = None
logfile = None


def parse_input_args():
    global args
    parser = argparse.ArgumentParser(description='A tool to analyse replays.')
    parser.add_argument('dirs', metavar='dir', type=str, nargs='+',
                        help='path to directory(s) containing replays')
    """parser.add_argument('-w', '--weighted', dest="weighted", action='store_true',
                        help='Weight player ratings by position on team')"""
    """parser.add_argument('--output', metavar='OUTPUT', type=str,
                        help="specify a particular output. Default is to output all\n"
                             "options are: 'all', 'rating_scatter', 'rating_histogram', 'result_histogram'")"""
    parser.add_argument('-o', '--output_name', type=str, default='', metavar='PREFIX',
                        help='saved graph and csv files will be prefixed with PREFIX')
    parser.add_argument('-s', '--save_img', action='store_true',
                        help='enable automatic saving of graphs as images.')
    parser.add_argument('-c', '--csv', action='store_true',
                        help='enable saving of graph data as csv files')
    parser.add_argument('-d', '--dpi', type=int, default=300,
                        help='set the DPI value for automatically saved images.  This scales the image. Default = 1000')
    parser.add_argument('-g', '--graphs_off', action='store_true',
                        help='Disable display of graph windows')
    parser.add_argument('-k', '--key', type=str,
                        default='48cef51dca87be6a244bd55566907d56',
                        # default=None,
                        help="application id (key) from https://developers.wargaming.net/applications/ (optional)")
    parser.add_argument('-r', '--region', type=str, default='eu',
                        help='set server region.  defaults to "eu" and can be one of [eu, us, ru, asia]')
    parser.add_argument('-p', '--filter_platoons', action='store_true',
                        help='remove battles where player was platooned from the analysed replays')
    args = parser.parse_args()
    if args.key is None:
        print('Error: Application ID (key) required')
        exit()


def names_ids_to_get(replays, cache):
    names_to_id = set()
    ids_to_stat = set()
    for battle in replays:
        standard = battle.get('std')
        extended = battle.get('ext')
        # if we have extended data, we have the player_id
        if extended and extended[0].get('players'):
            for player_id, player in extended[0].get('players').items():
                if cache.cached_record(player.get('name')) is None:
                    ids_to_stat.add(player_id)
        # otherwise, we have to find out the player_id
        elif standard:
            for player in standard.get('vehicles').values():
                name = player.get('name')
                if cache.cached_record(name) is None:
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
    return ({'green team': mean(teams[replay_team]),
             'red team': mean(teams[1 - replay_team])})


def team_average_ratings(replays, cache):
    global args
    team_ratings = []
    replay_team = None
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

        team_ratings.append(team_rating(teams, replay_team))
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


def output_xy_ratings(replays, team_ratings):
    global args
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')
    
    xs = [x.get('red team') for x in team_ratings]
    ys = [y.get('green team') for y in team_ratings]
    max_num = max((max(xs), max(ys)))
    colours = [battle_colours(replay) for replay in replays]
    
    ax.plot([0, max_num], [0, max_num], 'blue')

    title = "Average team rating distribution"
    ax.scatter(xs, ys,
               color=colours,
               marker='.', s=1,
               label='green / red')
    ax.set_xlabel('rating: red team')
    ax.set_ylabel('rating: green team')
    ax.set_title(title)

    filename = '_'.join((args.output_name, title))

    if args.csv:
        if args.csv:
            with open(f'{filename}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(zip(xs, ys, colours))

    if args.save_img:
        plt.savefig(f'{filename}.png', bbox_inches='tight', dpi=args.dpi)

    plt.clf() if args.graphs_off else plt.show()


def percent_diff(a, b):
    return 100*(a-b)/float(mean((a, b)))
    # return 100*(float(a)-float(b))/float(a)


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
    global args
    maxval += 1
    sigma = pstdev(data)
    mu = mean(data)
    output = f'{title}: μ={mu:.6f} σ={sigma:.6f}'
    print(output)
    if logfile:
        logfile.write(output + '\n')
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

    filename = '_'.join((args.output_name, title))

    if args.csv:
        if args.csv:
            bins = {v:0 for v in range(0, int((maxval - minval) / bin_size) + 1)}
            for d in data:
                zeroed = d - minval
                i = int((zeroed - 1) / bin_size)
                bins[i] += 1


            with open(f'{filename}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(zip(range(minval, maxval, bin_size), bins.values()))

    if args.save_img:
        plt.savefig(f'{filename}.png', bbox_inches='tight', dpi=args.dpi)

    plt.clf() if args.graphs_off else plt.show()


def zero_index(one_indexed):
    return one_indexed - 1


def output_pc_diff_per_battle_avg(team_ratings):
    global args
    title = 'Average Percentage Difference over Time'
    ys = [0.]
    subsum = 0
    for i, battle in enumerate(team_ratings):
        pd = percent_diff(battle.get('green team'), battle.get('red team'))
        subsum += pd
        ys.append(subsum/(i+1))

    plt.plot(range(len(ys)), ys)
    plt.xlabel('Battle Count')
    plt.ylabel('Average % Difference')
    plt.title(title)
    plt.grid()

    filename = '_'.join((args.output_name, title))

    if args.csv:
        if args.csv:
            with open(f'{filename}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(zip(range(len(ys)), ys))

    if args.save_img:
        plt.savefig(f'{filename}.png', bbox_inches='tight', dpi=args.dpi)

    plt.clf() if args.graphs_off else plt.show()


def output_pc_diff_per_battle_abs(replays, team_ratings):
    global args
    title = 'Percentage Difference per Battle'

    ys = [percent_diff(battle.get('green team'), battle.get('red team')) for battle in team_ratings]
    xs = range(len(ys))

    colours = [battle_colours(replay) for replay in replays]
    plt.scatter(xs,
                ys,
                color=colours,
                marker='.', s=5,
                label='green / red')

    plt.xlabel('Battle')
    plt.ylabel('% Difference')
    plt.title(title)
    plt.grid()

    filename = '_'.join((args.output_name, title))

    if args.csv:
        if args.csv:
            with open(f'{filename}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(zip(xs, ys, colours))

    if args.save_img:
        plt.savefig(f'{filename}.png', bbox_inches='tight', dpi=args.dpi)

    plt.clf() if args.graphs_off else plt.show()


def battle_score(battle):
    team_score = [0, 0]
    extended = battle.get('ext', [None])[0]
    if extended is None:
        return None  # [0, 0], 0  really we need to ensure that this isn't referenced, but this will do for now #FIX_ME
    for tank in extended.get('vehicles').values():
        tank = tank[0]
        alive = tank.get('health') > 0
        if alive:
            team = zero_index(tank.get('team'))
            team_score[team] += 1
    player_team = zero_index(extended.get('personal').get('avatar').get('team'))
    return team_score, player_team


def output_score_histogram(replays):
    results = []
    for battle in replays:
        bs = battle_score(battle)
        if bs:
            team_score, player_team = bs
            results.append(abs(team_score[1]-team_score[0]))
    output_histogram(results, 0, 15, 1, 'difference in score', 'count', 'Distribution of results')


def team_averages(team_ratings):
    global logfile
    g = mean(t.get('green team') for t in team_ratings)
    r = mean(t.get('red team') for t in team_ratings)
    c = Counter((t.get('green team') > t.get('red team') for t in team_ratings))
    output = '\n'.join((f'Total replays:\n\t\t\t{len(team_ratings)}',
                        f'Green team average rating:\n\t\t\t{g:.6}',
                        f'Red team average rating:\n\t\t\t{r:.6}',
                        f'Percentage difference:\n\t\t\t{percent_diff(g, r):+.3}%',
                        f'Stronger than enemy:\n\t\t\t{c.get(True,0)} battles',
                        f'Weaker than enemy:\n\t\t\t{c.get(False)} battles',
                        f'Percentage Stronger:\n\t\t\t{((100*c.get(True,0.0)/len(team_ratings)) -50):+.3}%'))
    print(output)
    if logfile:
        logfile.write(output + '\n')


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
                     'Histogram of all players') # > 100 rating')


def battle_colours(replay, colours={'win': 'green',
                                    'loss': 'red',
                                    'draw': 'orange',
                                    'unknown': 'grey'}):
    return colours.get(result(replay))


def output_xy_rating_vs_score(replays, team_ratings):
    title = 'Scores per team rating difference'
    # plt.plot([-8000,8000],[-16, 16], 'blue')
    # xs = [percent_diff(x.get('green team'), x.get('red team')) for x in team_ratings]
    # bs = (battle_score(y) for y in replays)
    # ys = [score[player_team] - score[1-player_team] for score, player_team in bs if bs]

    xs = []
    ys = []
    for tr, r in zip(team_ratings, replays):
        xs.append(percent_diff(tr.get('green team'), tr.get('red team')))
        bs = battle_score(r)
        if bs:
            score, player_team = bs
            ys.append(score[player_team] - score[1-player_team])
        else:
            ys.append(0)

    colours = [battle_colours(replay) for replay in replays]

    plt.scatter(xs, ys,
                color=colours,
                marker='.', s=1,
                label='green / red')
    plt.xlabel('Rating: % difference')
    plt.ylabel('Team score')
    plt.title(title)

    filename = '_'.join((args.output_name, title))

    if args.csv:
        if args.csv:
            with open(f'{filename}.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(zip(xs, ys, colours))

    if args.save_img:
        plt.savefig(f'{filename}.png', bbox_inches='tight', dpi=args.dpi)

    plt.clf() if args.graphs_off else plt.show()


def outputs(replays, team_ratings, cache):
    if not replays:
        return
    print('')   # force a new line
    team_averages(team_ratings)
    output_xy_ratings(replays, team_ratings)
    output_rating_histogram(team_ratings)
    output_score_histogram(replays)
    output_xy_rating_vs_score(replays, team_ratings)
    output_pc_diff_per_battle_avg(team_ratings)
    output_pc_diff_per_battle_abs(replays, team_ratings)
    output_team_ratings(team_ratings)
    output_player_ratings(cache)


def main():
    global args, logfile
    parse_input_args()
    if args.save_img:
        logfile = open(f'{args.save_img}.log', 'w', encoding='utf8')
    with Ow(sys.stderr) as ow, Pc('cache.csv', ['nickname', 'id', 'global_rating']) as cache:
        rp = Rp(args.dirs, ow)
        a = API(args.key, ow, args.region)
        replays = rp.read_replays(args.filter_platoons)
        cache_players(replays, cache, a)
        team_ratings = team_average_ratings(replays, cache)
        outputs(replays, team_ratings, cache)
    if logfile:
        logfile.close()


if __name__ == "__main__":
    main()

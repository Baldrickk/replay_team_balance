#!/usr/bin/python3
"""TODO: Module Docstring"""
import sys
import argparse
import csv
from statistics import mean, pstdev
from collections import Counter
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np

from utils import OverWriter as Ow
from replay_parser import ReplayParser as Rp

from api import API
from cache import PlayerCache as Pc


# import code

# global variables
ARGS = None
LOGFILE = None


def parse_input_args():
    """TODO: Method Docstring"""
    global ARGS
    parser = argparse.ArgumentParser(
        description="A tool to analy_scoree replay_score.")
    parser.add_argument(
        "dirs",
        metavar="dir",
        type=str,
        nargs="+",
        help="path to directory(s) containing replay_score",
    )
    parser.add_argument(
        "-o",
        "--output_name",
        type=str,
        default="",
        metavar="PREFIX",
        help="saved graph and csv files will be prefixed with PREFIX",
    )
    parser.add_argument(
        "-s",
        "--save_img",
        action="store_true",
        help="enable automatic saving of graphs as images.",
    )
    parser.add_argument(
        "-c",
        "--csv",
        action="store_true",
        help="enable saving of graph data as csv files",
    )
    parser.add_argument(
        "-data_values",
        "--dpi",
        type=int,
        default=300,
        help="set the DPI value for automatically saved images.  This scales the image. Default = 1000",
    )
    parser.add_argument(
        "-g",
        "--graphs_off",
        action="store_true",
        help="Disable display of graph windows",
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        default="48cef51dca87be6a244bd55566907d56",
        # default=None,
        help="application id (key) from https://developers.wargaming.net/applications/ (optional)",
    )
    parser.add_argument(
        "-r",
        "--region",
        type=str,
        default="eu",
        help='set server region.  defaults to "eu" and can be one of [eu, us, ru, asia]',
    )
    parser.add_argument(
        "-p",
        "--filter_platoons",
        action="store_true",
        help="remove battles where player was platooned from the analy_scoreed replay_score",
    )
    ARGS = parser.parse_args()
    if ARGS.key is None:
        print("Error: Application ID (key) required")
        exit()


def names_ids_to_get(replay_score, cache):
    """TODO: Method Docstring"""
    names_to_id = set()
    ids_to_stat = set()
    for battle in replay_score:
        standard = battle.get("std")
        extended = battle.get("ext")
        # if we have extended data, we have the player_id
        if extended and extended[0].get("players"):
            for player_id, player in extended[0].get("players").items():
                if cache.cached_record(player.get("name")) is None:
                    ids_to_stat.add(player_id)
        # otherwise, we have to find out the player_id
        elif standard:
            for player in standard.get("vehicles").values():
                name = player.get("name")
                if cache.cached_record(name) is None:
                    names_to_id.add(name)
    return names_to_id, ids_to_stat


def cache_players(replay_score, cache, api):
    """TODO: Method Docstring"""
    names_to_id, ids_to_stat = names_ids_to_get(replay_score, cache)
    query_pool = list()
    query_pool.append(api.ratings_from_ids(api.ids_from_names(names_to_id)))
    query_pool.append(api.ratings_from_ids(ids_to_stat))
    for player_set in query_pool:
        for player in player_set:
            cache.add_to_cache(player)
    # add blank records for non-existent players to prevent searching for them again
    for name in names_to_id:
        if not cache.cached_record(name):
            cache.add_to_cache(
                {"nickname": name, "id": None, "global_rating": None})


def weighted_team_rating(teams, replay_team):
    """TODO: Method Docstring"""
    top_tier = max(tier for team in teams for rating, tier in team)
    weights = [1.0, 1.0 / 2, 1.0 / 3]
    return {
        "green team": mean(
            rating * weights[top_tier - tier] for rating, tier in teams[replay_team]
        ),
        "red team": mean(
            rating * weights[top_tier - tier] for rating, tier in teams[1 - replay_team]
        ),
    }


def team_rating(teams, replay_team):
    """TODO: Method Docstring"""
    return {
        "green team": mean(teams[replay_team]),
        "red team": mean(teams[1 - replay_team]),
    }


def team_average_ratings(replay_score, cache):
    """TODO: Method Docstring"""
    global ARGS
    team_ratings = []
    replay_team = None
    for battle in replay_score:
        teams = [[], []]
        std = battle.get("std")
        for player in std.get("vehicles").values():
            name = player.get("name")
            cached_player = cache.cached_record(name)
            if cached_player and cached_player.get("global_rating"):
                rating = float(cached_player.get("global_rating"))
                team_num = player.get("team") - 1  # 1-indexed -> 0-indexed
                if name == std.get("playerName"):
                    # note player's team and eliminate them from the calculation
                    replay_team = team_num
                else:
                    teams[team_num].append(rating)

        team_ratings.append(team_rating(teams, replay_team))
    return team_ratings


def result(replay):
    """TODO: Method Docstring"""
    extended = replay.get("ext")
    if extended:
        for key, val in extended[0].get("personal").items():
            if not key == "avatar":
                player_team = val.get("team")
                winner = extended[0].get("common").get("winnerTeam")
                if winner == 0:
                    return "draw"
                return "win" if player_team == winner else "loss"
    return "unknown"


def output_xy_ratings(replay_score, team_ratings):
    """TODO: Method Docstring"""
    global ARGS
    fig = plt.figure()
    axis_x = fig.add_subplot(111, aspect="equal")
    x_score = [x.get("red team") for x in team_ratings]
    y_score = [y.get("green team") for y in team_ratings]
    max_num = max((max(x_score), max(y_score)))
    colours = [battle_colours(replay) for replay in replay_score]
    axis_x.plot([0, max_num], [0, max_num], "blue")
    title = "Average team rating distribution"
    axis_x.scatter(x_score, y_score, color=colours, marker=".", s=1, label="green / red")
    axis_x.set_xlabel("rating: red team")
    axis_x.set_ylabel("rating: green team")
    axis_x.set_title(title)
    filename = "_".join((ARGS.output_name, title))
    if ARGS.csv:
        if ARGS.csv:
            with open(f"{filename}.csv", "w", newline="") as selected_file:
                writer = csv.writer(selected_file)
                writer.writerows(zip(x_score, y_score, colours))
    if ARGS.save_img:
        plt.savefig(f"{filename}.png", bbox_inches="tight", dpi=ARGS.dpi)
    if ARGS.graphs_off:
        plt.clf()
    else:
        plt.show()

def percent_diff(param_a, param_b):
    """TODO: Method Docstring"""
    return 100 * (param_a - param_b) / float(mean((param_a, param_b)))

def output_rating_histogram(team_ratings):
    """TODO: Method Docstring"""
    p_diffs = [
        percent_diff(param_b.get("green team"), param_b.get("red team")) for param_b in team_ratings
    ]
    output_histogram(
        p_diffs,
        -100,
        100,
        3,
        "percentage difference",
        "frequency",
        "Histogram of team rating differences",
    )


def output_team_ratings(team_ratings):
    """TODO: Method Docstring"""
    data = [rating for team_r in team_ratings for rating in team_r.values()]
    output_histogram(
        data,
        int(min(data)),
        int(max(data)),
        100,
        "team average rating",
        "frequency",
        "All teams rating distribution",
    )


def output_histogram(data, minval, maxval, bin_size, xlabel="", ylabel="", title=""):
    """TODO: Method Docstring"""
    global ARGS
    maxval += 1
    sigma = pstdev(data)
    average = mean(data)
    output = f"{title}: μ={average:.6f} σ={sigma:.6f}"
    print(output)
    if LOGFILE:
        LOGFILE.write(output + "\n")
    plt.hist(data, range(minval, maxval, bin_size), rwidth=0.9, density=True)
    plt.plot(
        range(minval, maxval),
        norm.pdf(np.array(range(minval, maxval)), average, sigma),
        "--",
    )
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)

    filename = "_".join((ARGS.output_name, title))

    if ARGS.csv:
        if ARGS.csv:
            bins = {v: 0 for v in range(
                0, int((maxval - minval + 1) / bin_size) + 1)}
            for data_values in data:
                zeroed = data_values - minval
                i = int(zeroed / bin_size)
                bins[i] += 1

            with open(f"{filename}.csv", "w", newline="") as selected_file:
                writer = csv.writer(selected_file)
                writer.writerows(
                    zip(range(minval, maxval, bin_size), bins.values()))

    if ARGS.save_img:
        plt.savefig(f"{filename}.png", bbox_inches="tight", dpi=ARGS.dpi)

    if ARGS.graphs_off:
        plt.clf()
    else:
        plt.show()


def zero_index(one_indexed):
    """TODO: Method Docstring"""
    return one_indexed - 1


def output_pc_diff_per_battle_avg(team_ratings):
    """TODO: Method Docstring"""
    global ARGS
    title = "Average Percentage Difference over Time"
    y_score = [0.0]
    subsum = 0
    for i, battle in enumerate(team_ratings):
        percentage_difference = percent_diff(battle.get("green team"), battle.get("red team"))
        subsum += percentage_difference
        y_score.append(subsum / (i + 1))

    plt.plot(range(len(y_score)), y_score)
    plt.xlabel("Battle Count")
    plt.ylabel("Average % Difference")
    plt.title(title)
    plt.grid()

    filename = "_".join((ARGS.output_name, title))

    if ARGS.csv:
        if ARGS.csv:
            with open(f"{filename}.csv", "w", newline="") as selected_file:
                writer = csv.writer(selected_file)
                writer.writerows(zip(range(len(y_score)), y_score))

    if ARGS.save_img:
        plt.savefig(f"{filename}.png", bbox_inches="tight", dpi=ARGS.dpi)

    if ARGS.graphs_off:
        plt.clf()
    else:
        plt.show()


def output_pc_diff_per_battle_abs(replay_score, team_ratings):
    """TODO: Method Docstring"""
    global ARGS
    title = "Percentage Difference per Battle"

    y_score = [
        percent_diff(battle.get("green team"), battle.get("red team"))
        for battle in team_ratings
    ]
    x_score = range(len(y_score))

    colours = [battle_colours(replay) for replay in replay_score]
    plt.scatter(x_score, y_score, color=colours,
                marker=".", s=5, label="green / red")

    plt.xlabel("Battle")
    plt.ylabel("% Difference")
    plt.title(title)
    plt.grid()

    filename = "_".join((ARGS.output_name, title))

    if ARGS.csv:
        if ARGS.csv:
            with open(f"{filename}.csv", "w", newline="") as selected_file:
                writer = csv.writer(selected_file)
                writer.writerows(zip(x_score, y_score, colours))

    if ARGS.save_img:
        plt.savefig(f"{filename}.png", bbox_inches="tight", dpi=ARGS.dpi)

    if ARGS.graphs_off:
        plt.clf()
    else:
        plt.show()


def battle_score(battle):
    """TODO: Method Docstring"""
    team_score = [0, 0]
    extended = battle.get("ext", [None])[0]
    if extended is None:
        # [0, 0], 0  really we need to ensure that this isn't referenced, but this will do for now #FIX_ME
        return None
    for tank in extended.get("vehicles").values():
        tank = tank[0]
        alive = tank.get("health") > 0
        if alive:
            team = zero_index(tank.get("team"))
            team_score[team] += 1
    player_team = zero_index(extended.get(
        "personal").get("avatar").get("team"))
    return team_score, player_team


def output_score_histogram(replay_score):
    """TODO: Method Docstring"""
    results = []
    for battle in replay_score:
        battle_score_var = battle_score(battle)
        if battle_score_var:
            team_score = battle_score_var
            results.append(abs(team_score[1] - team_score[0]))
    output_histogram(
        results, 0, 15, 1, "difference in score", "count", "Distribution of results"
    )


def team_averages(team_ratings):
    """TODO: Method Docstring"""
    global LOGFILE
    green_avg = mean(t.get("green team") for t in team_ratings)
    red_avg = mean(t.get("red team") for t in team_ratings)
    counter = Counter((t.get("green team") > t.get("red team") for t in team_ratings))
    output = "\n".join(
        (
            f"Total replay_score:\n\t\t\t{len(team_ratings)}",
            f"Green team average rating:\n\t\t\t{green_avg:.6}",
            f"Red team average rating:\n\t\t\t{red_avg:.6}",
            f"Percentage difference:\n\t\t\t{percent_diff(green_avg, red_avg):+.3}%",
            f"Stronger than enemy:\n\t\t\t{counter.get(True,0)} battles",
            f"Weaker than enemy:\n\t\t\t{counter.get(False)} battles",
            f"Percentage Stronger:\n\t\t\t{((100*counter.get(True,0.0)/len(team_ratings))):.3}%",
        )
    )
    print(output)
    if LOGFILE:
        LOGFILE.write(output + "\n")


def output_player_ratings(cache):
    """TODO: Method Docstring"""
    all_player_ratings = [
        int(player.get("global_rating"))
        for player in cache.data.values()
        if player.get("global_rating") and int(player.get("global_rating")) > 100
    ]
    output_histogram(
        all_player_ratings,
        int(min(all_player_ratings)),
        int(max(all_player_ratings)),
        100,
        "player rating",
        "frequency",
        "Histogram of all players",
    )  # > 100 rating')


def battle_colours(replay, colours=None):
    """TODO: Method Docstring"""
    if colours is None:
        colours = {"win": "green", "loss": "red", "draw": "orange", "unknown": "grey"}
    return colours.get(result(replay))

def output_xy_rating_vs_score(replay_score, team_ratings):
    """TODO: Method Docstring"""
    title = "Scores per team rating difference"
    # plt.plot([-8000,8000],[-16, 16], 'blue')
    # x_score = [percent_diff(x.get('green team'), x.get('red team')) for x in team_ratings]
    # battle_score = (battle_score(y) for y in replay_score)
    # y_score = [score[player_team] - score[1-player_team] for score, player_team in battle_score if battle_score]

    x_score = []
    y_score = []
    for team_rating_var, rating in zip(team_ratings, replay_score):
        x_score.append(percent_diff(team_rating_var.get("green team"), team_rating_var.get("red team")))
        battle_score_var = battle_score(rating)
        if battle_score_var:
            score, player_team = battle_score_var
            y_score.append(score[player_team] - score[1 - player_team])
        else:
            y_score.append(0)

    colours = [battle_colours(replay) for replay in replay_score]

    plt.scatter(x_score, y_score, color=colours,
                marker=".", s=1, label="green / red")
    plt.xlabel("Rating: % difference")
    plt.ylabel("Team score")
    plt.title(title)

    filename = "_".join((ARGS.output_name, title))

    if ARGS.csv:
        if ARGS.csv:
            with open(f"{filename}.csv", "w", newline="") as selected_file:
                writer = csv.writer(selected_file)
                writer.writerows(zip(x_score, y_score, colours))

    if ARGS.save_img:
        plt.savefig(f"{filename}.png", bbox_inches="tight", dpi=ARGS.dpi)

    if ARGS.graphs_off:
        plt.clf()
    else:
        plt.show()


def outputs(replay_score, team_ratings, cache):
    """TODO: Method Docstring"""
    if not replay_score:
        return
    print("")  # force param_a new line
    team_averages(team_ratings)
    output_xy_ratings(replay_score, team_ratings)
    output_rating_histogram(team_ratings)
    output_score_histogram(replay_score)
    output_xy_rating_vs_score(replay_score, team_ratings)
    output_pc_diff_per_battle_avg(team_ratings)
    output_pc_diff_per_battle_abs(replay_score, team_ratings)
    output_team_ratings(team_ratings)
    output_player_ratings(cache)


def main():
    """TODO: Method Docstring"""
    global ARGS, LOGFILE
    parse_input_args()
    if ARGS.save_img:
        LOGFILE = open(f"{ARGS.save_img}.log", "w", encoding="utf8")
    with Ow(sys.stderr) as over_writer, Pc("cache.csv", ["nickname", "id", "global_rating"]) as cache:
        replay_parser_instance = Rp(ARGS.dirs, over_writer)
        api_instance = API(ARGS.key, over_writer, ARGS.region)
        replay_score = replay_parser_instance.read_replays(
            ARGS.filter_platoons)
        cache_players(replay_score, cache, api_instance)
        team_ratings = team_average_ratings(replay_score, cache)
        outputs(replay_score, team_ratings, cache)
    if LOGFILE:
        LOGFILE.close()


if __name__ == "__main__":
    main()

#!/usr/bin/python3
"""TODO: Module Docstring"""
import sys
import argparse
from utils import OverWriter as Ow
from replay_parser import ReplayParser as Rp

ARGS = ""

def parse_input_args():
    """TODO: Method Docstring"""
    global ARGS
    parser = argparse.ArgumentParser(description="A tool to analyse replays.")
    parser.add_argument(
        "dirs",
        metavar="dir",
        type=str,
        nargs="+",
        help="path to directory(s) containing replays",
    )
    parser.add_argument(
        "-o",
        "--output_name",
        type=str,
        default="names.csv",
        metavar="PREFIX",
        help="file to save output to, defaults to names.csv",
    )

    ARGS = parser.parse_args()


def main():
    """TODO: Method Docstring"""
    global ARGS
    parse_input_args()
    with Ow(sys.stderr) as over_writer_var:
        replay_parser_var = Rp(ARGS.dirs, over_writer_var)
        replays = replay_parser_var.read_replays()
        player_var = {"ally": {}, "enemy": {}}

    print("sorting players")

    for battle in replays:
        replay_team = None
        teams = [[], []]
        std = battle.get("std")
        for player in std.get("vehicles").values():
            name = player.get("name")
            team_num = player.get("team") - 1  # 1-indexed -> 0-indexed
            if name == std.get("playerName"):
                # note player's team and don't store them
                replay_team = team_num
            else:
                teams[team_num].append(name)
        if replay_team:
            # friendly team
            for name in teams[replay_team]:
                allies = player_var.get("ally")
                allies[name] = allies.get(name, 0) + 1
            # enemy team
            for name in teams[1 - replay_team]:
                enemies = player_var.get("enemy")
                enemies[name] = enemies.get(name, 0) + 1

    with open(ARGS.output_name, "w") as outfile:
        outfile.write(",Name,count\n")
        outfile.write("Ally")
        for player, count in player_var.get("ally").items():
            outfile.write(f",{player},{count}\n")
        outfile.write("Enemy")
        for player, count in player_var.get("enemy").items():
            outfile.write(f",{player},{count}\n")


if __name__ == "__main__":
    main()

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
from collections import defaultdict
import csv

def parse_input_args():
    global args
    parser = argparse.ArgumentParser(description='A tool to analyse replays.')
    parser.add_argument('dirs', metavar='dir', type=str, nargs='+',
                        help='path to directory(s) containing replays')
    parser.add_argument('-o', '--output_name', type=str, default='names.csv', metavar='PREFIX',
                        help='file to save output to, defaults to names.csv')

    args = parser.parse_args()


def main():
    global args, logfile
    parse_input_args()
    with Ow(sys.stderr) as ow:
        rp = Rp(args.dirs, ow)
        replays = rp.read_replays()
        p = {'ally': {}, 'enemy': {}}

    print('sorting players')

    for battle in replays:
        replay_team = None
        teams = [[], []]
        std = battle.get('std')
        for player in std.get('vehicles').values():
            name = player.get('name')
            team_num = player.get('team') - 1  # 1-indexed -> 0-indexed
            if name == std.get('playerName'):
                # note player's team and don't store them
                replay_team = team_num
            else:
                teams[team_num].append(name)
        if replay_team:
            #friendly team
            for name in teams[replay_team]:
                allies = p.get('ally')
                allies[name] = allies.get(name, 0) + 1
            #enemy team
            for name in teams[1 - replay_team]:
                enemies = p.get('enemy')
                enemies[name] = enemies.get(name, 0) + 1

    with open(args.output_name, 'w') as outfile:
        outfile.write(',Name,count\n')
        outfile.write('Ally')
        for player, count in p.get('ally').items():
            outfile.write(f',{player},{count}\n')
        outfile.write('Enemy')
        for player, count in p.get('enemy').items():
            outfile.write(f',{player},{count}\n')

if __name__ == "__main__":
    main()

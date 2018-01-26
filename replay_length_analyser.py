#!/usr/bin/python3

import sys
from utils import OverWriter as Ow
from replay_parser import ReplayParser as Rp
from statistics import mean


def main():
    if not len(sys.argv) > 1:
        print('need a dir name')
        exit()

    with Ow(sys.stderr) as ow:
        rp = Rp(sys.argv[1:], ow)
        lengths = []
        replays = rp.read_replays()
        for replay in replays:
            length = replay.get('ext', [{}])[0].get('common', {}).get('duration')
            if length:
                lengths.append(length)
        average_length = mean(lengths)
        minutes = int(average_length / 60)
        seconds = str(int(average_length % 60)).rjust(2, '0')
        print(f'\n{len(lengths)} replays:')
        print(f'average duration: {minutes}:{seconds}')


if __name__ == "__main__":
    main()
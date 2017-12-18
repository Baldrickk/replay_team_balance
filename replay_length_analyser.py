#!/usr/bin/python3

import requests
import json
import os
import sys
import itertools

from replay_analyser import load_json_from_replay

def get_duration_from_replay(replay):
  std, extended = load_json_from_replay(replay)
  return std.get('common', {}).get('duration', None) if std else None

def main()
  if not len(sys.argv) > 1:
    print ('need a dir name')
    exit()

  dir = sys.argv[1].rstrip('/\\') + os.path.sep
  files = list(os.listdir(dir))
  total_length = 0
  count = 0
  max_str_len = 0
  for i, replay in enumerate(files):
    if 'wotreplay' not in replay:
      continue
    length = get_duration_from_replay(replay)
    if length: 
      total_length += length
      count += 1
  print (f'\n{count} replays:')
  average_length = total_length / count
  minutes = int(average_length / 60)
  seconds = str(int(average_length % 60)).rjust(2,'0')
  print (f'average duration: {minutes}:{seconds}')

if __name__ == "__main__":
    main()
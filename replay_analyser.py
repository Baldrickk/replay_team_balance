#!/usr/bin/python3

import requests
import json
import os
import sys
import itertools
import struct
import glob

#globals
cache_filename = 'cache.csv'
cache_handle = None
cache = {}

def get_player_id_data_by_name(name, application_id):
  url = f'https://api.worldoftanks.eu/wot/account/list/?application_id={application_id}&search={name}&type=exact'
  return json.loads(requests.get(url).text)

def get_player_id_by_name(name, application_id):
  json_data = get_player_id_data_by_name(name, application_id)
  if not json_data.get('status') == 'ok':
    return
  id = json_data.get('data')[0].get('account_id') if json_data.get('meta').get('count') == 1 else 0
  write_data_to_cache(name, id, 0)
  return id

def get_player_rating_data_by_id(id, application_id):
  id = str(id)
  url = f'https://api.worldoftanks.eu/wot/account/info/?application_id={application_id}&account_id={id}&fields=global_rating,nickname'
  return json.loads(requests.get(url).text)

def player_ratings_by_id_to_cache(id_list, application_id):
  if not id_list:
    return
  json_data = get_player_rating_data_by_id(id_list, application_id)
  if not (json_data.get('status') == 'ok' and json_data.get('meta').get('count') > 0):
    return
  data = json_data.get('data')
  for id, info in data.items():
    if not info:
      continue;
    id = str(id)
    rating = int(info.get('global_rating'))
    name = info.get('nickname')
    write_data_to_cache(name, id, rating)

def get_player_rating_by_name(name, application_id):
  if name not in cache:
    id = get_player_id_by_name(name)
    player_ratings_by_id_to_cache([str(id)], application_id)
  rating = cache.get(name).get('rating')
  return rating

def write_data_to_dict_cache(name, id, rating):
  cache[name] = {'name':name,'id':int(id),'rating':int(rating)}

def write_data_to_file_cache(name, id, rating):
  if cache_handle:
    cache_handle.write(','.join((name,str(id),str(rating)))+'\n')

# assume that this is only called when necessarry, and record
# existance has been checked to save redundant writes
def write_data_to_cache(name, id, rating, write_to_file=True):
  write_data_to_dict_cache(name, id, rating)
  if write_to_file:
    write_data_to_file_cache(name, id, rating)

def init_player_cache():
  global cache_handle
  if os.path.isfile(cache_filename):
    print('reading cache from file')
    with open(cache_filename) as f:
      cachelines = f.read().split('\n')
    for line in cachelines:
      if line:
        name, id, rating = line.split(',')
        write_data_to_cache(name, id, rating, False)
  #this is opened 'forever' and will need to be closed at the end.
  cache_handle = open(cache_filename, 'a')

def write_clean_cache():
  global cache_handle
  print('\nwriting clean cache')
  cache_handle = open(cache_filename, 'w')
  for player in cache.values():
    write_data_to_file_cache(player.get('name'), player.get('id'), player.get('rating'))
  cache_handle.close()

def grouper(iterable, n, fillvalue=None):
  "Collect data into fixed-length chunks or blocks"
  # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
  args = [iter(iterable)] * n
  return itertools.zip_longest(*args, fillvalue=fillvalue)

def average_rating(teamdict):
  total = 0
  total_count = 0
  for name, count in teamdict.items():
    rating = cache.get(name,{}).get('rating',0)
    if rating:
      total += rating * count
      total_count += count
  return total/total_count

def extract_json_data(fmt_str, file_r):
  if len(fmt_str) != 4:
    raise ValueError("bad binary string length")
  length = struct.unpack('<I', fmt_str)[0]
  json_str = file_r.read(length).decode('utf-8')
  try:
    data = json.loads(json_str)
  except:
    return None
  return data

def load_json_from_replay(replay):
  with open(replay, 'rb') as r:
    d = r.read(12)
    parts = d[4]
    std_data = extract_json_data(d[8:12], r)
    if not std_data:
      return None
    if parts == 1:
      extended_data = None
    else:
      d = r.read(4)
      extended_data = extract_json_data(d[0:4], r)[0]
  return std_data, extended_data

def cache_player_ids(ext_data):
  if ext_data:
    for id, player_data in ext_data.get('players',{}).items():
      name = player_data.get('name')
      if cache.get('name',{}).get('rating',None):
        player_ids_to_stat.add(id)

def sort_players_to_teams(json_data, player_names_to_stat, player_ids_to_stat):
  battleteams = [[],[]]
  myteam = None
 
  data, ext_data = json_data if json_data else (None, None)
  if data and len(data['vehicles']) == 30:
    #cache player IDs if known
    cache_player_ids(ext_data)
    #add players to teams
    for key, player in data['vehicles'].items():
      team = int(player.get('team')) - 1
      name = player.get('name')
      playerName = data.get('playerName')
      if name == playerName:
        myteam = team
      else:
        battleteams[team].append(name)
        if name not in cache:
          player_names_to_stat.add(name)
        elif not cache.get(name).get('rating'):
          player_ids_to_stat.add(cache.get(name).get('id'))
  return myteam, battleteams
        
def print_one_line(print_string, length = 0):
  if len(print_string) > length:
    length = len(print_string)
  print ('\r' + print_string.ljust(length), end = '')
  return length

def get_teams_from_replays(directory):
  player_names_to_stat = set()
  player_ids_to_stat = set()
  teams = {'mine':{},'theirs':{}}
  files = glob.glob(directory + os.path.sep + '20*.wotreplay')
  max_str_len = 0
  print('reading replays:')
  total_count = len(files)
  for i, replay in enumerate(files):
    if 'wotreplay' not in replay:
      continue
    replay_string = f'{i+1}/{total_count} - {replay.rsplit(os.path.sep,1)[1]}'
    max_str_len = print_one_line(replay_string, max_str_len)
    json_data = load_json_from_replay(replay)
    if not json_data:
      continue
    
    myteam, battleteams = sort_players_to_teams(json_data, player_names_to_stat, player_ids_to_stat)

    if myteam is not None:
      for player in battleteams[myteam]:
        teams.get('mine')[player] = teams.get('mine').get(player, 0) + 1
      for player in battleteams[1 - myteam]:
        teams.get('theirs')[player] = teams.get('theirs').get(player, 0) + 1
  return teams, player_names_to_stat, player_ids_to_stat

def get_player_ids(name_set, player_ids_to_stat, application_id):
  print('\nGetting player IDs:')
  max_str_len = 0
  total_count = len(name_set)
  for i, name in enumerate(name_set):
    name_string = f'{i+1}/{total_count} - {name}'
    max_str_len = print_one_line(name_string, max_str_len)
    player_ids_to_stat.add(get_player_id_by_name(name, application_id))

def get_player_ratings(id_set, application_id):
  print('\nGetting player stats:')
  id_groups = grouper(id_set, 100)
  for ids in id_groups:
    id_list = ','.join(str(id) for id in ids if id is not None)
  #  print(f'\r{id_list}'.ljust(1000), end = "")
    player_ratings_by_id_to_cache(id_list, application_id)

def cache_players_from_replays():
  init_player_cache()
  teams, player_names_to_stat, player_ids_to_stat = get_teams_from_replays(directory)
  get_player_ids(player_names_to_stat, player_ids_to_stat, application_id)
  get_player_ratings(player_ids_to_stat, application_id)
  cache_handle.close()
  write_clean_cache()

def main():
  if not len(sys.argv) > 1:
    print ('need a directory name')
    exit()
  elif not len(sys.argv) > 2:
    print('need an application_id')
    exit()
  directory = sys.argv[1].rstrip('/\\') + os.path.sep
  application_id = sys.argv[2]
  print(f'directory = {directory}\nappID = {application_id}')

  cache_players_from_replays()

  averages = (average_rating(teams.get('mine')),
              average_rating(teams.get('theirs')))
  print ("\nMy team's average rating:")
  print ('\t' + str(averages[0]))
  print ("The other team's average rating:")
  print ('\t' + str(averages[1]))

if __name__ == "__main__":
    main()

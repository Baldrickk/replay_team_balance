import replay_analyser as RA
import glob
import sys
import os

def round_to(x, nearest=1):
    return int(nearest * round(float(x)/nearest))

def get_teams_from_replays(directory):
  player_names_to_stat = set()
  player_ids_to_stat = set()
  teams = {'mine':[],'theirs':[]}
  files = glob.glob(directory + os.path.sep + '20*.wotreplay')
  max_str_len = 0
  print('reading replays:')
  total_count = len(files)
  for i, replay in enumerate(files):
    if 'wotreplay' not in replay:
      continue
    replay_string = f'{i+1}/{total_count} - {replay.rsplit(os.path.sep,1)[1]}'
    max_str_len = RA.print_one_line(replay_string, max_str_len)
    json_data = RA.load_json_from_replay(replay)
    
    myteam, battleteams = RA.sort_players_to_teams(json_data, player_names_to_stat, player_ids_to_stat)
    
    if myteam is not None:
      teams.get('mine').append(battleteams[myteam])
      teams.get('theirs').append(battleteams[1 - myteam])
  return teams, player_names_to_stat, player_ids_to_stat

def main():
  if not len(sys.argv) > 1:
    print ('need a directory name')
    exit()
  elif not len(sys.argv) > 2:
    print('need an application_id')
    exit()
  elif not len(sys.argv) > 3:
    print('need an output filename')
    exit()
  directory = sys.argv[1].rstrip('/\\') + os.path.sep
  application_id = sys.argv[2]
  print(f'directory = {directory}\nappID = {application_id}')

  RA.init_player_cache()
  teams, player_names_to_stat, player_ids_to_stat = get_teams_from_replays(directory)
  RA.get_player_ids(player_names_to_stat, player_ids_to_stat, application_id)
  RA.get_player_ratings(player_ids_to_stat, application_id)
  RA.cache_handle.close()
  RA.write_clean_cache()

  with open(sys.argv[3].rsplit(',',1)[0] + '.csv', 'w') as outfile:
    buckets = {}
    for teamlists in zip(teams.get('mine'), teams.get('theirs')):
      total_mine = float(0)
      total_theirs = float(0)
      count_mine = 0
      count_theirs = 0
      for player in teamlists[0]:
        if player in RA.cache:
          total_mine += RA.cache.get(player).get('rating')
          count_mine += 1
      for player in teamlists[1]:
        if player in RA.cache:
          total_theirs += RA.cache.get(player).get('rating')
          count_theirs +=1 
      average_mine = total_mine / count_mine
      average_theirs = total_theirs / count_theirs
      outfile.write(f'{average_mine},{average_theirs}\n')
      pc_difference = ((average_theirs - average_mine) / average_mine) * 100
      bucket = round_to(pc_difference, 5)
      buckets[bucket] = buckets.get(bucket, 0) + 1
  with open(sys.argv[3].rsplit('.',1)[0] + '.buckets.csv', 'w') as outfile:
    for bucket, count in sorted(buckets.items()):
      outfile.write(f'{bucket},{count}\n')
  print ('done')

main()

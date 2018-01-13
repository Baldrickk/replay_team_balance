import replay_analyser as RA
import glob
import sys
import os


def round_to(x, nearest=1):
    return int(nearest * round(float(x) / nearest))


def get_teams_from_replays(directory):
    player_names_to_stat = set()
    player_ids_to_stat = set()
    teams = {'mine': [], 'theirs': []}
    files = glob.glob(directory + os.path.sep + '20*.wotreplay')
    max_str_len = 0
    print('reading replays:')
    total_count = len(files)
    for i, replay in enumerate(files):
        replay_string = f'{i+1}/{total_count} - {replay.rsplit(os.path.sep,1)[1]}'
        max_str_len = RA.print_one_line(replay_string, max_str_len)
        json_data = RA.load_json_from_replay(replay)

        myteam, battleteams = RA.sort_players_to_teams(json_data, player_names_to_stat, player_ids_to_stat)

        if myteam is not None:
            teams.get('mine').append(battleteams[myteam])
            teams.get('theirs').append(battleteams[1 - myteam])
    return teams, player_names_to_stat, player_ids_to_stat


def team_average(teamlist):
    total, count = 0, 0
    for player in teamlist:
        rating = RA.cache.get(player).get('rating', None)
        if rating:
            total += rating
            count += 1
    return total / count if total and count else None


def init():
    if not len(sys.argv) > 1:
        print('need a directory name')
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
    return directory, application_id


def main():
    directory, application_id = init()

    RA.init_player_cache()
    teams, player_names_to_stat, player_ids_to_stat = get_teams_from_replays(directory)
    RA.get_player_ids(player_names_to_stat, player_ids_to_stat, application_id)
    RA.get_player_ratings(player_ids_to_stat, application_id)
    RA.cache_handle.close()
    RA.write_clean_cache()

    with open(sys.argv[3].rsplit(',', 1)[0] + '.csv', 'w') as outfile:
        buckets = {}
        print(f'teamcount = {len(teams.get("mine"))}')
        for teamlists in zip(teams.get('mine'), teams.get('theirs')):
            average_mine = team_average(teamlists[0])
            average_theirs = team_average(teamlists[1])
            if average_mine and average_theirs:
                outfile.write(f'{average_mine},{average_theirs}\n')
                pc_difference = ((average_mine - average_theirs) / average_mine) * 100
                bucket = round_to(pc_difference, 5)
                buckets[bucket] = buckets.get(bucket, 0) + 1
    with open(sys.argv[3].rsplit('.', 1)[0] + '.buckets.csv', 'w') as outfile:
        for bucket, count in sorted(buckets.items()):
            outfile.write(f'{bucket},{count}\n')
    print('done')


main()

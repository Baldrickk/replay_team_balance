import json
import os
import struct
import glob


class ReplayParser:
    def __init__(self, paths, over_writer):
        self.paths = paths
        self.ow = over_writer
        self.replays = []

    @staticmethod
    def _extract_json_data(bin_str, file_r):
        if len(bin_str) != 4:
            raise ValueError("bad binary string length")
        length = struct.unpack('<I', bin_str)[0]
        json_str = file_r.read(length).decode('utf-8')
        data = json.loads(json_str)
        return data

    '''
    provide a True value if we can show that the player was not
    in a platoon for the battle in question
    otherwise, return False
    '''
    @staticmethod
    def _toon_filter_good(replay_data):
        if replay_data['ext']:
            player_id = replay_data['std'].get('playerID', {})
            player_data = replay_data['ext'][0].get('players',{}).get(str(player_id), {})
            pre_battle_id = player_data.get('prebattleID', 0)
            if pre_battle_id == 0:
                return True
        return False

    def _load_json_from_replay(self, replay, filter_platoons=False):
        with open(replay, 'rb') as r:
            try:
                data = dict()
                d = r.read(12)
                # the first byte in a valid replay is always 0x12
                if not d[0] == 0x12:
                    return None
                parts = d[4]
                json_data = self._extract_json_data(d[8:12], r)
                if json_data:
                    data['std'] = json_data
                else:
                    return None
                # Some replay types are bugged or don't work.
                # Forcibly ignore them here
                if (len(json_data.get('vehicles')) < 30 or               # not full team
                        json_data.get('regionCode') == 'CT' or           # test server
                        json_data.get('bootcampCtx') or                  # tutorial
                        json_data.get('gameplayID') == 'sandbox' or      # proving grounds
                        json_data.get('mapName') == '120_kharkiv_halloween'):       # Halloween 2017
                    return None

                if parts == 2:
                    d = r.read(4)
                    data['ext'] = self._extract_json_data(d[0:4], r)

                # To detect platoons, we need both parts,
                # So check if the second part exists.
                # If replay is incomplete or we are in a 'toon'
                # don't provide data
                if filter_platoons and not self._toon_filter_good(data):
                    return None

                return data
            except:
                return None

    def read_replays(self, filter_platoons=False):
        for replay_path in self.paths:
            if os.path.isfile(replay_path) and replay_path.endswith('ppr'):
                with open(replay_path) as rp:
                    file_replays = json.load(rp)
                    self.replays.extend(file_replays)
                    print(f'loaded {len(file_replays)} replays from file')
            elif os.path.isdir(replay_path):
                files = glob.glob(replay_path + os.path.sep + '*wotreplay')
                for i, replay in enumerate(files):
                    if replay.rsplit(os.path.sep, 1)[-1] in ('replay_last_battle.wotreplay', 'temp.wotreplay'):
                        continue
                    self.ow.print(f'{i+1}/{len(files)} - {replay}')
                    json_data = self._load_json_from_replay(replay, filter_platoons)
                    if json_data:
                        self.replays.append(json_data)
        return self.replays

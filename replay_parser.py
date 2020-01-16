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
    def _toon_filter_id(replay_data):
        std = replay_data.get('std')
        ext = replay_data.get('ext')
        if ext:
            player_id = str(std.get('playerID', {}))
            player_data = ext[0].get('players',{}).get(player_id, {})
            toon_id = player_data.get('prebattleID', 0)
            return toon_id
        return None

    def _load_json_from_replay(self, replay, filter_platoons=False):
        with open(replay, 'rb') as r:
            try:
                data = dict()
                d = r.read(12)
                message = ""
                # the first byte in a valid replay is always 0x12
                if not d[0] == 0x12:
                    message = ('replay excluded due to "not a replay file"')
                    return None
                parts = d[4]
                std = self._extract_json_data(d[8:12], r)
                if std:
                    data['std'] = std
                else:
                    message = ('replay excluded due to "unable to extract json data"')
                    return None
                # Some replay types are bugged or don't work.
                # Forcibly ignore them here
                valid_replay = False
                if (len(std.get('vehicles'))) < 30:
                    message = ('replay excluded due to "not full team"')
                elif std.get('regionCode') == 'CT':
                    message = ('replay excluded due to "test server"')
                elif std.get('bootcampCtx'):
                    message = ('replay excluded due to "tutorial"')
                elif std.get('gameplayID') == 'sandbox':
                    message = ('replay excluded due to "proving grounds"')
                elif std.get('mapName') == '120_kharkiv_halloween':
                    message = ('replay excluded due to "Halloween 2017"')
                else:
                    valid_replay = True
                if not valid_replay:
                    print('\r\n'*2 + message)
                    return False

                if parts == 2:
                    d = r.read(4)
                    ext = self._extract_json_data(d[0:4], r)
                    data['ext'] = ext

                # To detect platoons, we need both parts,
                # So check if the second part exists.
                # If replay is incomplete or we are in a 'toon'
                # don't provide data
                # better to not include incomplete battles and
                # miss some good data, then include bad data
                if filter_platoons:
                    toon_id = self._toon_filter_id(data)
                    # print(f'replay {replay} excluded due to platoon filter')
                    if not toon_id:
                        return None
                    std['platoon_id'] = toon_id
                return data

            except:
                print(f'Could not open replay file: {replay}')
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

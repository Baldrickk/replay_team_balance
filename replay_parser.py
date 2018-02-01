import json
import os
import struct
import glob


class ReplayParser:
    def __init__(self, directorys, over_writer):
        self.directorys = directorys
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

    def _load_json_from_replay(self, replay):
        with open(replay, 'rb') as r:
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
            # Some replays are bugged or don't work.
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
        return data

    def read_replays(self):
        for directory in self.directorys:
            files = glob.glob(directory + os.path.sep + '*wotreplay')
            for i, replay in enumerate(files):
                if replay.rsplit (os.path.sep, 1)[-1] in ('replay_last_battle.wotreplay', 'temp.wotreplay'):
                    continue
                self.ow.print(f'{i+1}/{len(files)} - {replay}')
                json_data = self._load_json_from_replay(replay)
                if json_data:
                    self.replays.append(json_data)
        return self.replays

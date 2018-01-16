import json
import os
import struct
import glob


class ReplayParser:
    def __init__(self, directory, over_writer):
        self.directory = directory
        self.ow = over_writer
        self.replays = []

    @staticmethod
    def _extract_json_data(bin_str, file_r):
        if len(bin_str) != 4:
            raise ValueError("bad binary string length")
        length = struct.unpack('<I', bin_str)[0]
        json_str = file_r.read(length).decode('utf-8')
        # try:
        data = json.loads(json_str)
        # except:
        #    return None
        return data

    def _load_json_from_replay(self, replay):
        with open(replay, 'rb') as r:
            data = dict()
            d = r.read(12)
            parts = d[4]
            json_data = self._extract_json_data(d[8:12], r)
            if json_data:
                data['std'] = json_data
            else:
                return None
            # bootcamp replays are bugged.  forcibly ignore them here:
            if json_data.get('bootcampCtx'):
                return None
            if parts == 2:
                d = r.read(4)
                data['ext'] = self._extract_json_data(d[0:4], r)
        return data

    def read_replays(self):
        files = glob.glob(self.directory + os.path.sep + '20*wotreplay')
        for i, replay in enumerate(files):
            self.ow.print(f'{i+1}/{len(files)} - {replay}')
            json_data = self._load_json_from_replay(replay)
            if json_data:
                self.replays.append(json_data)
        return self.replays

import sys
import json
from replay_parser import ReplayParser
from utils import OverWriter

if len(sys.argv) < 3:
    print('Please provide an input directory and output filename')
    exit()
out_file_name = f'{sys.argv[2]}.ppr'
with OverWriter() as ow:
    replays = ReplayParser([sys.argv[1]], ow).read_replays()
print(f'{len(replays)} read.  Saving as {out_file_name}.')
with open(out_file_name, 'w') as outfile:
    json.dump(replays, outfile)

"""TODO: Module Docstring"""
import sys
import json
from replay_parser import ReplayParser
from utils import OverWriter

if len(sys.argv) < 3:
    print("Please provide an input directory and output filename")
    exit()
OUTFILENAME = f"{sys.argv[2]}.ppr"
with OverWriter() as ow:
    REPLAYS = ReplayParser([sys.argv[1]], ow).read_replays()
print(f"{len(REPLAYS)} read.  Saving as {OUTFILENAME}.")
with open(OUTFILENAME, "w") as outfile:
    json.dump(REPLAYS, outfile)

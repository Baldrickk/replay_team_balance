# replay_team_balance
A tool for checking the average WG ratings of your teams and enemies teams in    World of Tanks

### Usage guide:

###### Get yourself an application ID from wargaming. (optional):
Go to <a href="https://developers.wargaming.net/applications">the Wargaming Developer room</a>, sign in, and create a new server application. Provide your external IP address i.e. what <a href="www.whatsmyip.org">what's my ip</a> tells you, not your machine's LAN address.<br>This lets you make non-rate limited API queries

###### Usage:
```bash
usage: replay_analyser.py [-h] [-w] [-k KEY] dir [dir ...]

A tool to analyse replays.

positional arguments:
  dir                path to directory(s) containing replays

optional arguments:
  -h, --help         show this help message and exit
  -k KEY, --key KEY  application id (key) from
                     https://developers.wargaming.net/applications/ (optional)
```
The program creates a cache.csv file so, if you need to stop it, WG results will not be fetched again. You can re-run or continue from where you left off. 

### To run a .exe:
Go to <a href="https://github.com/Baldrickk/replay_team_balance/releases">releases</a> and download the latest version.<br>
The executable can be run from the command line (cmd or powershell).

### To run the python code natively:
###### 1. Install python3:
https://www.python.org/ftp/python/3.6.4/python-3.6.4-amd64-webinstall.exe
<br>When you install, ensure you select the "add to path" option (will be something like that). It should be on the first page of the installer, otherwise you'll have to set it up manually, which is a pain.

###### 2. Install the required libraries.
Open a new Cmd or PowerShell window.
Assuming path is correctly set up, just run:
```
pip install requests
pip install matplotlib
```
###### 3. Download and unpack (or clone) the code
Either download <a href="https://github.com/Baldrickk/replay_team_balance/archive/master.zip">the latest .zip</a> and unpack to a directory of your choice, or clone the repo

###### 4.Run the code
In a Cmd or Powershell terminal, navigate to the directory where the unpacked code is<br>
```cd C:\full\path\to\containing\directory```
<br>Then run the code.

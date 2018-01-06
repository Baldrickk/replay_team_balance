# replay_team_balance
A tool to check the average WG ratings of your teams vs your enemies teams from World of Tanks

Usage guide:

1. Install python3:

https://www.python.org/ftp/python/3.6.4/python-3.6.4-amd64-webinstall.exe

When you install, ensure you select the "add to path" option (will be something like that) I think it is on the first page of the installer, otherwise you'll have to set it up manually, which is a pain.


2. Install the requests library.

Open a new Cmd or PowerShell window.
Assuming path is correctly set up, just run:

<i>pip install requests</i>

 
3. Get yourself an application ID from wargaming.

Go to https://developers.wargaming.net/applications sign in, and create a new server application. Provide your external IP address i.e. what www.whatsmyip.org tells you, not your machine's LAN address.

This lets you make non-rate limited API queries

 
4. Download and unpack the code

Download https://github.com/B...hive/master.zip and unpack to a directory of your choice.

 
5 Run the code

In a Cmd or Powershell terminal, navigate to the directory where the unpacked code is

 <i>cd C:\full\path\to\containing\directory</i>

 Then run the code. Use the application ID you generated earlier.

 <i>python replay_analyser.py C:\Games\World_of_Tanks\replays APPLICATION_ID_HERE</i>


It creates a cache.csv file so if you need to stop it, the results it has already fetched from WG will not need to be fetched again and you can re-run or continue from where you left off. 

plotter.py is still a work in progress. invoked the same way, it provides a .csv containing the average rating for each team for each replay.

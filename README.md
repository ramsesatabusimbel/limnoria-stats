# limnoria-stats.py
A python script that counts words from .log file with Limnoria ChannelLogger.

Change language and banner by yourself or with AI.

Settings:
1. LOG_DIR = "/home/USER/path/to/log/file/folder" # As in "home/bot/limnoria/logs/ChannelLogger/network".

2. CHANNEL = "#channel" # As in #test.

3. OUTPUT_DIR = "/var/www/html" # Where to generate output htlm files, index, daily and total.

4. Generate the ignore nick file.
  mkdir -p /etc/limnoria
  nano /etc/limnoria/ignored_nicks.txt
  Addnicks per line as:
  nick1
  nick2

5. Have a webserver showing the stats.


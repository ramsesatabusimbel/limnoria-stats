#!/usr/bin/env python3
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

# =====================
# Copyright ramsesatabusimbel 2026
# =====================

# =====================
# KONFIG
# =====================
LOG_DIR = "/home/USER/limnoria/logs/ChannelLogger/network”
CHANNEL = ”#channel
LOG_FILE = f"{LOG_DIR}/{CHANNEL}/{CHANNEL}.log"

OUTPUT_DIR = "/var/www/html"

IGNORE_FILE = "/etc/limnoria/ignored_nicks.txt"

TOP_N = 10

# =====================
# HJÄLPFUNKTIONER
# =====================
def load_ignored_nicks():
    try:
        with open(IGNORE_FILE, encoding="utf-8") as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        return set()

def parse_log_line(line):
    """
    Exempelrad:
    2026-02-09T03:06:16  <StrumpaN> Ska du ha kaffe?
    Returns: (date, hour, nick, word_count)
    """
    m = re.match(
        r"(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})\s+<([^>]+)>\s+(.+)",
        line
    )
    if not m:
        return None

    date_str, hour, minute, second, nick, message = m.groups()
    
    # Parse as UTC and convert to Europe/Stockholm
    utc_dt = datetime.strptime(f"{date_str}T{hour}:{minute}:{second}", "%Y-%m-%dT%H:%M:%S")
    utc_dt = utc_dt.replace(tzinfo=ZoneInfo('UTC'))
    stockholm_dt = utc_dt.astimezone(ZoneInfo('Europe/Stockholm'))
    
    # Get date and hour in Stockholm time
    local_date = stockholm_dt.strftime('%Y-%m-%d')
    local_hour = stockholm_dt.hour
    
    word_count = len(message.split())
    return local_date, local_hour, nick.lower(), word_count

def write_html(path, title, body):
    html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
:root {{
  --bg-color: #111;
  --text-color: #eee;
  --heading-color: #fff;
  --link-color: #7af;
  --border-color: #333;
  --nav-bg: #222;
  --nav-hover: #333;
  --table-border: #333;
  --network-color: #888;
  --bar-color: #4caf50;
}}

body.light-theme {{
  --bg-color: #f5f5f5;
  --text-color: #333;
  --heading-color: #000;
  --link-color: #0066cc;
  --border-color: #ddd;
  --nav-bg: #e0e0e0;
  --nav-hover: #d0d0d0;
  --table-border: #ddd;
  --network-color: #666;
  --bar-color: #4caf50;
}}

body {{
  font-family: sans-serif;
  background: var(--bg-color);
  color: var(--text-color);
  margin: 0;
  padding: 20px;
  transition: background 0.3s ease, color 0.3s ease;
}}
a {{ 
  color: var(--link-color);
  text-decoration: none;
  transition: color 0.2s;
}}
a:hover {{
  text-decoration: underline;
}}
h1, h2 {{ 
  color: var(--heading-color);
  transition: color 0.3s ease;
}}
table {{
  border-collapse: collapse;
  margin-top: 1em;
}}
th, td {{
  padding: 6px 12px;
  border-bottom: 1px solid var(--table-border);
  transition: border-color 0.3s ease;
}}
.bar {{
  background: var(--bar-color);
  height: 14px;
}}
header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid var(--border-color);
  padding-bottom: 15px;
  margin-bottom: 20px;
  transition: border-color 0.3s ease;
}}
.channel-info {{
  flex: 1;
}}
.channel-info h1 {{
  margin: 0;
  font-size: 2em;
  color: var(--bar-color);
}}
.channel-info .network {{
  color: var(--network-color);
  font-size: 0.9em;
  margin-top: 5px;
  transition: color 0.3s ease;
}}
nav {{
  display: flex;
  gap: 15px;
  align-items: center;
}}
nav a, #theme-toggle {{
  padding: 8px 15px;
  background: var(--nav-bg);
  border-radius: 4px;
  transition: background 0.2s;
  border: none;
  cursor: pointer;
  color: var(--text-color);
  font-size: 1em;
  font-family: sans-serif;
}}
nav a:hover, #theme-toggle:hover {{
  background: var(--nav-hover);
  text-decoration: none;
}}
#theme-toggle {{
  display: flex;
  align-items: center;
  gap: 5px;
}}
</style>
</head>
<body>

<header>
  <div class="channel-info">
    <h1>#Channel stats</h1>
    <div class="network">Network</div>
  </div>
  <nav>
    <a href="index.html">Top 10</a>
    <a href="daily.html">Per dag</a>
    <a href="total.html">Totalt</a>
    <button id="theme-toggle" title="Byt tema">
      <span id="theme-icon">☀️</span>
    </button>
  </nav>
</header>

{body}

<p><small>Uppdaterad {datetime.now(ZoneInfo('Europe/Stockholm')).strftime('%Y-%m-%d %H:%M:%S')}</small></p>

<script>
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.getElementById('theme-icon');
const body = document.body;

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'light') {{
  body.classList.add('light-theme');
  themeIcon.textContent = '🌙';
}}

themeToggle.addEventListener('click', () => {{
  body.classList.toggle('light-theme');
  
  if (body.classList.contains('light-theme')) {{
    themeIcon.textContent = '🌙';
    localStorage.setItem('theme', 'light');
  }} else {{
    themeIcon.textContent = '☀️';
    localStorage.setItem('theme', 'dark');
  }}
}});
</script>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

# =====================
# HUVUDLOGIK
# =====================
def main():
    ignored = load_ignored_nicks()

    if not os.path.exists(LOG_FILE):
        print(f"[{datetime.now(ZoneInfo('Europe/Stockholm'))}] Loggfil saknas.")
        return

    total_counter = Counter()
    daily_counter = defaultdict(Counter)

    with open(LOG_FILE, encoding="utf-8", errors="ignore") as f:
        for line in f:
            parsed = parse_log_line(line)
            if not parsed:
                continue

            date, hour, nick, word_count = parsed
            if nick in ignored:
                continue

            total_counter[nick] += word_count
            daily_counter[date][nick] += word_count

    # =====================
    # TOP 10
    # =====================
    rows = "".join(
        f"<tr><td>{nick}</td><td>{count}</td></tr>"
        for nick, count in total_counter.most_common(TOP_N)
    )

    write_html(
        f"{OUTPUT_DIR}/index.html",
        "Top 10",
        f"<h1>Top 10 (alla dagar)</h1><table><tr><th>Nick</th><th>Ord</th></tr>{rows}</table>"
    )

    # =====================
    # DAILY
    # =====================
    daily_html = "<h1>Statistik per dag</h1>"
    for day in sorted(daily_counter, reverse=True):
        daily_html += f"<h2>{day}</h2><table>"
        daily_html += "<tr><th>Nick</th><th>Ord</th></tr>"
        for nick, count in daily_counter[day].most_common(TOP_N):
            daily_html += f"<tr><td>{nick}</td><td>{count}</td></tr>"
        daily_html += "</table>"

    write_html(
        f"{OUTPUT_DIR}/daily.html",
        "Per dag",
        daily_html
    )

    # =====================
    # TOTAL
    # =====================
    max_count = max(total_counter.values(), default=1)
    total_words = sum(total_counter.values())

    total_html = "<h1>Total statistik</h1><table>"
    total_html += "<tr><th>Nick</th><th>Ord</th><th>%</th><th></th></tr>"

    for nick, count in total_counter.most_common():
        width = int((count / max_count) * 300)
        percentage = (count / total_words * 100) if total_words > 0 else 0
        total_html += (
            f"<tr><td>{nick}</td><td>{count}</td>"
            f"<td>{percentage:.1f}%</td>"
            f"<td><div class='bar' style='width:{width}px'></div></td></tr>"
        )

    total_html += "</table>"

    write_html(
        f"{OUTPUT_DIR}/total.html",
        "Totalt",
        total_html
    )

    print(f"[{datetime.now(ZoneInfo('Europe/Stockholm'))}] Statistik uppdaterad.")

if __name__ == "__main__":
    main()

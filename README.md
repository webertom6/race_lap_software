# tandem race app

<!-- description -->
This side-project is destined for youth movement, association, etc. making a **race with laps event** which want to have a free software to handle the race data and display the leaderboard to the public and **can work without WIFI**. This is clearly not my field but, I didn't want to see my team use AI-slop (or worse buy it).

I try to make this app clear/simple as possible such that non-technical person that want to customize can and the installation/use required only `uv`. The best would be to be accessible by a large public at once but difficult now.


<!-- screenshot -->

---

## install

**1 - clone or download**

```bash
git clone https://github.com/webertom6/tandem-race-software.git
cd tandem-race-software
```

or download the ZIP from GitHub (green "Code" button -> "Download ZIP"), unzip it, then open a terminal in that folder.

**2 - install dependencies with uv**

```bash
uv sync
```

if `uv` is not installed [Astral doc - Installing uv](https://docs.astral.sh/uv/getting-started/installation/) :

```bash
# windows (powershell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

then run `uv sync` again.

---

## run

```bash
uv run app.py
```

the terminal will print the local addresses + QR code, for example:

```
08:00:00 Server started on port 8094 -- share one of these addresses:
08:00:00   http://192.168.1.42:8094
```

open in a browser:

| page | url |
|---|---|
| operator console | [http://localhost:8094](http://localhost:8094) |
| scoreboard display | [http://localhost:8094/scoreboard](http://localhost:8094/scoreboard) |

to open the scoreboard on a TV or phone on the same network, use the IP address printed in the terminal.

## sharing

1. Windows Settings -> Network & Internet -> Mobile Hotspot -> Enable
2. Connect your phone to that hotspot
3. Run ipconfig -> look for Local Area Connection adapter -> its IPv4 (usually 192.168.137.1) OR test QR code at start
4. Start the server, open http://192.168.137.1:8094 on your phone

---

## features

- **registration phase** 
  - add teams (number + name)
  - set lap distance and race duration
- **race phase** 
  - record laps (+1 per team)
  - revert last lap
  - manual lap entry
  - magic lap (mean duration)
- **finished phase** 
  - results locked
  - final charts (laps over time, lap duration over time)
- operator page adapts to phone and tablet for use during the race
- scoreboard scales for large TV displays (4K)

---

## notes

- state is in-memory only - restarting the app resets all race data
- to share the operator page with another device on the same network, open the IP address printed at startup

---

## license

MIT License - Copyright (c) 2026 Tom Weber - see [LICENSE](LICENSE)

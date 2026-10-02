# Screens
Operator: http://localhost:8095
Public display: http://localhost:8095/scoreboard

# Operator controls
Auto scroll : scroll auto on summary page if too many info

# Import/Export state
Export a .json file with the current state so it can be resumed at this exact point

# Race
Configure (config is frozen) -> Add teams -> Start race -> +1 per crossing -> Finish for charts (when timer goes to 0, still need to clikc on finish race)

# Corrections
Revert, manual/magic lap, or preview/confirm lap edits (delete or modify somelap of a specified team)

# Display
share the startup LAN address on the same network

# Standings and tie-break decisions
Apply these rules in order; use the next rule only when the previous one is tied

1. Most completed laps first
2. Same lap count: earliest recorded crossing time for the last completed lap first
3. Same lap count and crossing time: lowest internal team ID first (normally registration order, not the displayed team number)

Example: A has 6 laps and B has 5, so A leads regardless of lap times
If both have 6 laps, A's sixth crossing at 10:30 beats B's at 10:32
If those crossing times are identical, the internal team ID decides

Teams with no completed laps are ordered by internal team ID
Best lap, last lap duration, current timer, and team name do not break ties
Ranks are always distinct; a full tie is not displayed as a shared position

# Saving
Autosave restores progress
Force-closing can lose recent changes

# Offline
Setup needs Internet once; then `uv run --offline --no-sync app.py`
Keep the terminal open

# Audit log
Actions by the operator/user are printed there as a trace of every decisions
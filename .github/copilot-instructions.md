# Copilot Instructions

## Build, test, and lint commands

Python Bottle backend served by Waitress, with Hupper for dev auto-reload. Dependencies managed with `uv`

- Install dependencies: `uv sync`
- Run app (dev, auto-reload via hupper): `python app.py`
- Server URL: `http://localhost:8094`
- The startup log prints LAN IP addresses and QR codes for quick device access

No formal lint or test runner is configured

- Single-file backend syntax check: `python -m py_compile app.py`
- Single endpoint smoke check: `curl http://localhost:8094/api/state`
- Single operator action check: `curl -X POST http://localhost:8094/api/register-team -H "Content-Type: application/json" -d "{\"number\":1,\"name\":\"Team A\"}"`
- Config change check (registry phase only): `curl -X POST http://localhost:8094/api/set-config -H "Content-Type: application/json" -d "{\"lap_distance_km\":9,\"race_duration_minutes\":180}"`

## High-level architecture

- `app.py` is the full backend
  - owns global in-memory race state (`STATE`) protected by `Lock`
  - enforces phase transitions: `registry -> race -> finished`
  - computes all derived views (`team_snapshot`, `build_leaderboard`, `build_charts_data`) before returning `/api/state`
  - exposes operator mutation APIs:
    - registry: `/api/register-team`, `/api/remove-team`, `/api/set-config`
    - race: `/api/start-race`, `/api/increment-lap`, `/api/revert-last-lap`, `/api/manual-lap`, `/api/magic-lap`, `/api/finish-race`
    - reset: `/api/reset-all`
  - served by Waitress in production; Hupper wraps `main()` for dev hot-reload
  - prints LAN IPs and ASCII QR codes at startup for quick access from other devices
- UI is split into two static pages under `static/`
  - `operator.html` + `operator.js`: control plane for registration and race actions
  - `scoreboard.html` + `scoreboard.js`: display plane for public leaderboard and final charts
- Both pages poll `/api/state` every second for sync
  - operator page mutates state through POST APIs, then refreshes
  - scoreboard page is read-only and only renders snapshots
- Final charts are backend-driven
  - backend returns pre-shaped series in `state.charts`
  - frontend passes those points directly to Chart.js in scoreboard view

## Key conventions in this codebase

- Treat backend as source of truth
  - do not compute rankings or lap stats in frontend code
  - frontend should render values from `/api/state` only
- Preserve API response contract
  - success responses use `{"ok": true, ...}`
  - error responses use `{"ok": false, "error": "..."}`
- Preserve leaderboard tie-break behavior in `build_leaderboard`
  - primary key: higher lap count first
  - tie-break: earlier `last_crossing_at`
  - final tie-break: lower internal team id
- Keep lap event shape stable for each team
  - each lap entry includes `duration_seconds`, `crossing_at`, and `source` (`button`, `manual`, `magic`)
- Revert behavior depends on lap history
  - after revert, `lap_started_at` is restored from previous lap crossing or race start
- Race timing model is event-driven, not per-ms push
  - timers are derived with `now - lap_started_at` at snapshot time
  - UIs refresh with 1s polling
- App state is intentionally in-memory for v1
  - restart resets race data
- `/api/set-config` is only valid during `registry` phase; changes `lap_distance_km` and `race_duration_seconds`
- `magic-lap` falls back from team mean to global mean; errors if no lap data exists at all
- `remove-team` is only valid during `registry` phase
- JS clock rendering: operator uses `race-clock-elapsed` / `race-clock-remaining` element IDs; scoreboard uses the same IDs. Both JS files guard against null elements before setting `textContent`
- Keep display styling aligned with design tokens in `static/style.css` (navy `#061534`, blue `#005eff`, red `#e11d22`, Barlow Condensed + Barlow + Roboto Mono font stack)

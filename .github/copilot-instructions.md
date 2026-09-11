# Copilot Instructions

## Build, test, and lint commands

Python Bottle backend served by Waitress, with Hupper for dev auto-reload. Dependencies managed with `uv`.

- Install dependencies: `uv sync`
- Run app (dev, auto-reload via hupper): `uv run app.py` (plain `python app.py` only works if the venv is already activated)
- Server URL: `http://localhost:8095`
- The startup log prints LAN IP addresses and QR codes for quick device access
- Dev-server gotcha: `uv run` spawns a hupper monitor + worker process pair that a terminal kill does not reliably clean up. Before starting a fresh server, check for orphans: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'race_lap_software|hupper' }`, then stop them. Do this *before* starting the new server, not after (the new process matches the same filter)

No test runner is configured

- Python lint: `uv run ruff check .`
- Backend syntax check: `uv run python -m py_compile app.py race_state.py api_handlers.py autosave.py network.py`
- Frontend syntax check: `node --check static/operator.js` (or `scoreboard.js`, `shared.js`)
- Single endpoint smoke check: `curl http://localhost:8095/api/state`
- Single operator action check: `curl -X POST http://localhost:8095/api/register-team -H "Content-Type: application/json" -d "{\"number\":1,\"name\":\"Team A\"}"`

## High-level architecture

Backend is split across small modules; `api_handlers.register_routes(app, state)` takes the constructed `Bottle` app and `RaceState` instance as parameters (avoids circular imports between `app.py` and `api_handlers.py`).

- `app.py`: composition root. Creates `app = Bottle()` and `STATE = RaceState()`, loads a previous autosave on startup (`load_state`), wires `STATE.on_change = lambda: save_state(STATE, ...)`, calls `register_routes`, and defines `main()` (Waitress serve + LAN IP/QR banner). `if __name__ == "__main__":` wraps `main` with `hupper.start_reloader` for dev auto-reload
- `race_state.py`: the `RaceState` class holds all mutable race data + a `Lock`. `reset()` reassigns fields in place (same object identity, so no caller needs `global`). Phase state machine is `registry -> race -> finished`. Computes all derived views before they leave the backend: `team_snapshot`, `build_leaderboard` (accepts an optional `teams` param for dry-run previews without mutating real state), `build_charts_data`, `snapshot()`. `to_dict()`/`from_dict()` serialize the raw state (used by both export/import and autosave) and stamp/consume a `saved_at` timestamp so a race resumed after a real-world gap continues from where it left off instead of appearing to have kept running the whole time (see "Resume-after-gap" below)
- `api_handlers.py`: all Bottle routes. Response contract: `{"ok": true, ...}` on success, `{"ok": false, "error": "..."}` on failure (`err()`/`ok()` helpers)
- `autosave.py`: `save_state()` (atomic temp-file + `os.replace`, never raises) / `load_state()` (best-effort restore, returns the resume gap in seconds or `None`)
- `network.py`: `get_local_ips()` / `print_qr()` for the startup LAN banner
- Frontend is two static pages under `static/`, both polling `GET /api/state` every 1s and rendering only what the backend sends (never compute rankings/stats client-side):
  - `operator.html` + `operator.js`: control plane. Layout is phase-aware: `#registry-setup-group` (full config/add-team forms) is swapped for a collapsed `#registry-summary-card` once `phase !== "registry"`, and the freed space is used to promote "Phase 2/3 controls" into the left column, which is `position: sticky` above the 1121px breakpoint (`.op-stack-sticky` in `style.css`)
  - `scoreboard.html` + `scoreboard.js`: read-only display. Auto-scroll is driven by `setInterval`, not `requestAnimationFrame` (rAF gets throttled hard when the page is "occluded", e.g. during a fullscreen transition; `setInterval` isn't). Chart.js renders `state.charts` once `phase === "finished"`
  - `shared.js`: code shared between the two pages (`formatSeconds`, `renderClock`, `fetchState`)

## Key conventions in this codebase

- Backend is the source of truth; frontend renders values from `/api/state` only
- Leaderboard tie-break in `build_leaderboard`: higher lap count first, then earlier `last_crossing_at`, then lower internal team id
- Lap shape is `{duration_seconds, crossing_at, source}`; `source` is one of `"button +1" | "manual" | "magic"`
- Revert/edit behavior recomputes `lap_started_at` from the new last lap's `crossing_at` (falling back to `race_start_at`, else `None`) whenever the removed/edited lap was the team's last one
- Lap editing supports a **batch of mixed edits** in one call: `POST /api/apply-lap-edit` body is `{team_id, edits: [{lap_index, action: "edit"|"remove", new_duration?}, ...]}`. The whole batch is validated before anything is mutated (one bad entry rejects all of them) in `race_state._edit_team_laps`
- Phase gating: `/api/set-config`, `/api/register-team`, `/api/remove-team` only valid in `registry`; `/api/increment-lap`, `/api/manual-lap`, `/api/magic-lap`, `/api/preview-lap-edit`, `/api/apply-lap-edit` only valid in `race`
- `magic-lap` falls back from team mean to global mean; errors if no lap data exists at all
- Race timing is snapshot-computed (`now - lap_started_at`), not push-based; both pages simply poll every 1s
- **State persists across restarts** via autosave to `race_state_autosave.json` (gitignored, written after every mutating route via `RaceState.on_change`) - it is not "in-memory only"
- **Resume-after-gap**: `to_dict()` stamps `saved_at`; `from_dict()` shifts `race_start_at` + every `lap_started_at` + every `crossing_at` forward by `now() - saved_at` (only when `phase == "race"`), so importing an export or reloading an autosave after real downtime doesn't make timers look like they kept running. Audit log timestamps are deliberately never shifted (they record real wall-clock history)
- Design tokens in `static/style.css`: navy `#061534`, blue `#005eff`, red `#e11d22`, danger `#b91c1c`, shared `--line` token used for **both** `body` and `.page` background (keep them equal - a past bug had them mismatched, causing a visible seam)
- Font stack: Barlow Condensed (display) + Barlow (body) + Roboto Mono (numbers/timers)


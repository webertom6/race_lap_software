import time
from threading import Lock

from bottle import Bottle, HTTPResponse, request, response, static_file


app = Bottle()
state_lock = Lock()


def new_state():
    return {
        "phase": "registry",  # registry | race | finished
        "race_duration_seconds": 3 * 60 * 60,
        "race_start_at": None,
        "race_end_at": None,
        "teams": [],
        "next_team_id": 1,
        "audit": [],
    }


STATE = new_state()


def now_ts():
    return time.time()


def err(message, status=400):
    return HTTPResponse(
        body={"ok": False, "error": str(message)},
        status=status,
        headers={"Content-Type": "application/json"},
    )


def ok(payload=None):
    data = {"ok": True}
    if payload:
        data.update(payload)
    return data


def find_team(team_id):
    for team in STATE["teams"]:
        if team["id"] == team_id:
            return team
    return None


def push_audit(action, message):
    STATE["audit"].append({"at": now_ts(), "action": action, "message": message})
    if len(STATE["audit"]) > 500:
        STATE["audit"] = STATE["audit"][-500:]


def add_lap(team, duration_seconds, source):
    crossing = now_ts()
    duration = float(duration_seconds)
    if duration < 0:
        duration = 0.0
    team["laps"].append(
        {
            "duration_seconds": duration,
            "crossing_at": crossing,
            "source": source,
        }
    )
    team["lap_started_at"] = crossing


def mean_lap_duration_for_team(team):
    if not team["laps"]:
        return None
    values = [lap["duration_seconds"] for lap in team["laps"]]
    return sum(values) / len(values)


def mean_lap_duration_global():
    values = []
    for team in STATE["teams"]:
        values.extend([lap["duration_seconds"] for lap in team["laps"]])
    if not values:
        return None
    return sum(values) / len(values)


def team_snapshot(team, now_value):
    laps_count = len(team["laps"])
    last_lap = team["laps"][-1]["duration_seconds"] if laps_count > 0 else None
    best_lap = min((lap["duration_seconds"] for lap in team["laps"]), default=None)
    last_crossing = team["laps"][-1]["crossing_at"] if laps_count > 0 else None

    running = None
    if STATE["phase"] == "race" and team["lap_started_at"] is not None:
        running = max(0.0, now_value - team["lap_started_at"])

    return {
        "id": team["id"],
        "number": team["number"],
        "name": team["name"],
        "laps_count": laps_count,
        "last_lap_seconds": last_lap,
        "best_lap_seconds": best_lap,
        "running_lap_seconds": running,
        "last_crossing_at": last_crossing,
    }


def build_leaderboard(now_value):
    items = [team_snapshot(team, now_value) for team in STATE["teams"]]
    items.sort(
        key=lambda t: (
            -t["laps_count"],
            t["last_crossing_at"] if t["last_crossing_at"] is not None else float("inf"),
            t["id"],
        )
    )
    for index, row in enumerate(items, start=1):
        row["rank"] = index
    return items


def build_charts_data():
    if STATE["race_start_at"] is None:
        return {"laps_over_time": [], "lap_durations": []}

    lap_progress = []
    lap_durations = []
    start = STATE["race_start_at"]

    for team in STATE["teams"]:
        lap_points = [{"x": 0, "y": 0}]
        lap_duration_points = []
        lap_count = 0
        for lap in team["laps"]:
            lap_count += 1
            elapsed_minutes = max(0.0, (lap["crossing_at"] - start) / 60.0)
            lap_points.append({"x": elapsed_minutes, "y": lap_count})
            lap_duration_points.append({"x": elapsed_minutes, "y": lap["duration_seconds"]})

        lap_progress.append(
            {"team_id": team["id"], "label": f"#{team['number']} {team['name']}", "points": lap_points}
        )
        lap_durations.append(
            {"team_id": team["id"], "label": f"#{team['number']} {team['name']}", "points": lap_duration_points}
        )

    return {
        "laps_over_time": lap_progress,
        "lap_durations": lap_durations,
    }


def state_snapshot():
    now_value = now_ts()
    leaderboard = build_leaderboard(now_value)
    teams = [team_snapshot(team, now_value) for team in STATE["teams"]]
    return {
        "phase": STATE["phase"],
        "race_duration_seconds": STATE["race_duration_seconds"],
        "race_start_at": STATE["race_start_at"],
        "race_end_at": STATE["race_end_at"],
        "now": now_value,
        "teams": teams,
        "leaderboard": leaderboard,
        "charts": build_charts_data(),
        "audit": STATE["audit"][-100:],
    }


@app.get("/")
def operator_page():
    return static_file("operator.html", root="./static")


@app.get("/scoreboard")
def scoreboard_page():
    return static_file("scoreboard.html", root="./static")


@app.get("/static/<filepath:path>")
def static_assets(filepath):
    return static_file(filepath, root="./static")


@app.get("/api/state")
def api_state():
    response.content_type = "application/json"
    with state_lock:
        return state_snapshot()


@app.post("/api/register-team")
def api_register_team():
    response.content_type = "application/json"
    data = request.json or {}
    name = str(data.get("name", "")).strip()
    number_raw = str(data.get("number", "")).strip()

    if not name:
        return err("team name is required")
    if not number_raw.isdigit():
        return err("team number must be an integer")

    number = int(number_raw)
    if number <= 0:
        return err("team number must be >= 1")

    with state_lock:
        if STATE["phase"] != "registry":
            return err("cannot add team outside registry phase")

        for team in STATE["teams"]:
            if team["number"] == number:
                return err("team number already exists")

        team_id = STATE["next_team_id"]
        STATE["next_team_id"] += 1
        STATE["teams"].append(
            {
                "id": team_id,
                "number": number,
                "name": name,
                "laps": [],
                "lap_started_at": None,
            }
        )
        push_audit("register-team", f"added team #{number} {name}")
        return ok({"state": state_snapshot()})


@app.post("/api/start-race")
def api_start_race():
    response.content_type = "application/json"
    with state_lock:
        if STATE["phase"] != "registry":
            return err("race can only start from registry phase")
        if len(STATE["teams"]) < 1:
            return err("add at least one team before starting race")

        start = now_ts()
        STATE["phase"] = "race"
        STATE["race_start_at"] = start
        STATE["race_end_at"] = None
        for team in STATE["teams"]:
            team["laps"] = []
            team["lap_started_at"] = start
        push_audit("start-race", "race started")
        return ok({"state": state_snapshot()})


@app.post("/api/increment-lap")
def api_increment_lap():
    response.content_type = "application/json"
    data = request.json or {}
    team_id = data.get("team_id")

    with state_lock:
        if STATE["phase"] != "race":
            return err("laps can only be added during race phase")
        if team_id is None:
            return err("team_id is required")

        team = find_team(int(team_id))
        if not team:
            return err("team not found")
        if team["lap_started_at"] is None:
            return err("team timer is not initialized")

        duration = now_ts() - team["lap_started_at"]
        add_lap(team, duration, "button")
        push_audit("increment-lap", f"team #{team['number']} +1 lap")
        return ok({"state": state_snapshot()})


@app.post("/api/revert-last-lap")
def api_revert_last_lap():
    response.content_type = "application/json"
    data = request.json or {}
    team_id = data.get("team_id")

    with state_lock:
        if team_id is None:
            return err("team_id is required")

        team = find_team(int(team_id))
        if not team:
            return err("team not found")
        if not team["laps"]:
            return err("no lap to revert for this team")

        removed = team["laps"].pop()
        if team["laps"]:
            team["lap_started_at"] = team["laps"][-1]["crossing_at"]
        elif STATE["race_start_at"] is not None:
            team["lap_started_at"] = STATE["race_start_at"]
        else:
            team["lap_started_at"] = None

        push_audit(
            "revert-last-lap",
            f"team #{team['number']} reverted lap ({removed['duration_seconds']:.1f}s)",
        )
        return ok({"state": state_snapshot()})


@app.post("/api/manual-lap")
def api_manual_lap():
    response.content_type = "application/json"
    data = request.json or {}
    team_id = data.get("team_id")
    duration_raw = data.get("duration_seconds")

    with state_lock:
        if STATE["phase"] != "race":
            return err("manual lap can only be added during race phase")
        if team_id is None:
            return err("team_id is required")
        if duration_raw is None:
            return err("duration_seconds is required")

        team = find_team(int(team_id))
        if not team:
            return err("team not found")

        try:
            duration = float(duration_raw)
        except (TypeError, ValueError):
            return err("duration_seconds must be numeric")
        if duration <= 0:
            return err("duration_seconds must be > 0")

        add_lap(team, duration, "manual")
        push_audit("manual-lap", f"team #{team['number']} manual lap ({duration:.1f}s)")
        return ok({"state": state_snapshot()})


@app.post("/api/magic-lap")
def api_magic_lap():
    response.content_type = "application/json"
    data = request.json or {}
    team_id = data.get("team_id")

    with state_lock:
        if STATE["phase"] != "race":
            return err("magic lap can only be added during race phase")
        if team_id is None:
            return err("team_id is required")

        team = find_team(int(team_id))
        if not team:
            return err("team not found")

        mean_duration = mean_lap_duration_for_team(team)
        if mean_duration is None:
            mean_duration = mean_lap_duration_global()
        if mean_duration is None:
            return err("no lap data available yet to compute a mean duration")

        add_lap(team, mean_duration, "magic")
        push_audit("magic-lap", f"team #{team['number']} magic lap ({mean_duration:.1f}s)")
        return ok({"state": state_snapshot()})


@app.post("/api/finish-race")
def api_finish_race():
    response.content_type = "application/json"
    with state_lock:
        if STATE["phase"] != "race":
            return err("race can only be finished from race phase")
        STATE["phase"] = "finished"
        STATE["race_end_at"] = now_ts()
        for team in STATE["teams"]:
            team["lap_started_at"] = None
        push_audit("finish-race", "race finished and results locked")
        return ok({"state": state_snapshot()})


@app.post("/api/reset-all")
def api_reset_all():
    response.content_type = "application/json"
    with state_lock:
        global STATE
        STATE = new_state()
        return ok({"state": state_snapshot()})


if __name__ == "__main__":
    app.run(host="localhost", port=8070, debug=True, reloader=True)

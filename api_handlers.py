from bottle import HTTPResponse, request, response, static_file

from race_state import now_ts

REPO_URL = "https://github.com/webertom6/race_lap_software"


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


def _describe_edits(edits):
    parts = []
    for edit in edits:
        try:
            lap_label = f"lap {int(edit.get('lap_index', 0)) + 1}"
        except (TypeError, ValueError):
            lap_label = "lap ?"
        if edit.get("action") == "remove":
            parts.append(f"removed {lap_label}")
        else:
            try:
                duration = float(edit.get("new_duration"))
                parts.append(f"{lap_label} set to {duration:.1f}s")
            except (TypeError, ValueError):
                parts.append(f"{lap_label} edited")
    return ", ".join(parts)


def format_gap(seconds):
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def register_routes(app, state):
    @app.get("/")
    def operator_page():
        return static_file("operator.html", root="./static")

    @app.get("/scoreboard")
    def scoreboard_page():
        return static_file("scoreboard.html", root="./static")

    @app.get("/static/<filepath:path>")
    def static_assets(filepath):
        return static_file(filepath, root="./static")

    @app.get("/qr.png")
    def qr_code():
        import io
        import qrcode
        response.content_type = "image/png"
        buf = io.BytesIO()
        qrcode.make(REPO_URL).save(buf, format="PNG")
        return buf.getvalue()

    @app.get("/api/state")
    def api_state():
        response.content_type = "application/json"
        with state.lock:
            return state.snapshot()

    @app.post("/api/set-config")
    def api_set_config():
        response.content_type = "application/json"
        data = request.json or {}
        distance_raw = data.get("lap_distance_km")
        duration_raw = data.get("race_duration_minutes")

        with state.lock:
            if state.phase != "registry":
                return err("configuration can only be changed during registry phase")

            if distance_raw is not None:
                try:
                    distance = float(distance_raw)
                except (TypeError, ValueError):
                    return err("lap_distance_km must be numeric")
                if distance <= 0:
                    return err("lap_distance_km must be > 0")
                state.lap_distance_km = distance

            if duration_raw is not None:
                try:
                    duration_min = float(duration_raw)
                except (TypeError, ValueError):
                    return err("race_duration_minutes must be numeric")
                if duration_min <= 0:
                    return err("race_duration_minutes must be > 0")
                state.race_duration_seconds = duration_min * 60

            state.push_audit(
                "set-config",
                f"config: {state.lap_distance_km} km, {state.race_duration_seconds / 60:.0f} min",
            )
            return ok({"state": state.snapshot()})

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

        with state.lock:
            if state.phase != "registry":
                return err("cannot add team outside registry phase")

            for team in state.teams:
                if team["number"] == number:
                    return err("team number already exists")

            team_id = state.next_team_id
            state.next_team_id += 1
            state.teams.append(
                {
                    "id": team_id,
                    "number": number,
                    "name": name,
                    "laps": [],
                    "lap_started_at": None,
                }
            )
            state.push_audit("register-team", f"added team #{number} {name}")
            return ok({"state": state.snapshot()})

    @app.post("/api/remove-team")
    def api_remove_team():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")

        with state.lock:
            if state.phase != "registry":
                return err("teams can only be removed during registry phase")
            if team_id is None:
                return err("team_id is required")

            team = state.find_team(int(team_id))
            if not team:
                return err("team not found")

            state.teams = [t for t in state.teams if t["id"] != int(team_id)]
            state.push_audit("remove-team", f"removed team #{team['number']} {team['name']}")
            return ok({"state": state.snapshot()})

    @app.post("/api/start-race")
    def api_start_race():
        response.content_type = "application/json"
        with state.lock:
            if state.phase != "registry":
                return err("race can only start from registry phase")
            if len(state.teams) < 1:
                return err("add at least one team before starting race")

            start = now_ts()
            state.phase = "race"
            state.race_start_at = start
            state.race_end_at = None
            for team in state.teams:
                team["laps"] = []
                team["lap_started_at"] = start
            state.push_audit("start-race", "race started")
            return ok({"state": state.snapshot()})

    @app.post("/api/increment-lap")
    def api_increment_lap():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")

        with state.lock:
            if state.phase != "race":
                return err("laps can only be added during race phase")
            if team_id is None:
                return err("team_id is required")

            team = state.find_team(int(team_id))
            if not team:
                return err("team not found")
            if team["lap_started_at"] is None:
                return err("team timer is not initialized")

            duration = now_ts() - team["lap_started_at"]
            state.add_lap(team, duration, "button +1")
            state.push_audit("increment-lap", f"team #{team['number']} +1 lap")
            return ok({"state": state.snapshot()})

    @app.post("/api/revert-last-lap")
    def api_revert_last_lap():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")

        with state.lock:
            if team_id is None:
                return err("team_id is required")

            team = state.find_team(int(team_id))
            if not team:
                return err("team not found")
            if not team["laps"]:
                return err("no lap to revert for this team")

            removed = team["laps"].pop()
            if team["laps"]:
                team["lap_started_at"] = team["laps"][-1]["crossing_at"]
            elif state.race_start_at is not None:
                team["lap_started_at"] = state.race_start_at
            else:
                team["lap_started_at"] = None

            state.push_audit(
                "revert-last-lap",
                f"team #{team['number']} reverted lap ({removed['duration_seconds']:.1f}s)",
            )
            return ok({"state": state.snapshot()})

    @app.post("/api/manual-lap")
    def api_manual_lap():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")
        duration_raw = data.get("duration_seconds")

        with state.lock:
            if state.phase != "race":
                return err("manual lap can only be added during race phase")
            if team_id is None:
                return err("team_id is required")
            if duration_raw is None:
                return err("duration_seconds is required")

            team = state.find_team(int(team_id))
            if not team:
                return err("team not found")

            try:
                duration = float(duration_raw)
            except (TypeError, ValueError):
                return err("duration_seconds must be numeric")
            if duration <= 0:
                return err("duration_seconds must be > 0")

            state.add_lap(team, duration, "manual")
            state.push_audit("manual-lap", f"team #{team['number']} manual lap ({duration:.1f}s)")
            return ok({"state": state.snapshot()})

    @app.post("/api/magic-lap")
    def api_magic_lap():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")

        with state.lock:
            if state.phase != "race":
                return err("magic lap can only be added during race phase")
            if team_id is None:
                return err("team_id is required")

            team = state.find_team(int(team_id))
            if not team:
                return err("team not found")

            mean_duration = state.mean_lap_duration_for_team(team)
            if mean_duration is None:
                mean_duration = state.mean_lap_duration_global()
            if mean_duration is None:
                return err("no lap data available yet to compute a mean duration")

            state.add_lap(team, mean_duration, "magic")
            state.push_audit("magic-lap", f"team #{team['number']} magic lap ({mean_duration:.1f}s)")
            return ok({"state": state.snapshot()})

    @app.get("/api/team-laps")
    def api_team_laps():
        response.content_type = "application/json"
        team_id_raw = request.query.get("team_id")
        if team_id_raw is None:
            return err("team_id is required")

        with state.lock:
            team = state.find_team(int(team_id_raw))
            if not team:
                return err("team not found")
            laps = [
                {"index": i, "duration_seconds": lap["duration_seconds"], "source": lap["source"]}
                for i, lap in enumerate(team["laps"])
            ]
            return ok({"laps": laps})

    @app.post("/api/preview-lap-edit")
    def api_preview_lap_edit():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")
        edits = data.get("edits")
        if team_id is None or not isinstance(edits, list) or not edits:
            return err("team_id and a non-empty edits list are required")

        with state.lock:
            if state.phase != "race":
                return err("lap editing is only available during the race phase")
            try:
                row = state.preview_team_edit(int(team_id), edits)
            except ValueError as exc:
                return err(str(exc))
            return ok({"preview": row})

    @app.post("/api/apply-lap-edit")
    def api_apply_lap_edit():
        response.content_type = "application/json"
        data = request.json or {}
        team_id = data.get("team_id")
        edits = data.get("edits")
        if team_id is None or not isinstance(edits, list) or not edits:
            return err("team_id and a non-empty edits list are required")

        with state.lock:
            if state.phase != "race":
                return err("lap editing is only available during the race phase")
            try:
                team = state.apply_team_lap_edit(int(team_id), edits)
            except ValueError as exc:
                return err(str(exc))
            state.push_audit("edit-lap", f"team #{team['number']} lap edit: {_describe_edits(edits)}")
            return ok({"state": state.snapshot()})

    @app.post("/api/finish-race")
    def api_finish_race():
        response.content_type = "application/json"
        with state.lock:
            if state.phase != "race":
                return err("race can only be finished from race phase")
            state.phase = "finished"
            state.race_end_at = now_ts()
            for team in state.teams:
                team["lap_started_at"] = None
            state.push_audit("finish-race", "race finished and results locked")
            return ok({"state": state.snapshot()})

    @app.get("/api/export")
    def api_export_state():
        response.content_type = "application/json"
        response.set_header("Content-Disposition", 'attachment; filename="race-state.json"')
        with state.lock:
            return state.to_dict()

    @app.post("/api/import")
    def api_import_state():
        response.content_type = "application/json"
        data = request.json
        if not isinstance(data, dict):
            return err("invalid state file")

        with state.lock:
            try:
                gap = state.from_dict(data)
            except (TypeError, ValueError, KeyError) as exc:
                return err(f"invalid state file: {exc}")
            message = "state imported from file"
            if gap > 0:
                message += f" (resumed after {format_gap(gap)})"
            state.push_audit("import-state", message)
            return ok({"state": state.snapshot()})

    @app.post("/api/toggle-auto-scroll")
    def api_toggle_auto_scroll():
        response.content_type = "application/json"
        with state.lock:
            state.auto_scroll = not state.auto_scroll
            state.push_audit("toggle-auto-scroll", f"auto-scroll {'enabled' if state.auto_scroll else 'disabled'}")
            return ok({"state": state.snapshot()})

    @app.post("/api/reset-all")
    def api_reset_all():
        response.content_type = "application/json"
        with state.lock:
            state.reset()
            return ok({"state": state.snapshot()})

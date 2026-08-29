import time
from threading import Lock


def now_ts():
    return time.time()


class RaceState:
    """Holds all race data; reset() mutates fields in place so the instance
    identity never changes and no caller needs `global` to see a fresh state."""

    def __init__(self):
        self.lock = Lock()
        self._reset_fields()

    def _reset_fields(self):
        self.phase = "registry"  # registry | race | finished
        self.race_duration_seconds = 3 * 60 * 60
        self.lap_distance_km = 9
        self.race_start_at = None
        self.race_end_at = None
        self.teams = []
        self.next_team_id = 1
        self.audit = []
        self.auto_scroll = False

    def reset(self):
        self._reset_fields()

    def to_dict(self):
        return {
            "phase": self.phase,
            "race_duration_seconds": self.race_duration_seconds,
            "lap_distance_km": self.lap_distance_km,
            "race_start_at": self.race_start_at,
            "race_end_at": self.race_end_at,
            "teams": self.teams,
            "next_team_id": self.next_team_id,
            "audit": self.audit,
            "auto_scroll": self.auto_scroll,
        }

    def from_dict(self, data):
        phase = data.get("phase", "registry")
        if phase not in ("registry", "race", "finished"):
            raise ValueError("invalid phase")
        teams = data.get("teams", [])
        if not isinstance(teams, list):
            raise ValueError("teams must be a list")
        audit = data.get("audit", [])
        if not isinstance(audit, list):
            raise ValueError("audit must be a list")

        self.phase = phase
        self.race_duration_seconds = float(data.get("race_duration_seconds", 3 * 60 * 60))
        self.lap_distance_km = float(data.get("lap_distance_km", 9))
        self.race_start_at = data.get("race_start_at")
        self.race_end_at = data.get("race_end_at")
        self.teams = teams
        self.next_team_id = int(data.get("next_team_id", 1))
        self.audit = audit
        self.auto_scroll = bool(data.get("auto_scroll", False))

    def find_team(self, team_id):
        for team in self.teams:
            if team["id"] == team_id:
                return team
        return None

    def push_audit(self, action, message):
        self.audit.append({"at": now_ts(), "action": action, "message": message})
        if len(self.audit) > 500:
            self.audit = self.audit[-500:]

    def add_lap(self, team, duration_seconds, source):
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

    @staticmethod
    def _edit_team_laps(team, edits, race_start_at=None):
        """Apply a batch of edits (list of {lap_index, action, new_duration}) to one
        team, atomically: the whole batch is validated against the original lap
        list before anything is mutated, so one invalid entry rejects all of them.
        lap_index always refers to the position in the ORIGINAL (pre-batch) list.
        """
        if not edits:
            raise ValueError("no edits provided")

        laps = team["laps"]
        original_len = len(laps)
        normalized = []
        seen_indices = set()
        for edit in edits:
            try:
                lap_index = int(edit.get("lap_index"))
            except (TypeError, ValueError):
                raise ValueError("lap_index must be an integer")
            if lap_index < 0 or lap_index >= original_len:
                raise ValueError(f"lap index {lap_index} out of range")
            if lap_index in seen_indices:
                raise ValueError(f"lap index {lap_index} targeted by more than one edit")
            seen_indices.add(lap_index)

            action = edit.get("action")
            if action == "edit":
                new_duration = edit.get("new_duration")
                if new_duration is None:
                    raise ValueError("new_duration is required for edit")
                new_duration = float(new_duration)
                if new_duration <= 0:
                    raise ValueError("duration must be > 0")
                normalized.append({"lap_index": lap_index, "action": "edit", "new_duration": new_duration})
            elif action == "remove":
                normalized.append({"lap_index": lap_index, "action": "remove"})
            else:
                raise ValueError(f"invalid action: {action}")

        # durations first (indices stay stable), then removals highest-index-first
        # so popping never shifts an index we still need to remove or already edited
        for edit in normalized:
            if edit["action"] == "edit":
                laps[edit["lap_index"]]["duration_seconds"] = edit["new_duration"]

        remove_indices = sorted(
            (edit["lap_index"] for edit in normalized if edit["action"] == "remove"), reverse=True
        )
        for lap_index in remove_indices:
            was_last = lap_index == len(laps) - 1
            laps.pop(lap_index)
            if was_last:
                if laps:
                    team["lap_started_at"] = laps[-1]["crossing_at"]
                elif race_start_at is not None:
                    team["lap_started_at"] = race_start_at
                else:
                    team["lap_started_at"] = None

    def preview_team_edit(self, team_id, edits):
        team = self.find_team(team_id)
        if not team:
            raise ValueError("team not found")

        team_copy = {**team, "laps": [dict(lap) for lap in team["laps"]]}
        self._edit_team_laps(team_copy, edits, race_start_at=self.race_start_at)

        now_value = now_ts()
        temp_teams = [team_copy if t["id"] == team_id else t for t in self.teams]
        return next(row for row in self.build_leaderboard(now_value, teams=temp_teams) if row["id"] == team_id)

    def apply_team_lap_edit(self, team_id, edits):
        team = self.find_team(team_id)
        if not team:
            raise ValueError("team not found")
        self._edit_team_laps(team, edits, race_start_at=self.race_start_at)
        return team

    @staticmethod
    def mean_lap_duration_for_team(team):
        if not team["laps"]:
            return None
        values = [lap["duration_seconds"] for lap in team["laps"]]
        return sum(values) / len(values)

    def mean_lap_duration_global(self):
        values = []
        for team in self.teams:
            values.extend([lap["duration_seconds"] for lap in team["laps"]])
        if not values:
            return None
        return sum(values) / len(values)

    def team_snapshot(self, team, now_value):
        laps_count = len(team["laps"])
        last_lap = team["laps"][-1]["duration_seconds"] if laps_count > 0 else None
        best_lap = min((lap["duration_seconds"] for lap in team["laps"]), default=None)
        last_crossing = team["laps"][-1]["crossing_at"] if laps_count > 0 else None

        running = None
        if self.phase == "race" and team["lap_started_at"] is not None:
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

    def build_leaderboard(self, now_value, teams=None):
        source = self.teams if teams is None else teams
        items = [self.team_snapshot(team, now_value) for team in source]
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

    def build_charts_data(self):
        if self.race_start_at is None:
            return {"laps_over_time": [], "lap_durations": []}

        lap_progress = []
        lap_durations = []
        start = self.race_start_at

        for team in self.teams:
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

    def snapshot(self):
        now_value = now_ts()
        return {
            "phase": self.phase,
            "race_duration_seconds": self.race_duration_seconds,
            "lap_distance_km": self.lap_distance_km,
            "race_start_at": self.race_start_at,
            "race_end_at": self.race_end_at,
            "now": now_value,
            "teams": [self.team_snapshot(team, now_value) for team in self.teams],
            "leaderboard": self.build_leaderboard(now_value),
            "charts": self.build_charts_data(),
            "audit": self.audit[-100:],
            "auto_scroll": self.auto_scroll,
        }

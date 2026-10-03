import pytest

from server.race_state import RaceState, now_ts


def make_team(state, number=1, name="Team", laps=None):
    team = {
        "id": state.next_team_id,
        "number": number,
        "name": name,
        "laps": list(laps) if laps else [],
        "lap_started_at": None,
    }
    state.next_team_id += 1
    state.teams.append(team)
    return team


def lap(duration, crossing_at, source="button +1"):
    return {"duration_seconds": duration, "crossing_at": crossing_at, "source": source}


class TestTeamSnapshot:
    def test_fields_with_no_laps(self, state):
        team = make_team(state)
        snap = state.team_snapshot(team, now_value=1000.0)
        assert snap["id"] == team["id"]
        assert snap["laps_count"] == 0
        assert snap["last_lap_seconds"] is None
        assert snap["best_lap_seconds"] is None
        assert snap["last_crossing_at"] is None
        assert snap["running_lap_seconds"] is None

    def test_best_and_last_lap_differ(self, state):
        team = make_team(state, laps=[lap(30.0, 100.0), lap(10.0, 130.0), lap(20.0, 150.0)])
        snap = state.team_snapshot(team, now_value=200.0)
        assert snap["laps_count"] == 3
        assert snap["last_lap_seconds"] == 20.0
        assert snap["best_lap_seconds"] == 10.0
        assert snap["last_crossing_at"] == 150.0

    def test_running_lap_only_during_race_phase(self, state):
        team = make_team(state)
        team["lap_started_at"] = 100.0
        state.phase = "registry"
        assert state.team_snapshot(team, now_value=140.0)["running_lap_seconds"] is None
        state.phase = "race"
        assert state.team_snapshot(team, now_value=140.0)["running_lap_seconds"] == 40.0


class TestBuildLeaderboard:
    def test_ranks_by_lap_count_descending(self, state):
        make_team(state, number=1, laps=[lap(10, 10)])
        make_team(state, number=2, laps=[lap(10, 10), lap(10, 20)])
        rows = state.build_leaderboard(now_value=1000.0)
        assert [row["laps_count"] for row in rows] == [2, 1]
        assert [row["rank"] for row in rows] == [1, 2]

    def test_tie_break_on_earlier_last_crossing(self, state):
        # both teams have 1 lap; the one that crossed earlier ranks first
        make_team(state, number=1, laps=[lap(10, crossing_at=500.0)])
        make_team(state, number=2, laps=[lap(10, crossing_at=100.0)])
        rows = state.build_leaderboard(now_value=1000.0)
        assert [row["number"] for row in rows] == [2, 1]

    def test_tie_break_falls_back_to_lower_team_id(self, state):
        # same lap count, both with no crossing (last_crossing_at is None for both)
        team_a = make_team(state, number=5)
        team_b = make_team(state, number=1)
        rows = state.build_leaderboard(now_value=1000.0)
        assert [row["id"] for row in rows] == [team_a["id"], team_b["id"]]

    def test_dry_run_with_explicit_teams_param_does_not_read_real_state(self, state):
        make_team(state, number=1, laps=[lap(10, 10)])
        fake_team = {"id": 999, "number": 99, "name": "Preview", "laps": [], "lap_started_at": None}
        rows = state.build_leaderboard(now_value=1000.0, teams=[fake_team])
        assert [row["id"] for row in rows] == [999]


class TestBuildChartsData:
    def test_empty_before_race_start(self, state):
        assert state.build_charts_data() == {"laps_over_time": [], "lap_durations": []}

    def test_points_are_elapsed_minutes_since_race_start(self, state):
        state.race_start_at = 1000.0
        make_team(state, number=7, name="Foxes", laps=[lap(30.0, 1060.0), lap(45.0, 1180.0)])
        data = state.build_charts_data()
        assert len(data["laps_over_time"]) == 1
        series = data["laps_over_time"][0]
        assert series["label"] == "#7 Foxes"
        assert series["points"][0] == {"x": 0, "y": 0}
        assert series["points"][1] == {"x": 1.0, "y": 1}  # (1060-1000)/60
        assert series["points"][2] == {"x": 3.0, "y": 2}  # (1180-1000)/60

        durations = data["lap_durations"][0]
        assert durations["points"] == [{"x": 1.0, "y": 30.0}, {"x": 3.0, "y": 45.0}]


class TestResumeAfterGap:
    def test_round_trip_preserves_values(self, state, monkeypatch):
        monkeypatch.setattr("server.race_state.now_ts", lambda: 1_700_000_000.0)
        state.phase = "race"
        state.race_start_at = 1000.0
        make_team(state, number=1, laps=[lap(10.0, 1010.0)])
        state.teams[0]["lap_started_at"] = 1010.0

        dumped = state.to_dict()
        restored = RaceState()
        gap = restored.from_dict(dumped)

        assert gap == 0.0
        assert restored.phase == "race"
        assert restored.race_start_at == 1000.0
        assert restored.teams[0]["laps"][0]["crossing_at"] == 1010.0

    def test_gap_shifts_race_timers_forward_but_not_audit(self, state, monkeypatch):
        state.phase = "race"
        state.race_start_at = 1000.0
        team = make_team(state, number=1, laps=[lap(10.0, 1010.0)])
        team["lap_started_at"] = 1010.0
        state.audit.append({"at": 1005.0, "action": "start-race", "message": "race started"})

        dumped = state.to_dict()
        dumped["saved_at"] = 1010.0  # snapshot was taken 50s before "now"

        monkeypatch.setattr("server.race_state.now_ts", lambda: 1060.0)
        restored = RaceState()
        gap = restored.from_dict(dumped)

        assert gap == 50.0
        assert restored.race_start_at == 1050.0
        assert restored.teams[0]["lap_started_at"] == 1060.0
        assert restored.teams[0]["laps"][0]["crossing_at"] == 1060.0
        assert restored.audit[0]["at"] == 1005.0  # untouched

    def test_no_shift_outside_race_phase(self, state, monkeypatch):
        state.phase = "finished"
        state.race_start_at = 1000.0
        dumped = state.to_dict()
        dumped["saved_at"] = 900.0

        monkeypatch.setattr("server.race_state.now_ts", lambda: 2000.0)
        restored = RaceState()
        gap = restored.from_dict(dumped)

        assert gap == 0.0
        assert restored.race_start_at == 1000.0

    def test_rejects_invalid_phase(self, state):
        dumped = state.to_dict()
        dumped["phase"] = "not-a-real-phase"
        with pytest.raises(ValueError):
            RaceState().from_dict(dumped)

    def test_rejects_non_list_teams(self, state):
        dumped = state.to_dict()
        dumped["teams"] = "not-a-list"
        with pytest.raises(TypeError):
            RaceState().from_dict(dumped)


class TestEditTeamLaps:
    def test_edit_changes_duration_without_touching_others(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0), lap(20.0, 130.0)])
        state._edit_team_laps(team, [{"lap_index": 0, "action": "edit", "new_duration": 15.0}])
        assert team["laps"][0]["duration_seconds"] == 15.0
        assert team["laps"][1]["duration_seconds"] == 20.0

    def test_remove_last_lap_recomputes_lap_started_at_from_new_last(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0), lap(20.0, 130.0)])
        state._edit_team_laps(team, [{"lap_index": 1, "action": "remove"}], race_start_at=50.0)
        assert len(team["laps"]) == 1
        assert team["lap_started_at"] == 100.0  # new last lap's crossing_at

    def test_remove_only_lap_falls_back_to_race_start_at(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0)])
        state._edit_team_laps(team, [{"lap_index": 0, "action": "remove"}], race_start_at=50.0)
        assert team["laps"] == []
        assert team["lap_started_at"] == 50.0

    def test_remove_only_lap_with_no_race_start_at_gives_none(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0)])
        state._edit_team_laps(team, [{"lap_index": 0, "action": "remove"}], race_start_at=None)
        assert team["lap_started_at"] is None

    def test_removing_non_last_lap_keeps_lap_started_at(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0), lap(20.0, 130.0)])
        team["lap_started_at"] = 999.0
        state._edit_team_laps(team, [{"lap_index": 0, "action": "remove"}])
        assert len(team["laps"]) == 1
        assert team["laps"][0]["duration_seconds"] == 20.0
        assert team["lap_started_at"] == 999.0

    def test_batch_is_atomic_one_bad_entry_rejects_everything(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0), lap(20.0, 130.0)])
        original = [dict(l) for l in team["laps"]]
        with pytest.raises(ValueError):
            state._edit_team_laps(
                team,
                [
                    {"lap_index": 0, "action": "edit", "new_duration": 99.0},
                    {"lap_index": 1, "action": "remove"},
                    {"lap_index": 5, "action": "remove"},  # out of range -> whole batch rejected
                ],
            )
        assert team["laps"] == original

    def test_rejects_duplicate_index_in_same_batch(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0)])
        with pytest.raises(ValueError):
            state._edit_team_laps(
                team,
                [
                    {"lap_index": 0, "action": "edit", "new_duration": 5.0},
                    {"lap_index": 0, "action": "remove"},
                ],
            )

    def test_rejects_non_positive_duration(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0)])
        with pytest.raises(ValueError):
            state._edit_team_laps(team, [{"lap_index": 0, "action": "edit", "new_duration": 0}])

    def test_no_edits_raises(self, state):
        team = make_team(state, laps=[lap(10.0, 100.0)])
        with pytest.raises(ValueError):
            state._edit_team_laps(team, [])


class TestMeanLapDuration:
    def test_team_mean(self, state):
        team = make_team(state, laps=[lap(10.0, 1), lap(20.0, 2), lap(30.0, 3)])
        assert state.mean_lap_duration_for_team(team) == 20.0

    def test_team_mean_none_when_no_laps(self, state):
        team = make_team(state)
        assert state.mean_lap_duration_for_team(team) is None

    def test_global_mean_across_all_teams(self, state):
        make_team(state, number=1, laps=[lap(10.0, 1)])
        make_team(state, number=2, laps=[lap(30.0, 2)])
        assert state.mean_lap_duration_global() == 20.0

    def test_global_mean_none_when_nobody_has_laps(self, state):
        make_team(state, number=1)
        make_team(state, number=2)
        assert state.mean_lap_duration_global() is None


class TestPushAudit:
    def test_trims_to_last_500_entries(self, state):
        for i in range(510):
            state.push_audit("test-action", f"message {i}")
        assert len(state.audit) == 500
        assert state.audit[0]["message"] == "message 10"
        assert state.audit[-1]["message"] == "message 509"

    def test_on_change_hook_is_invoked(self, state):
        calls = []
        state.on_change = lambda: calls.append(True)
        state.push_audit("test-action", "hello")
        assert calls == [True]


def test_now_ts_returns_a_real_timestamp():
    before = now_ts()
    assert isinstance(before, float)
    assert before > 0

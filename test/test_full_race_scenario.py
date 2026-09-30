"""End-to-end scenario test with 40 teams through the full race lifecycle.

Unlike test_api_handlers.py (which checks each route in isolation), this test
drives the whole registry -> race -> finished lifecycle once, at a scale close
to real event usage, and asserts the system-wide invariants that only show up
when many teams and many laps interact (leaderboard ordering, chart series
counts, audit growth, export/import fidelity).
"""

from itertools import pairwise

import pytest

TEAM_COUNT = 40


def register_all_teams(client):
    for i in range(1, TEAM_COUNT + 1):
        status, payload = client.post_json("/api/register-team", {"number": i, "name": f"Team {i}"})
        assert status == 200 and payload["ok"] is True


def laps_for_team(index):
    """Deterministic, varied lap count per team (3..10) so ranks differ meaningfully."""
    return (index % 8) + 3


class TestFullRaceScenario:
    def test_forty_team_race(self, client, clock, state):
        register_all_teams(client)

        status, payload = client.post_json("/api/start-race")
        assert status == 200
        assert payload["state"]["phase"] == "race"

        expected_lap_counts = {}
        for index, team_id in enumerate(range(1, TEAM_COUNT + 1), start=0):
            target_laps = laps_for_team(index)
            for lap_number in range(target_laps):
                clock.advance(5 + (index % 4))  # small varied gaps -> distinct crossing timestamps
                if lap_number == target_laps - 1 and team_id % 10 == 0:
                    # every 10th team closes out its race with a magic lap
                    status, payload = client.post_json("/api/magic-lap", {"team_id": team_id})
                elif lap_number % 4 == 3:
                    status, payload = client.post_json(
                        "/api/manual-lap", {"team_id": team_id, "duration_seconds": 40.0 + index}
                    )
                else:
                    status, payload = client.post_json("/api/increment-lap", {"team_id": team_id})
                assert status == 200 and payload["ok"] is True
            expected_lap_counts[team_id] = target_laps

        # mid-race correction: revert team 1's last lap
        status, payload = client.post_json("/api/revert-last-lap", {"team_id": 1})
        assert status == 200 and payload["ok"] is True
        expected_lap_counts[1] -= 1

        # mid-race correction: preview then apply a batch edit for team 2
        # (edit lap 0's duration, remove lap 1) - preview must not mutate state
        preview_status, preview_payload = client.post_json(
            "/api/preview-lap-edit",
            {
                "team_id": 2,
                "edits": [
                    {"lap_index": 0, "action": "edit", "new_duration": 12.3},
                    {"lap_index": 1, "action": "remove"},
                ],
            },
        )
        assert preview_status == 200 and preview_payload["ok"] is True

        apply_status, apply_payload = client.post_json(
            "/api/apply-lap-edit",
            {
                "team_id": 2,
                "edits": [
                    {"lap_index": 0, "action": "edit", "new_duration": 12.3},
                    {"lap_index": 1, "action": "remove"},
                ],
            },
        )
        assert apply_status == 200 and apply_payload["ok"] is True
        expected_lap_counts[2] -= 1

        finish_status, finish_payload = client.post_json("/api/finish-race")
        assert finish_status == 200
        finished_state = finish_payload["state"]
        assert finished_state["phase"] == "finished"

        # --- leaderboard invariants ---
        leaderboard = finished_state["leaderboard"]
        assert len(leaderboard) == TEAM_COUNT
        assert sorted(row["rank"] for row in leaderboard) == list(range(1, TEAM_COUNT + 1))
        assert sorted(row["id"] for row in leaderboard) == list(range(1, TEAM_COUNT + 1))

        for row in leaderboard:
            assert row["laps_count"] == expected_lap_counts[row["id"]]
            assert row["running_lap_seconds"] is None  # cleared by finish-race

        # ranking must be non-increasing in laps_count, and within an equal-laps
        # group, non-decreasing in last_crossing_at (the documented tie-break)
        for earlier, later in pairwise(leaderboard):
            assert earlier["laps_count"] >= later["laps_count"]
            if (
                earlier["laps_count"] == later["laps_count"]
                and earlier["last_crossing_at"] is not None
                and later["last_crossing_at"] is not None
            ):
                assert earlier["last_crossing_at"] <= later["last_crossing_at"]

        # --- charts invariants ---
        status, state_payload = client.get("/api/state")
        charts = state_payload["charts"]
        assert len(charts["laps_over_time"]) == TEAM_COUNT
        assert len(charts["lap_durations"]) == TEAM_COUNT
        by_team_id = {row["id"]: row for row in leaderboard}
        for series in charts["laps_over_time"]:
            team_id = series["team_id"]
            # first point is the synthetic (0, 0) origin, so real laps = len - 1
            assert len(series["points"]) - 1 == by_team_id[team_id]["laps_count"]

        # --- audit invariants ---
        # the HTTP snapshot only ever carries the last 100 audit entries (by design,
        # see RaceState.snapshot), so the early register-team/start-race entries have
        # scrolled out of it by now at this scale - check the full in-memory log instead
        full_audit_actions = {entry["action"] for entry in state.audit}
        assert {"register-team", "start-race", "revert-last-lap", "edit-lap", "finish-race"} <= full_audit_actions
        assert len(finished_state["audit"]) == 100

        # --- export/import fidelity ---
        export_status, exported = client.get("/api/export")
        assert export_status == 200
        total_laps_before = sum(len(team["laps"]) for team in exported["teams"])

        import_status, import_payload = client.post_json("/api/import", exported)
        assert import_status == 200 and import_payload["ok"] is True
        reimported_teams = import_payload["state"]["teams"]
        assert len(reimported_teams) == TEAM_COUNT
        total_laps_after = sum(team["laps_count"] for team in reimported_teams)
        assert total_laps_after == total_laps_before


def test_laps_for_team_covers_expected_range():
    values = {laps_for_team(i) for i in range(TEAM_COUNT)}
    assert values == set(range(3, 11))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))

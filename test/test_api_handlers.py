import pytest

from server.api_handlers import format_gap


def register_team(client, number, name):
    return client.post_json("/api/register-team", {"number": number, "name": name})


def start_race(client):
    return client.post_json("/api/start-race")


class TestFormatGap:
    def test_seconds_only(self):
        assert format_gap(30) == "30s"

    def test_minutes_and_seconds(self):
        assert format_gap(90) == "1m 30s"

    def test_hours_and_minutes(self):
        assert format_gap(3661) == "1h 01m"


class TestSetConfig:
    def test_updates_distance_and_duration(self, client):
        status, payload = client.post_json(
            "/api/set-config", {"lap_distance_km": 5, "race_duration_minutes": 90}
        )
        assert status == 200
        assert payload["ok"] is True
        assert payload["state"]["lap_distance_km"] == 5
        assert payload["state"]["race_duration_seconds"] == 90 * 60

    def test_rejects_non_positive_distance(self, client):
        _, payload = client.post_json("/api/set-config", {"lap_distance_km": 0})
        assert payload["ok"] is False

    def test_rejects_non_numeric_duration(self, client):
        _, payload = client.post_json("/api/set-config", {"race_duration_minutes": "soon"})
        assert payload["ok"] is False

    def test_blocked_outside_registry_phase(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/set-config", {"lap_distance_km": 5})
        assert payload["ok"] is False


class TestRegisterTeam:
    def test_adds_team(self, client):
        status, payload = register_team(client, 1, "Alpha")
        assert status == 200
        assert payload["ok"] is True
        assert len(payload["state"]["teams"]) == 1

    def test_requires_name(self, client):
        _, payload = client.post_json("/api/register-team", {"number": 1, "name": "  "})
        assert payload["ok"] is False

    def test_requires_integer_number(self, client):
        _, payload = client.post_json("/api/register-team", {"number": "abc", "name": "Alpha"})
        assert payload["ok"] is False

    def test_rejects_duplicate_number(self, client):
        register_team(client, 1, "Alpha")
        _, payload = register_team(client, 1, "Bravo")
        assert payload["ok"] is False

    def test_blocked_outside_registry_phase(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = register_team(client, 2, "Bravo")
        assert payload["ok"] is False


class TestRemoveTeam:
    def test_removes_existing_team(self, client):
        register_team(client, 1, "Alpha")
        _, reg = register_team(client, 2, "Bravo")
        team_id = reg["state"]["teams"][0]["id"]
        status, payload = client.post_json("/api/remove-team", {"team_id": team_id})
        assert status == 200
        assert payload["ok"] is True
        assert len(payload["state"]["teams"]) == 1

    def test_unknown_team_errors(self, client):
        _, payload = client.post_json("/api/remove-team", {"team_id": 9999})
        assert payload["ok"] is False

    def test_blocked_outside_registry_phase(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/remove-team", {"team_id": 1})
        assert payload["ok"] is False


class TestStartRace:
    def test_requires_at_least_one_team(self, client):
        _, payload = client.post_json("/api/start-race")
        assert payload["ok"] is False

    def test_starts_and_resets_laps(self, client):
        register_team(client, 1, "Alpha")
        status, payload = start_race(client)
        assert status == 200
        assert payload["state"]["phase"] == "race"
        assert payload["state"]["race_start_at"] is not None

    def test_blocked_if_already_started(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = start_race(client)
        assert payload["ok"] is False


class TestIncrementLap:
    def test_blocked_outside_race_phase(self, client):
        register_team(client, 1, "Alpha")
        _, payload = client.post_json("/api/increment-lap", {"team_id": 1})
        assert payload["ok"] is False

    def test_adds_one_lap_with_elapsed_duration(self, client, clock):
        register_team(client, 1, "Alpha")
        start_race(client)
        clock.advance(42.5)
        status, payload = client.post_json("/api/increment-lap", {"team_id": 1})
        assert status == 200
        team = payload["state"]["teams"][0]
        assert team["laps_count"] == 1
        assert team["last_lap_seconds"] == pytest.approx(42.5)

    def test_unknown_team_errors(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/increment-lap", {"team_id": 9999})
        assert payload["ok"] is False

    def test_errors_when_timer_not_initialized(self, client, state):
        register_team(client, 1, "Alpha")
        start_race(client)
        state.teams[0]["lap_started_at"] = None
        _, payload = client.post_json("/api/increment-lap", {"team_id": 1})
        assert payload["ok"] is False


class TestRevertLastLap:
    def test_reverts_most_recent_lap(self, client, clock):
        register_team(client, 1, "Alpha")
        start_race(client)
        clock.advance(10)
        client.post_json("/api/increment-lap", {"team_id": 1})
        clock.advance(20)
        client.post_json("/api/increment-lap", {"team_id": 1})

        status, payload = client.post_json("/api/revert-last-lap", {"team_id": 1})
        assert status == 200
        assert payload["state"]["teams"][0]["laps_count"] == 1

    def test_errors_when_no_laps(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/revert-last-lap", {"team_id": 1})
        assert payload["ok"] is False

    def test_not_phase_gated_works_after_finish(self, client, clock):
        # deliberate: revert-last-lap has no phase check in the route, unlike
        # increment/manual/magic-lap - this documents and locks in that behavior
        register_team(client, 1, "Alpha")
        start_race(client)
        clock.advance(10)
        client.post_json("/api/increment-lap", {"team_id": 1})
        client.post_json("/api/finish-race")

        status, payload = client.post_json("/api/revert-last-lap", {"team_id": 1})
        assert status == 200
        assert payload["ok"] is True
        assert payload["state"]["teams"][0]["laps_count"] == 0


class TestManualLap:
    def test_blocked_outside_race_phase(self, client):
        register_team(client, 1, "Alpha")
        _, payload = client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 30})
        assert payload["ok"] is False

    def test_adds_lap_with_given_duration(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        status, payload = client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 33.3})
        assert status == 200
        assert payload["state"]["teams"][0]["last_lap_seconds"] == pytest.approx(33.3)

    def test_rejects_non_positive_duration(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 0})
        assert payload["ok"] is False

    def test_requires_duration_field(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/manual-lap", {"team_id": 1})
        assert payload["ok"] is False


class TestMagicLap:
    def test_blocked_outside_race_phase(self, client):
        register_team(client, 1, "Alpha")
        _, payload = client.post_json("/api/magic-lap", {"team_id": 1})
        assert payload["ok"] is False

    def test_uses_team_mean_when_available(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 10})
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 30})
        status, payload = client.post_json("/api/magic-lap", {"team_id": 1})
        assert status == 200
        assert payload["state"]["teams"][0]["last_lap_seconds"] == pytest.approx(20.0)

    def test_falls_back_to_global_mean(self, client):
        register_team(client, 1, "Alpha")
        register_team(client, 2, "Bravo")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 40})
        # team 2 has no laps of its own yet -> falls back to the global mean (40.0)
        status, payload = client.post_json("/api/magic-lap", {"team_id": 2})
        assert status == 200
        team_two = next(t for t in payload["state"]["teams"] if t["id"] == 2)
        assert team_two["last_lap_seconds"] == pytest.approx(40.0)

    def test_errors_when_no_lap_data_exists_anywhere(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/magic-lap", {"team_id": 1})
        assert payload["ok"] is False


class TestTeamLaps:
    def test_lists_laps_with_index_and_source(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 12})
        status, payload = client.get("/api/team-laps", query={"team_id": 1})
        assert status == 200
        assert payload["laps"] == [{"index": 0, "duration_seconds": 12.0, "source": "manual"}]

    def test_requires_team_id(self, client):
        _, payload = client.get("/api/team-laps")
        assert payload["ok"] is False

    def test_unknown_team_errors(self, client):
        _, payload = client.get("/api/team-laps", query={"team_id": 9999})
        assert payload["ok"] is False


class TestLapEditBatch:
    def test_preview_does_not_mutate_real_state(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 10})
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 20})

        status, payload = client.post_json(
            "/api/preview-lap-edit",
            {"team_id": 1, "edits": [{"lap_index": 0, "action": "edit", "new_duration": 999}]},
        )
        assert status == 200
        assert payload["preview"]["last_lap_seconds"] == 20.0  # unchanged - preview is a dry run

        _, laps_payload = client.get("/api/team-laps", query={"team_id": 1})
        assert laps_payload["laps"][0]["duration_seconds"] == 10.0  # untouched by preview

    def test_apply_mutates_state_and_logs_audit(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 10})
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 20})

        status, payload = client.post_json(
            "/api/apply-lap-edit",
            {"team_id": 1, "edits": [{"lap_index": 0, "action": "remove"}]},
        )
        assert status == 200
        assert payload["state"]["teams"][0]["laps_count"] == 1
        assert any(entry["action"] == "edit-lap" for entry in payload["state"]["audit"])

    def test_batch_atomicity_over_http(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        client.post_json("/api/manual-lap", {"team_id": 1, "duration_seconds": 10})

        _, payload = client.post_json(
            "/api/apply-lap-edit",
            {
                "team_id": 1,
                "edits": [
                    {"lap_index": 0, "action": "edit", "new_duration": 50},
                    {"lap_index": 5, "action": "remove"},  # out of range
                ],
            },
        )
        assert payload["ok"] is False

        _, laps_payload = client.get("/api/team-laps", query={"team_id": 1})
        assert laps_payload["laps"][0]["duration_seconds"] == 10.0  # unchanged

    def test_requires_non_empty_edits_list(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        _, payload = client.post_json("/api/apply-lap-edit", {"team_id": 1, "edits": []})
        assert payload["ok"] is False

    def test_blocked_outside_race_phase(self, client):
        register_team(client, 1, "Alpha")
        _, payload = client.post_json(
            "/api/preview-lap-edit",
            {"team_id": 1, "edits": [{"lap_index": 0, "action": "remove"}]},
        )
        assert payload["ok"] is False


class TestFinishRace:
    def test_blocked_outside_race_phase(self, client):
        register_team(client, 1, "Alpha")
        _, payload = client.post_json("/api/finish-race")
        assert payload["ok"] is False

    def test_locks_phase_and_clears_running_timers(self, client):
        register_team(client, 1, "Alpha")
        start_race(client)
        status, payload = client.post_json("/api/finish-race")
        assert status == 200
        assert payload["state"]["phase"] == "finished"
        assert payload["state"]["teams"][0]["running_lap_seconds"] is None


class TestExportImport:
    def test_export_returns_raw_state_dict(self, client):
        register_team(client, 1, "Alpha")
        status, payload = client.get("/api/export")
        assert status == 200
        assert payload["phase"] == "registry"
        assert "saved_at" in payload
        assert len(payload["teams"]) == 1

    def test_import_rejects_non_dict_body(self, client):
        _status, payload = client.post_json("/api/import", [1, 2, 3])
        assert payload["ok"] is False

    def test_import_round_trip(self, client):
        register_team(client, 1, "Alpha")
        _, exported = client.get("/api/export")
        status, payload = client.post_json("/api/import", exported)
        assert status == 200
        assert payload["ok"] is True
        assert len(payload["state"]["teams"]) == 1

    def test_import_mentions_resumed_gap_in_audit(self, client, clock, state):
        state.phase = "race"
        state.race_start_at = clock.value
        _, exported = client.get("/api/export")
        clock.advance(120)
        _, payload = client.post_json("/api/import", exported)
        messages = [entry["message"] for entry in payload["state"]["audit"]]
        assert any("resumed after" in message for message in messages)


class TestToggleAutoScroll:
    def test_toggles_on_then_off(self, client):
        status, payload = client.post_json("/api/toggle-auto-scroll")
        assert status == 200
        assert payload["ok"] is True
        _, state_payload = client.get("/api/state")
        assert state_payload["auto_scroll"] is True

        client.post_json("/api/toggle-auto-scroll")
        _, state_payload = client.get("/api/state")
        assert state_payload["auto_scroll"] is False


class TestStateSnapshot:
    def test_shape_includes_expected_keys(self, client):
        status, payload = client.get("/api/state")
        assert status == 200
        for key in ("phase", "teams", "leaderboard", "charts", "audit", "auto_scroll", "now"):
            assert key in payload

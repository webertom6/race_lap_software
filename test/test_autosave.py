import json
import os

from server.autosave import load_state, save_state
from server.race_state import RaceState


class TestSaveState:
    def test_writes_a_readable_json_file(self, tmp_path):
        state = RaceState()
        state.teams.append({"id": 1, "number": 1, "name": "Alpha", "laps": [], "lap_started_at": None})
        path = tmp_path / "autosave.json"

        save_state(state, path=str(path))

        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert data["teams"][0]["name"] == "Alpha"

    def test_write_is_atomic_no_leftover_tmp_file(self, tmp_path):
        state = RaceState()
        path = tmp_path / "autosave.json"

        save_state(state, path=str(path))

        assert not os.path.exists(f"{path}.tmp")

    def test_never_raises_on_unwritable_path(self, tmp_path):
        state = RaceState()
        unwritable_dir = tmp_path / "does" / "not" / "exist"
        # parent directories don't exist -> OSError internally, must be swallowed
        save_state(state, path=str(unwritable_dir / "autosave.json"))


class TestLoadState:
    def test_missing_file_returns_none(self, tmp_path):
        result = load_state(RaceState(), path=str(tmp_path / "missing.json"))
        assert result is None

    def test_round_trips_a_saved_state(self, tmp_path):
        original = RaceState()
        original.teams.append({"id": 1, "number": 3, "name": "Gamma", "laps": [], "lap_started_at": None})
        path = tmp_path / "autosave.json"
        save_state(original, path=str(path))

        restored = RaceState()
        gap = load_state(restored, path=str(path))

        assert gap == 0.0
        assert restored.teams[0]["name"] == "Gamma"

    def test_corrupted_json_returns_none_without_raising(self, tmp_path):
        path = tmp_path / "autosave.json"
        path.write_text("{not valid json", encoding="utf-8")

        result = load_state(RaceState(), path=str(path))

        assert result is None

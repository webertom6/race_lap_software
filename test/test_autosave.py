import json
import os
from threading import Event

from server import autosave
from server.autosave import AutosaveWorker, load_state, save_state
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


class TestAutosaveWorker:
    def test_burst_is_coalesced_and_shutdown_flushes_latest_state(self, tmp_path, monkeypatch):
        state = RaceState()
        writes = []
        monkeypatch.setattr(autosave, "_write_snapshot", lambda data, path: writes.append(data) or True)
        worker = AutosaveWorker(state, tmp_path / "autosave.json", delay=60)
        state.on_change = worker.request_save
        try:
            with state.lock:
                for index in range(20):
                    state.push_audit("test", f"change {index}")
            assert writes == []
        finally:
            worker.close()
        assert len(writes) == 1
        assert len(writes[0]["audit"]) == 20
        worker.close()
        assert len(writes) == 1

    def test_slow_write_does_not_hold_lock_or_see_later_mutations(self, tmp_path, monkeypatch):
        state = RaceState()
        entered = Event()
        release = Event()
        writes = []

        def slow_write(data, path):
            if not writes:
                entered.set()
                assert release.wait(5)
            writes.append(data)
            return True

        monkeypatch.setattr(autosave, "_write_snapshot", slow_write)
        worker = AutosaveWorker(state, tmp_path / "autosave.json", delay=0.01)
        state.on_change = worker.request_save
        try:
            with state.lock:
                state.push_audit("test", "first")
            assert entered.wait(5)
            assert state.lock.acquire(timeout=1)
            try:
                state.push_audit("test", "second")
            finally:
                state.lock.release()
        finally:
            release.set()
            worker.close()
        assert [entry["message"] for entry in writes[0]["audit"]] == ["first"]
        assert [entry["message"] for entry in writes[-1]["audit"]] == ["first", "second"]

    def test_failed_write_is_retried_without_another_mutation(self, tmp_path, monkeypatch):
        state = RaceState()
        saved = Event()
        attempts = []
        path = tmp_path / "autosave.json"
        path.write_text("previous autosave", encoding="utf-8")
        original_replace = os.replace

        def flaky_replace(source, destination):
            attempts.append(destination)
            if len(attempts) == 1:
                assert path.read_text(encoding="utf-8") == "previous autosave"
                raise OSError("temporarily busy")
            original_replace(source, destination)
            saved.set()

        monkeypatch.setattr(autosave.os, "replace", flaky_replace)
        worker = AutosaveWorker(state, path, delay=0.01)
        try:
            with state.lock:
                worker.request_save()
            assert saved.wait(5)
        finally:
            worker.close()
        assert len(attempts) == 2
        assert json.loads(path.read_text(encoding="utf-8"))["phase"] == "registry"

    def test_idle_worker_does_not_overwrite_existing_file_on_close(self, tmp_path):
        path = tmp_path / "autosave.json"
        path.write_text("existing autosave", encoding="utf-8")
        worker = AutosaveWorker(RaceState(), path)
        worker.close()
        assert path.read_text(encoding="utf-8") == "existing autosave"


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

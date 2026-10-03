import json
import logging
import os
from copy import deepcopy
from threading import Event, Thread

log = logging.getLogger("autosave")

AUTOSAVE_PATH = "race_state_autosave.json"


def save_state(state, path=AUTOSAVE_PATH):
    """Write state.to_dict() to disk atomically (temp file + os.replace).
    Never raises: a failed autosave should not break the request that triggered it.
    """
    _write_snapshot(state.to_dict(), path)


def _write_snapshot(snapshot, path):
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f)
        os.replace(tmp_path, path)
        return True
    except (OSError, ValueError, TypeError) as exc:
        log.warning("autosave failed: %s", exc)
        return False


class AutosaveWorker:
    """Coalesce changes, copy under the state lock, and write outside it."""

    def __init__(self, state, path=AUTOSAVE_PATH, delay=0.25):
        if delay <= 0:
            raise ValueError("autosave delay must be positive")
        self.state = state
        self.path = path
        self.delay = delay
        self._pending = Event()
        self._wake = Event()
        self._stop = Event()
        self._thread = Thread(target=self._run, name="autosave", daemon=True)
        self._thread.start()

    def request_save(self):
        if not self._stop.is_set():
            self._pending.set()
            self._wake.set()

    def _save_pending(self):
        with self.state.lock:
            if not self._pending.is_set():
                return
            snapshot = deepcopy(self.state.to_dict())
            self._pending.clear()
        if not _write_snapshot(snapshot, self.path):
            self._pending.set()
            self._wake.set()

    def _run(self):
        while True:
            self._wake.wait()
            self._wake.clear()
            if self._stop.wait(self.delay):
                return
            self._save_pending()

    def close(self):
        """Wait for any active write, then flush pending changes on shutdown."""
        if self._stop.is_set():
            return
        self._stop.set()
        self._wake.set()
        self._thread.join()
        self._save_pending()


def load_state(state, path=AUTOSAVE_PATH):
    """Best-effort restore from a previous autosave. Returns the resume gap in
    seconds (0.0 if none was needed) on success, or None if nothing was restored.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return state.from_dict(data)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        log.warning("failed to load autosave file %s: %s", path, exc)
        return None

import json
import logging
import os

log = logging.getLogger("autosave")

AUTOSAVE_PATH = "race_state_autosave.json"


def save_state(state, path=AUTOSAVE_PATH):
    """Write state.to_dict() to disk atomically (temp file + os.replace).
    Never raises: a failed autosave should not break the request that triggered it.
    """
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f)
        os.replace(tmp_path, path)
    except OSError as exc:
        log.warning("autosave failed: %s", exc)


def load_state(state, path=AUTOSAVE_PATH):
    """Best-effort restore from a previous autosave. Returns True if restored."""
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state.from_dict(data)
        return True
    except (OSError, ValueError, TypeError, KeyError) as exc:
        log.warning("failed to load autosave file %s: %s", path, exc)
        return False

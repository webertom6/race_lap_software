# Test suite reference

Exhaustive index of every test in this directory: what it checks (one sentence) and, per file, a concise note on how the testing is wired internally. See the root `README.md`'s "automated tests" section for *how to run* the suites and how to read pass/fail output - this file is the detailed index instead.

Two independent suites: Python (`test/*.py`, pytest) and JavaScript (`test/js/*.test.js`, Node's built-in `node:test`).

---

## test_race_state.py (26 tests)

Unit tests against the `RaceState` class directly - no HTTP layer, no Bottle app involved.

**How it works:**
- `make_team(state, ...)` / `lap(...)` helpers in the file build teams/laps without going through the API.
- Uses the `state` fixture (a bare `RaceState()`) from `conftest.py`.
- Time-sensitive tests monkeypatch `server.race_state.now_ts` directly (not the shared `clock` fixture, since these tests don't go through `api_handlers.py`).

**Tests:**
- `TestTeamSnapshot`
  - `test_fields_with_no_laps` - a team with zero laps reports `None`/`0` in every lap-derived field.
  - `test_best_and_last_lap_differ` - best lap and last lap are tracked independently when they're not the same lap.
  - `test_running_lap_only_during_race_phase` - the live "running lap" timer only appears when `phase == "race"`.
- `TestBuildLeaderboard`
  - `test_ranks_by_lap_count_descending` - more laps always ranks higher.
  - `test_tie_break_on_earlier_last_crossing` - equal lap count is broken by whoever crossed the line first.
  - `test_tie_break_falls_back_to_lower_team_id` - a full tie (laps and crossing time) falls back to team id order.
  - `test_dry_run_with_explicit_teams_param_does_not_read_real_state` - the optional `teams=` override is used instead of `self.teams` (dry-run previews).
- `TestBuildChartsData`
  - `test_empty_before_race_start` - charts are empty structures before a race has started.
  - `test_points_are_elapsed_minutes_since_race_start` - chart X values are minutes since `race_start_at`, not raw timestamps.
- `TestResumeAfterGap`
  - `test_round_trip_preserves_values` - `to_dict()` -> `from_dict()` with no real time gap changes nothing.
  - `test_gap_shifts_race_timers_forward_but_not_audit` - a real-world gap shifts `race_start_at`/`lap_started_at`/`crossing_at` forward but leaves audit timestamps untouched.
  - `test_no_shift_outside_race_phase` - no time-shift is applied when the saved phase isn't `"race"`.
  - `test_rejects_invalid_phase` - an unknown `phase` value raises `ValueError`.
  - `test_rejects_non_list_teams` - a non-list `teams` value raises `TypeError`.
- `TestEditTeamLaps` (the `_edit_team_laps` batch-edit primitive)
  - `test_edit_changes_duration_without_touching_others` - editing one lap doesn't affect sibling laps.
  - `test_remove_last_lap_recomputes_lap_started_at_from_new_last` - removing the last lap resets the running timer to the new last lap's crossing time.
  - `test_remove_only_lap_falls_back_to_race_start_at` - removing a team's only lap falls back to the race start time.
  - `test_remove_only_lap_with_no_race_start_at_gives_none` - removing the only lap with no race start at all leaves the timer at `None`.
  - `test_removing_non_last_lap_keeps_lap_started_at` - removing a lap that isn't the last one doesn't touch the running timer.
  - `test_batch_is_atomic_one_bad_entry_rejects_everything` - one invalid entry in a batch rejects the whole batch, unchanged.
  - `test_rejects_duplicate_index_in_same_batch` - two edits targeting the same lap index in one batch is rejected.
  - `test_rejects_non_positive_duration` - an edit with a duration `<= 0` is rejected.
  - `test_no_edits_raises` - calling with an empty edits list raises `ValueError`.
- `TestMeanLapDuration`
  - `test_team_mean` - a team's mean lap duration is the arithmetic mean of its own laps.
  - `test_team_mean_none_when_no_laps` - `None` when the team has no laps yet.
  - `test_global_mean_across_all_teams` - the global mean pools every team's laps together.
  - `test_global_mean_none_when_nobody_has_laps` - `None` when literally no team has a lap yet.
- `TestPushAudit`
  - `test_trims_to_last_500_entries` - the audit log never grows past 500 entries (drops the oldest).
  - `test_on_change_hook_is_invoked` - `push_audit` fires the `on_change` callback (autosave hook).
- `test_now_ts_returns_a_real_timestamp` - the un-mocked `now_ts()` returns a real positive float.

---

## test_api_handlers.py (48 tests)

One HTTP-level test per route/behavior, checking each endpoint's contract in isolation from the others.

**How it works:**
- Uses the `client` fixture (a fresh `Bottle()` app + fresh `RaceState()`, wired with `register_routes` - never the real `app.py` singleton, so nothing touches the real autosave file).
- `client` is a `WSGIClient` (defined in `conftest.py`): a ~50-line dependency-free WSGI test client built on stdlib `io.BytesIO` + `json` + a hand-built WSGI `environ` dict. No `requests`/`webtest`/Flask test client involved.
- Time-sensitive tests use the `clock` fixture, which patches **both** `server.race_state.now_ts` and `server.api_handlers.now_ts` (two separate bindings from the same `from ... import now_ts` pattern - both must be patched for HTTP-level timing to be deterministic).
- `register_team(client, number, name)` / `start_race(client)` module-level helpers remove repetition across test classes.

**Tests:**
- `TestFormatGap` (the `format_gap()` helper used in import/resume audit messages)
  - `test_seconds_only`, `test_minutes_and_seconds`, `test_hours_and_minutes` - formatting at each magnitude (`"30s"`, `"1m 30s"`, `"1h 01m"`).
- `TestSetConfig`
  - `test_updates_distance_and_duration` - valid values are stored (minutes converted to seconds).
  - `test_rejects_non_positive_distance`, `test_rejects_non_numeric_duration` - invalid input is rejected.
  - `test_blocked_outside_registry_phase` - can't change config once racing has started.
- `TestRegisterTeam`
  - `test_adds_team` - a valid team is added.
  - `test_requires_name`, `test_requires_integer_number` - input validation.
  - `test_rejects_duplicate_number` - team numbers must be unique.
  - `test_blocked_outside_registry_phase` - can't register once racing has started.
- `TestRemoveTeam`
  - `test_removes_existing_team`, `test_unknown_team_errors`, `test_blocked_outside_registry_phase`.
- `TestStartRace`
  - `test_requires_at_least_one_team` - can't start an empty race.
  - `test_starts_and_resets_laps` - phase flips to `"race"` and `race_start_at` is set.
  - `test_blocked_if_already_started` - can't start twice.
- `TestIncrementLap`
  - `test_blocked_outside_race_phase`, `test_unknown_team_errors`.
  - `test_adds_one_lap_with_elapsed_duration` - the lap duration equals the real elapsed time (verified via the `clock` fixture).
  - `test_errors_when_timer_not_initialized` - a team whose `lap_started_at` was never set can't get a +1.
- `TestRevertLastLap`
  - `test_reverts_most_recent_lap` - the last lap is removed.
  - `test_errors_when_no_laps` - nothing to revert.
  - `test_not_phase_gated_works_after_finish` - **documents a real code property**: this route, unlike the others, has no phase check at all and still works after `finish-race`.
- `TestManualLap`
  - `test_blocked_outside_race_phase`, `test_adds_lap_with_given_duration`, `test_rejects_non_positive_duration`, `test_requires_duration_field`.
- `TestMagicLap`
  - `test_blocked_outside_race_phase`.
  - `test_uses_team_mean_when_available` - uses the team's own mean when it has lap history.
  - `test_falls_back_to_global_mean` - falls back to the global mean when the team has none yet.
  - `test_errors_when_no_lap_data_exists_anywhere` - errors when there's no lap data at all to compute a mean from.
- `TestTeamLaps`
  - `test_lists_laps_with_index_and_source`, `test_requires_team_id`, `test_unknown_team_errors`.
- `TestLapEditBatch`
  - `test_preview_does_not_mutate_real_state` - preview is a true dry run (verified by re-reading the real laps afterward).
  - `test_apply_mutates_state_and_logs_audit` - apply actually mutates and writes an `edit-lap` audit entry.
  - `test_batch_atomicity_over_http` - one bad entry in the batch, sent over HTTP, still rejects the whole thing.
  - `test_requires_non_empty_edits_list`, `test_blocked_outside_race_phase`.
- `TestFinishRace`
  - `test_blocked_outside_race_phase`.
  - `test_locks_phase_and_clears_running_timers` - phase becomes `"finished"` and every team's running timer clears.
- `TestExportImport`
  - `test_export_returns_raw_state_dict` - export is the raw `to_dict()` shape, not the `{"ok": ...}` envelope.
  - `test_import_rejects_non_dict_body` - a JSON array (or anything non-dict) is rejected.
  - `test_import_round_trip` - export then import preserves the team list.
  - `test_import_mentions_resumed_gap_in_audit` - importing after a real time gap logs a "resumed after ..." audit message.
- `TestToggleAutoScroll`
  - `test_toggles_on_then_off` - the flag flips both ways and is reflected in `/api/state`.
- `TestStateSnapshot`
  - `test_shape_includes_expected_keys` - `/api/state` always includes `phase`/`teams`/`leaderboard`/`charts`/`audit`/`auto_scroll`/`now`.

---

## test_autosave.py (10 tests)

Checks `save_state`/`load_state` and the background autosave worker, entirely against temporary files (never the real `race_state_autosave.json`).

**How it works:** every test uses pytest's built-in `tmp_path` fixture and passes an explicit `path=` argument, so nothing here can ever touch a real project file.
- Worker tests use real threads and `Event` barriers with bounded waits instead of sleeps; slow-write tests replace the disk writer, while the retry test injects one `os.replace` failure and then performs a real save
- Every worker is closed in cleanup so no background thread survives the test

**Tests:**
- `TestSaveState`
  - `test_writes_a_readable_json_file` - the written file round-trips through `json.load`.
  - `test_write_is_atomic_no_leftover_tmp_file` - no `.tmp` file survives a successful save (temp-file + `os.replace` pattern).
  - `test_never_raises_on_unwritable_path` - a save to a non-existent directory doesn't raise (autosave must never break the request that triggered it).
- `TestAutosaveWorker`
  - `test_burst_is_coalesced_and_shutdown_flushes_latest_state` - twenty notifications produce one latest-state write when shutdown flushes the pending burst, and closing twice is harmless
  - `test_slow_write_does_not_hold_lock_or_see_later_mutations` - while a writer is blocked, another mutation acquires the state lock and leaves the first detached snapshot unchanged
  - `test_failed_write_is_retried_without_another_mutation` - a temporary atomic-replacement failure preserves the previous file and is retried successfully without another notification
  - `test_idle_worker_does_not_overwrite_existing_file_on_close` - shutting down an unused worker leaves an existing autosave untouched
- `TestLoadState`
  - `test_missing_file_returns_none` - no autosave file yet -> `None`, not an exception.
  - `test_round_trips_a_saved_state` - what was saved is what comes back.
  - `test_corrupted_json_returns_none_without_raising` - garbage file content -> `None`, not an exception.

---

## test_full_race_scenario.py (2 tests)

The "real condition" end-to-end test: one full race with **40 teams** through the whole `registry -> race -> finished` lifecycle, checking system-wide invariants that only show up when many teams and many laps interact together.

**How it works:**
- `register_all_teams` registers teams 1..40. `laps_for_team(index)` assigns each team a different lap count (3..10) deterministically, so ranks differ meaningfully.
- Drives laps through a mix of `increment-lap` (button +1), `manual-lap`, and `magic-lap` (every 10th team's last lap), using the `clock` fixture to advance time between laps instead of `time.sleep`.
- Performs one `revert-last-lap` and one preview-then-apply batch edit mid-race, adjusting the expected lap counts accordingly.
- After `finish-race`, cross-checks the `leaderboard`, `charts`, `audit` (the full `state.audit` fixture, not the HTTP-snapshot's last-100-only slice), and an export/import round-trip, all in one test.

**Tests:**
- `test_forty_team_race` - the full scenario described above; asserts leaderboard ranking order/ranks/ids, per-team lap counts, non-increasing-by-laps-then-non-decreasing-by-crossing-time ordering, matching chart series counts, presence of every major audit action, and export/import fidelity.
- `test_laps_for_team_covers_expected_range` - a one-line sanity check that the `laps_for_team` helper itself produces the intended 3..10 spread (so the scenario test's premise isn't silently wrong).

---

## test/js/shared.test.js (10 tests)

Pure-logic tests for `static/shared.js` (`formatSeconds`, `renderClock`), used by both the operator and scoreboard pages.

**How it works:**
- `shared.js` has no top-level side effects (only function declarations), so the whole file is safe to run as-is via `vm.createContext` + `vm.runInContext`, with a small fake `document` object (`getElementById`/`querySelectorAll` returning plain stub elements) - no jsdom, no npm install.
- `loadSharedModule({withClockEl, remainingCount})` rebuilds a fresh sandbox + fake DOM per call, so tests don't leak state into each other.

**Tests:**
- `formatSeconds`: null/undefined -> `"--"`; zero and sub-minute formatting; sub-hour and multi-hour formatting; negative values clamp to zero; fractional seconds are floored.
- `renderClock`: shows "Waiting" before a race starts; computes elapsed/remaining correctly during `"race"`; freezes on `race_end_at` (not `now`) once `"finished"`; remaining never goes negative in overtime; does nothing (and doesn't throw) when no matching elements exist in the DOM.

---

## test/js/scoreboard.test.js (5 tests)

Pure-logic tests for two helpers in `static/scoreboard.js`: `teamColor` and `toDatasets`.

**How it works:**
- `scoreboard.js` runs `refreshState()` and `window.setInterval(...)` at the top level, which would need a much larger DOM/Chart.js/fetch stub just to load the file at all. Instead, `extractFunctionSource()` slices out just the `teamColor`/`toDatasets` function source by balanced-brace matching and evaluates only that snippet via `vm.runInNewContext` - the rest of the file (DOM rendering, Chart.js wiring, the polling loop) is never executed by this test.

**Tests:**
- `teamColor`: a single team gets the fixed top-of-scale hue; first/last of several teams sit exactly at the two hue boundaries; a middle index lands strictly between them.
- `toDatasets`: label/points/color are correctly mapped per series (color reused for border+background, distinct across series); an empty series list returns an empty dataset list.

---

## test/js/operator.test.js (22 tests)

Pure-logic tests for the rendering/state-transform functions in `static/operator.js` (the operator console's view layer).

**How it works:**
- Same problem as `scoreboard.js`, worse: operator.js wires ~20 `addEventListener` calls directly against real element IDs at the top level, so running the whole file needs every one of those elements to exist first.
- `loadOperatorModule(documentStub)` extracts only the rendering functions under test (`setError`, `updateTeamSelects`, `hideLapPreview`, `resetLapEditor`, `updateConfirmButtonLabel`, `renderPendingSummary`, `renderLapEditorLaps`, `buildEditsPayload`, `renderAudit`, `renderTable`, `updatePhaseControls`) plus `formatSeconds` (pulled in the same way from `shared.js`, since `renderTable`/`renderClock` need it) via balanced-brace extraction, and the module-level `let`/`const` state (`configDirty`, `editorTeamId`, `editorLaps`, `pendingEdits`) rewritten to `var` so tests can read/set them directly on the sandbox object (plain `let`/`const` don't attach to the vm context object the way `var` does).
- `makeDocumentStub()` builds one fake element per real element id these functions touch (`classList.add/remove/toggle/contains`, `textContent`, `innerHTML`, `value`, `disabled`), plus a `.querySelector()` stub on the three `<form>` elements that need it.
- Objects/arrays *created inside* the vm sandbox (e.g. `buildEditsPayload`'s return value) belong to a different JS realm than the test file, so `assert.deepEqual` needs a `JSON.parse(JSON.stringify(...))` normalization pass first - direct reference/prototype comparison across vm realms otherwise fails even on structurally identical data.

**Tests:**
- `setError` - writes the message, empty/`undefined` clears it.
- `updateTeamSelects` - renders one `<option>` per team into all three selects; preserves the previously selected value across a re-render.
- `hideLapPreview` / `resetLapEditor` - hide the preview panels and clear pending edits.
- `updateConfirmButtonLabel` - singular vs. plural wording ("Confirm change" vs "Confirm N changes"), disabled when there's nothing pending.
- `renderPendingSummary` - hidden when empty; describes a pending edit as `old -> new`; describes a pending removal.
- `renderLapEditorLaps` - placeholder text with no laps; a pending removal is shown disabled with a "Removed" badge; a pending edit is shown with a "Changed" badge and the new value.
- `buildEditsPayload` - maps the internal pending-edits map into the exact `{lap_index, action, new_duration}` shape the API expects.
- `renderAudit` - placeholder text with no history; newest entry renders first.
- `renderTable` - placeholder row with no teams; `"race"` phase shows +1/Revert but not Remove; `"registry"` phase shows Remove but not +1/Revert.
- `updatePhaseControls` - `"registry"` phase enables setup controls and shows the setup group; `"race"` phase disables them and shows the read-only summary card; config inputs are not clobbered while the user is actively editing them (`configDirty`); leaving `"race"` phase resets the lap editor selection.

---

## Known limitations (things the suite does **not** cover)

- **`server/network.py`** (`get_local_ips`, `print_qr`) - not tested. It's OS/network-stack dependent (real sockets, hostname resolution) and low-value to mock; excluded as out of scope.
- **`app.py`'s `main()`** - not tested (starting the real Waitress server, the hupper dev-reloader, the launcher auto-open-browser thread). Covered instead by the existing manual commands in the root `README.md`'s "checks" section (`py_compile`, a real `uv run app.py` + `curl` smoke check).
- **Concurrency** - autosave tests exercise the real worker thread against concurrent mutations and a blocked writer; HTTP routes still run sequentially, so concurrent request stress and hard process termination are not covered
- **JS network glue and DOM event wiring** - `postJSON`, `loadTeamLaps`, `previewPendingEdits`, `onPendingEditsChanged`, `refreshState` (both pages), `ensureCharts`/`renderChartsIfFinished`'s Chart.js integration, and every `addEventListener` registration are **not executed** by the JS suite - only the pure rendering/state functions they call are extracted and tested in isolation (see each JS file's "how it works" above). A real end-to-end click-through test would need a browser automation tool (e.g. Playwright) driving the actual pages against a running server; that's a different, heavier kind of test than the fast, dependency-free unit tests here.
- **Visual/CSS regressions and accessibility** - not covered by either suite.
- **The QR code image (`/qr.png`)** - not tested (thin wrapper around the `qrcode` library).

let configDirty = false;
let lastState = null;
let editorTeamId = null;
let editorLaps = [];
const pendingEdits = new Map();

function setError(message) {
  document.getElementById("error-box").textContent = message || "";
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  return res.json();
}

function updateTeamSelects(teams) {
  const selects = [document.getElementById("manual-team-id"), document.getElementById("magic-team-id")];
  for (const select of selects) {
    const old = select.value;
    select.innerHTML = teams.map((t) => `<option value="${t.id}">#${t.number} ${t.name}</option>`).join("");
    if (old) {
      select.value = old;
    }
  }

  const editSelect = document.getElementById("edit-team-id");
  const oldEdit = editSelect.value;
  editSelect.innerHTML = '<option value="">Select a team</option>' +
    teams.map((t) => `<option value="${t.id}">#${t.number} ${t.name}</option>`).join("");
  if (oldEdit) {
    editSelect.value = oldEdit;
  }
}

function hideLapPreview() {
  document.getElementById("lap-editor-preview").classList.add("is-hidden");
  document.getElementById("lap-editor-pending").classList.add("is-hidden");
}

function resetLapEditor() {
  pendingEdits.clear();
  hideLapPreview();
}

function updateConfirmButtonLabel() {
  const btn = document.getElementById("lap-editor-confirm-btn");
  const n = pendingEdits.size;
  btn.textContent = n > 1 ? `Confirm ${n} changes` : "Confirm change";
  btn.disabled = n === 0;
}

function renderPendingSummary() {
  const box = document.getElementById("lap-editor-pending");
  if (!pendingEdits.size) {
    box.classList.add("is-hidden");
    box.innerHTML = "";
    return;
  }
  const items = [...pendingEdits.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([lapIndex, edit]) => {
      if (edit.action === "remove") {
        return `<li>Lap ${lapIndex + 1}: will be <strong>removed</strong></li>`;
      }
      const original = editorLaps.find((lap) => lap.index === lapIndex);
      const from = original ? original.duration_seconds.toFixed(1) : "?";
      return `<li>Lap ${lapIndex + 1}: ${from}s -&gt; <strong>${edit.new_duration.toFixed(1)}s</strong></li>`;
    })
    .join("");
  box.classList.remove("is-hidden");
  box.innerHTML = `<p class="lap-editor-pending-title">Pending changes (${pendingEdits.size})</p><ul>${items}</ul>`;
}

function renderLapEditorLaps() {
  const box = document.getElementById("lap-editor-laps");
  if (!editorLaps.length) {
    box.innerHTML = '<p class="muted">No laps recorded for this team yet</p>';
    return;
  }
  box.innerHTML = editorLaps
    .map((lap) => {
      const pending = pendingEdits.get(lap.index);
      const isRemoved = pending && pending.action === "remove";
      const isEdited = pending && pending.action === "edit";
      const rowClass = ["row", "lap-editor-row"];
      if (isRemoved) rowClass.push("is-removed");
      if (isEdited) rowClass.push("is-edited");
      const value = isEdited ? pending.new_duration : lap.duration_seconds;
      const badge = isRemoved
        ? '<span class="lap-edit-badge lap-edit-badge-removed">Removed</span>'
        : isEdited
        ? '<span class="lap-edit-badge lap-edit-badge-edited">Changed</span>'
        : "";
      const actionBtn = isRemoved || isEdited
        ? '<button type="button" class="secondary lap-edit-undo">Undo</button>'
        : '<button type="button" class="danger lap-edit-remove">Remove</button>';
      return `
      <div class="${rowClass.join(" ")}" data-lap-index="${lap.index}">
        <div class="field">
          <label>Lap ${lap.index + 1} (s) ${badge}
            <input type="number" min="0.1" step="0.1" class="lap-edit-duration" value="${value.toFixed(1)}" ${isRemoved ? "disabled" : ""}>
          </label>
        </div>
        ${actionBtn}
      </div>`;
    })
    .join("");
}

async function loadTeamLaps(teamId) {
  editorTeamId = teamId || null;
  resetLapEditor();
  if (!teamId) {
    editorLaps = [];
    document.getElementById("lap-editor-laps").innerHTML = "";
    return;
  }
  const res = await fetch(`/api/team-laps?team_id=${teamId}`);
  const data = await res.json();
  if (!data.ok) {
    setError(data.error);
    return;
  }
  editorLaps = data.laps;
  renderLapEditorLaps();
  updateConfirmButtonLabel();
}

function showLapPreview(teamId, preview) {
  const current = (lastState && lastState.leaderboard || []).find((r) => r.id === teamId);
  document.getElementById("lap-editor-preview").classList.remove("is-hidden");
  document.getElementById("lap-preview-current-rank").textContent = current ? current.rank : "--";
  document.getElementById("lap-preview-current-laps").textContent = current ? current.laps_count : "--";
  document.getElementById("lap-preview-current-last").textContent = current ? formatSeconds(current.last_lap_seconds) : "--";
  document.getElementById("lap-preview-current-best").textContent = current ? formatSeconds(current.best_lap_seconds) : "--";
  document.getElementById("lap-preview-new-rank").textContent = preview.rank;
  document.getElementById("lap-preview-new-laps").textContent = preview.laps_count;
  document.getElementById("lap-preview-new-last").textContent = formatSeconds(preview.last_lap_seconds);
  document.getElementById("lap-preview-new-best").textContent = formatSeconds(preview.best_lap_seconds);
}

function buildEditsPayload() {
  return [...pendingEdits.entries()].map(([lap_index, edit]) => ({
    lap_index,
    action: edit.action,
    new_duration: edit.action === "edit" ? edit.new_duration : null,
  }));
}

async function previewPendingEdits() {
  const res = await postJSON("/api/preview-lap-edit", { team_id: editorTeamId, edits: buildEditsPayload() });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  setError("");
  showLapPreview(editorTeamId, res.preview);
  renderPendingSummary();
}

function onPendingEditsChanged() {
  renderLapEditorLaps();
  updateConfirmButtonLabel();
  if (!pendingEdits.size) {
    hideLapPreview();
    return;
  }
  previewPendingEdits();
}

function renderAudit(audit) {
  const box = document.getElementById("audit-list");
  if (!audit.length) {
    box.innerHTML = '<div class="muted">No action yet</div>';
    return;
  }
  const html = [...audit]
    .reverse()
    .map((item) => {
      const at = new Date(item.at * 1000).toLocaleTimeString();
      return `<div class="audit-item"><strong>${at}</strong> - ${item.message}</div>`;
    })
    .join("");
  box.innerHTML = html;
}

function renderTable(state) {
  const tbody = document.getElementById("teams-body");
  if (!state.leaderboard.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="muted">No team registered</td></tr>';
    return;
  }

  tbody.innerHTML = state.leaderboard
    .map((row) => {
      const incBtn = state.phase === "race"
        ? `<button class="action-inc" data-action="inc" data-team-id="${row.id}">+1</button>` : "";
      const revertBtn = state.phase === "race"
        ? `<button class="secondary action-revert" data-action="revert" data-team-id="${row.id}">Revert</button>` : "";
      const removeBtn = state.phase === "registry"
        ? `<button class="danger" data-action="remove" data-team-id="${row.id}">Remove</button>` : "";
      const mobileBtns = `<div class="action-btns-mobile">${incBtn}${revertBtn}${removeBtn}</div>`;
      const hasActions = incBtn || revertBtn || removeBtn;
      return `
        <tr>
          <td class="rank">${row.rank}</td>
          <td>#${row.number} ${row.name}</td>
          <td>${row.laps_count}</td>
          <td>${formatSeconds(row.running_lap_seconds)}</td>
          <td>${formatSeconds(row.last_lap_seconds)}</td>
          <td>${formatSeconds(row.best_lap_seconds)}</td>
          <td ${hasActions ? 'class="action-cell"' : ""}>${incBtn}${revertBtn}${removeBtn}</td>
        </tr>
        <tr class="action-row-mobile">
          <td colspan="7">${mobileBtns}</td>
        </tr>
      `;
    })
    .join("");
}

function updatePhaseControls(state) {
  document.getElementById("phase-pill").textContent = `phase: ${state.phase}`;
  document.getElementById("save-config-btn").disabled = state.phase !== "registry";
  document.getElementById("start-race-btn").disabled = state.phase !== "registry";
  document.getElementById("register-form").querySelector("button").disabled = state.phase !== "registry";
  document.getElementById("finish-race-btn").disabled = state.phase !== "race";
  document.getElementById("manual-lap-form").querySelector("button").disabled = state.phase !== "race";
  document.getElementById("magic-lap-form").querySelector("button").disabled = state.phase !== "race";

  if (!configDirty) {
    document.getElementById("lap-distance").value = state.lap_distance_km;
    document.getElementById("race-duration").value = Math.round(state.race_duration_seconds / 60);
  }

  const autoScrollBtn = document.getElementById("auto-scroll-btn");
  autoScrollBtn.textContent = `Auto-scroll leaderboard: ${state.auto_scroll ? "ON" : "OFF"}`;
  autoScrollBtn.classList.toggle("active", state.auto_scroll);

  const editTeamSelect = document.getElementById("edit-team-id");
  editTeamSelect.disabled = state.phase !== "race";
  if (state.phase !== "race") {
    editTeamSelect.value = "";
    editorTeamId = null;
    editorLaps = [];
    document.getElementById("lap-editor-laps").innerHTML = "";
    resetLapEditor();
  }
}

async function refreshState() {
  try {
    const state = await fetchState();
    lastState = state;
    setError("");
    updatePhaseControls(state);
    updateTeamSelects(state.teams);
    renderClock(state);
    renderTable(state);
    renderAudit(state.audit || []);
  } catch (error) {
    setError(String(error));
  }
}

document.getElementById("config-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const lapDistanceKm = Number(document.getElementById("lap-distance").value);
  const raceDurationMinutes = Number(document.getElementById("race-duration").value);
  const res = await postJSON("/api/set-config", { lap_distance_km: lapDistanceKm, race_duration_minutes: raceDurationMinutes });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  configDirty = false;
  refreshState();
});

document.getElementById("lap-distance").addEventListener("input", () => { configDirty = true; });
document.getElementById("race-duration").addEventListener("input", () => { configDirty = true; });

document.getElementById("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const number = document.getElementById("team-number").value;
  const name = document.getElementById("team-name").value;
  const res = await postJSON("/api/register-team", { number, name });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  event.target.reset();
  refreshState();
});

document.getElementById("start-race-btn").addEventListener("click", async () => {
  const res = await postJSON("/api/start-race", {});
  if (!res.ok) {
    setError(res.error);
    return;
  }
  refreshState();
});

document.getElementById("finish-race-btn").addEventListener("click", async () => {
  const res = await postJSON("/api/finish-race", {});
  if (!res.ok) {
    setError(res.error);
    return;
  }
  refreshState();
});

document.getElementById("reset-all-btn").addEventListener("click", async () => {
  const okReset = window.confirm("Reset all race data?");
  if (!okReset) {
    return;
  }
  await postJSON("/api/reset-all", {});
  refreshState();
});

document.getElementById("auto-scroll-btn").addEventListener("click", async () => {
  await postJSON("/api/toggle-auto-scroll", {});
  refreshState();
});

document.getElementById("export-state-btn").addEventListener("click", () => {
  window.location.href = "/api/export";
});

document.getElementById("import-state-btn").addEventListener("click", () => {
  document.getElementById("import-state-file").click();
});

document.getElementById("import-state-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    const res = await postJSON("/api/import", data);
    if (!res.ok) {
      setError(res.error);
      return;
    }
    refreshState();
  } catch (e) {
    setError("invalid state file");
  }
});

document.getElementById("manual-lap-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const teamId = Number(document.getElementById("manual-team-id").value);
  const durationSeconds = Number(document.getElementById("manual-duration").value);
  const res = await postJSON("/api/manual-lap", {
    team_id: teamId,
    duration_seconds: durationSeconds,
  });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  event.target.reset();
  refreshState();
});

document.getElementById("magic-lap-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const teamId = Number(document.getElementById("magic-team-id").value);
  const res = await postJSON("/api/magic-lap", { team_id: teamId });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  refreshState();
});

document.getElementById("edit-team-id").addEventListener("change", (event) => {
  loadTeamLaps(Number(event.target.value) || null);
});

document.getElementById("lap-editor-laps").addEventListener("change", (event) => {
  if (!event.target.classList.contains("lap-edit-duration")) return;
  const row = event.target.closest(".lap-editor-row");
  const lapIndex = Number(row.dataset.lapIndex);
  const original = editorLaps.find((lap) => lap.index === lapIndex);
  const newDuration = Number(event.target.value);
  if (!(newDuration > 0)) {
    pendingEdits.delete(lapIndex);
  } else if (original && Math.abs(newDuration - original.duration_seconds) < 0.001) {
    pendingEdits.delete(lapIndex);
  } else {
    pendingEdits.set(lapIndex, { action: "edit", new_duration: newDuration });
  }
  onPendingEditsChanged();
});

document.getElementById("lap-editor-laps").addEventListener("click", (event) => {
  const row = event.target.closest(".lap-editor-row");
  if (!row) return;
  const lapIndex = Number(row.dataset.lapIndex);
  if (event.target.classList.contains("lap-edit-remove")) {
    pendingEdits.set(lapIndex, { action: "remove" });
  } else if (event.target.classList.contains("lap-edit-undo")) {
    pendingEdits.delete(lapIndex);
  } else {
    return;
  }
  onPendingEditsChanged();
});

document.getElementById("lap-editor-cancel-btn").addEventListener("click", () => {
  resetLapEditor();
  renderLapEditorLaps();
  updateConfirmButtonLabel();
});

document.getElementById("lap-editor-confirm-btn").addEventListener("click", async () => {
  if (!pendingEdits.size) return;
  const teamId = editorTeamId;
  const res = await postJSON("/api/apply-lap-edit", { team_id: teamId, edits: buildEditsPayload() });
  if (!res.ok) {
    setError(res.error);
    return;
  }
  resetLapEditor();
  refreshState();
  loadTeamLaps(teamId);
});

document.getElementById("teams-body").addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) {
    return;
  }

  const teamId = Number(target.dataset.teamId);
  const action = target.dataset.action;
  if (!teamId || !action) {
    return;
  }

  if (action === "inc") {
    const res = await postJSON("/api/increment-lap", { team_id: teamId });
    if (!res.ok) {
      setError(res.error);
      return;
    }
  }

  if (action === "revert") {
    const res = await postJSON("/api/revert-last-lap", { team_id: teamId });
    if (!res.ok) {
      setError(res.error);
      return;
    }
  }

  if (action === "remove") {
    const res = await postJSON("/api/remove-team", { team_id: teamId });
    if (!res.ok) {
      setError(res.error);
      return;
    }
  }

  refreshState();
});

refreshState();
window.setInterval(refreshState, 1000);

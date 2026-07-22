function formatSeconds(total) {
  if (total === null || total === undefined) {
    return "--";
  }
  const value = Math.max(0, Math.floor(total));
  const h = Math.floor(value / 3600);
  const m = Math.floor((value % 3600) / 60);
  const s = value % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function setError(message) {
  document.getElementById("error-box").textContent = message || "";
}

function updateTeamSelects(teams) {
  const selects = [document.getElementById("manual-team-id"), document.getElementById("magic-team-id")];
  for (const select of selects) {
    const old = select.value;
    select.innerHTML = teams.map((t) => `<option value="${t.id}">#${t.number} ${t.name}</option>`).join("");
    if (old) select.value = old;
  }
}

function renderClock(state) {
  const clockEl = document.getElementById("race-clock-elapsed");
  const clockRem = document.getElementById("race-clock-remaining");
  if (!clockEl) return;
  if (!state.race_start_at) {
    clockEl.textContent = "Waiting";
    if (clockRem) clockRem.textContent = "";
    return;
  }
  const endAt = state.phase === "finished" ? state.race_end_at : state.now;
  const elapsed = Math.max(0, endAt - state.race_start_at);
  const remaining = Math.max(0, state.race_duration_seconds - elapsed);
  clockEl.textContent = formatSeconds(elapsed);
  if (clockRem) clockRem.textContent = formatSeconds(remaining);
}

function renderAudit(audit) {
  const box = document.getElementById("audit-list");
  if (!audit.length) {
    box.innerHTML = '<div class="muted">No action yet</div>';
    return;
  }
  box.innerHTML = [...audit]
    .reverse()
    .map((item) => {
      const at = new Date(item.at * 1000).toLocaleTimeString();
      return `<div class="audit-item"><strong>${at}</strong> - ${item.message}</div>`;
    })
    .join("");
}

function renderTable(state) {
  const tbody = document.getElementById("teams-body");
  if (!state.leaderboard.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="muted">No team registered</td></tr>';
    return;
  }
  tbody.innerHTML = state.leaderboard
    .map((row) => {
      const raceBtn = state.phase === "race"
        ? `<button data-action="inc" data-team-id="${row.id}">+1</button>
           <button class="secondary" data-action="revert" data-team-id="${row.id}">Revert</button>`
        : "";
      const removeBtn = state.phase === "registry"
        ? `<button class="danger" data-action="remove" data-team-id="${row.id}">Remove</button>`
        : "";
      return `
        <tr>
          <td class="rank">${row.rank}</td>
          <td>#${row.number} ${row.name}</td>
          <td>${row.laps_count}</td>
          <td>${formatSeconds(row.running_lap_seconds)}</td>
          <td>${formatSeconds(row.last_lap_seconds)}</td>
          <td>${formatSeconds(row.best_lap_seconds)}</td>
          <td>${raceBtn}${removeBtn}</td>
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

  const distEl = document.getElementById("lap-distance");
  const durEl = document.getElementById("race-duration");
  if (document.activeElement !== distEl) distEl.value = state.lap_distance_km;
  if (document.activeElement !== durEl) durEl.value = Math.round(state.race_duration_seconds / 60);
}

function renderAll(snapshot) {
  setError("");
  updatePhaseControls(snapshot);
  updateTeamSelects(snapshot.teams);
  renderClock(snapshot);
  renderTable(snapshot);
  renderAudit(snapshot.audit || []);
}

// event handlers - synchronous, no fetch needed

document.getElementById("config-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const lapDistanceKm = Number(document.getElementById("lap-distance").value);
  const raceDurationMinutes = Number(document.getElementById("race-duration").value);
  const res = applySetConfig(STATE, lapDistanceKm, raceDurationMinutes);
  if (!res.ok) { setError(res.error); return; }
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("register-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const number = document.getElementById("team-number").value;
  const name = document.getElementById("team-name").value;
  const res = applyRegisterTeam(STATE, number, name);
  if (!res.ok) { setError(res.error); return; }
  event.target.reset();
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("start-race-btn").addEventListener("click", () => {
  const res = applyStartRace(STATE);
  if (!res.ok) { setError(res.error); return; }
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("finish-race-btn").addEventListener("click", () => {
  const res = applyFinishRace(STATE);
  if (!res.ok) { setError(res.error); return; }
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("reset-all-btn").addEventListener("click", () => {
  if (!window.confirm("Reset all race data?")) return;
  STATE = applyResetAll();
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("manual-lap-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const teamId = Number(document.getElementById("manual-team-id").value);
  const durationSeconds = Number(document.getElementById("manual-duration").value);
  const res = applyManualLap(STATE, teamId, durationSeconds);
  if (!res.ok) { setError(res.error); return; }
  event.target.reset();
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("magic-lap-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const teamId = Number(document.getElementById("magic-team-id").value);
  const res = applyMagicLap(STATE, teamId);
  if (!res.ok) { setError(res.error); return; }
  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

document.getElementById("teams-body").addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof HTMLButtonElement)) return;
  const teamId = Number(target.dataset.teamId);
  const action = target.dataset.action;
  if (!teamId || !action) return;

  let res;
  if (action === "inc") res = applyIncrementLap(STATE, teamId);
  if (action === "revert") res = applyRevertLastLap(STATE, teamId);
  if (action === "remove") res = applyRemoveTeam(STATE, teamId);
  if (!res || !res.ok) { if (res) setError(res.error); return; }

  saveAndBroadcast(STATE);
  renderAll(stateSnapshot(STATE));
});

// init and clock tick
renderAll(stateSnapshot(STATE));
setInterval(() => renderClock(stateSnapshot(STATE)), 1000);

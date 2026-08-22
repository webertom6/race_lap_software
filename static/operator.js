let configDirty = false;

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
}

async function refreshState() {
  try {
    const state = await fetchState();
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

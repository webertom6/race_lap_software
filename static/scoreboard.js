let chartLaps = null;
let chartDurations = null;
let chartsRendered = false;
let lastState = null;

function teamColor(index, total) {
  const hue = total <= 1 ? 270 : Math.round(270 - (270 * index / (total - 1)));
  return `hsl(${hue}, 80%, 45%)`;
}

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

function renderClock(state) {
  const clockEl = document.getElementById("race-clock-elapsed") || document.getElementById("race-clock");
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

function renderLeaderboard(state) {
  document.getElementById("phase-pill").textContent = `phase: ${state.phase}`;
  const tbody = document.getElementById("teams-body");
  if (!state.leaderboard.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="muted">No team registered</td></tr>';
    return;
  }
  const validBests = state.leaderboard.map(r => r.best_lap_seconds).filter(v => v !== null && v !== undefined);
  const topBest = validBests.length ? Math.min(...validBests) : null;
  tbody.innerHTML = state.leaderboard
    .map((row) => {
      const bestClass = row.best_lap_seconds == null ? "time" : row.best_lap_seconds === topBest ? "time best-lap-top" : "time best-lap";
      return `
        <tr>
          <td class="rank">${row.rank}</td>
          <td>${row.name}</td>
          <td>${row.laps_count}</td>
          <td class="time" id="timer-${row.id}">${formatSeconds(row.running_lap_seconds)}</td>
          <td class="time">${formatSeconds(row.last_lap_seconds)}</td>
          <td class="${bestClass}">${formatSeconds(row.best_lap_seconds)}</td>
        </tr>
      `;
    })
    .join("");
}

function updateRunningTimers() {
  if (!lastState || lastState.phase !== "race") return;
  const now = Date.now() / 1000;
  for (const row of lastState.leaderboard) {
    const el = document.getElementById(`timer-${row.id}`);
    if (!el) continue;
    const startAt = row.last_crossing_at ?? lastState.race_start_at;
    if (startAt == null) continue;
    el.textContent = formatSeconds(now - startAt);
  }
}

function toDatasets(series) {
  const total = series.length;
  return series.map((item, index) => {
    const color = teamColor(index, total);
    return {
      label: item.label,
      data: item.points,
      borderColor: color,
      backgroundColor: color,
      pointRadius: 2,
      borderWidth: 2,
      tension: 0.15,
      parsing: false,
    };
  });
}

function ensureCharts() {
  if (!chartLaps) {
    chartLaps = new Chart(document.getElementById("laps-over-time-chart"), {
      type: "line",
      data: { datasets: [] },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { title: { display: true, text: "Laps in function of time (minutes)" } },
        scales: {
          x: { type: "linear", title: { display: true, text: "time (min)" } },
          y: { title: { display: true, text: "laps" }, beginAtZero: true },
        },
      },
    });
  }
  if (!chartDurations) {
    chartDurations = new Chart(document.getElementById("lap-duration-chart"), {
      type: "line",
      data: { datasets: [] },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: { title: { display: true, text: "Lap duration in function of time (seconds)" } },
        scales: {
          x: { type: "linear", title: { display: true, text: "time (min)" } },
          y: { title: { display: true, text: "lap duration (s)" }, beginAtZero: true },
        },
      },
    });
  }
}

function renderChartsIfFinished(state) {
  const section = document.getElementById("charts-section");
  if (state.phase !== "finished") {
    section.style.display = "none";
    chartsRendered = false;
    return;
  }
  if (chartsRendered) return;

  section.style.display = "block";
  ensureCharts();

  const rankMap = {};
  for (const row of state.leaderboard) rankMap[row.id] = row.rank;
  const byRank = (a, b) => (rankMap[a.team_id] ?? 999) - (rankMap[b.team_id] ?? 999);
  const lapsSeries = [...(state.charts.laps_over_time || [])].sort(byRank);
  const durationsSeries = [...(state.charts.lap_durations || [])].sort(byRank);

  chartLaps.data.datasets = toDatasets(lapsSeries);
  chartLaps.update();
  chartDurations.data.datasets = toDatasets(durationsSeries);
  chartDurations.update();
  chartsRendered = true;
}

function renderConfig(state) {
  const el = document.getElementById("brand-meta");
  if (!el) return;
  const durationMin = Math.round(state.race_duration_seconds / 60);
  el.textContent = `Lap ${state.lap_distance_km} km · ${durationMin} min`;
}

function renderAll(snapshot) {
  lastState = snapshot;
  renderConfig(snapshot);
  renderClock(snapshot);
  renderLeaderboard(snapshot);
  renderChartsIfFinished(snapshot);
}

// init from localStorage (scoreboard opened after race already started)
try {
  const saved = localStorage.getItem("tandem_race_raw");
  if (saved) renderAll(stateSnapshot(JSON.parse(saved)));
} catch (_) {}

// live updates from operator tab via BroadcastChannel
CHANNEL.onmessage = e => renderAll(e.data);

// clock and running timers tick locally every second
setInterval(() => {
  if (!lastState) return;
  renderClock({ ...lastState, now: Date.now() / 1000 });
  updateRunningTimers();
}, 1000);

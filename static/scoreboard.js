let chartLaps = null;
let chartDurations = null;

const COLORS = [
  "#1d4ed8",
  "#2563eb",
  "#3b82f6",
  "#60a5fa",
  "#0ea5e9",
  "#0284c7",
  "#0369a1",
  "#0891b2",
];

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
  if (!clockEl) {
    return;
  }
  if (!state.race_start_at) {
    clockEl.textContent = "Waiting";
    if (clockRem) {
      clockRem.textContent = "";
    }
    return;
  }
  const endAt = state.phase === "finished" ? state.race_end_at : state.now;
  const elapsed = Math.max(0, endAt - state.race_start_at);
  const remaining = Math.max(0, state.race_duration_seconds - elapsed);
  clockEl.textContent = `${formatSeconds(elapsed)}`;
  if (clockRem) {
    clockRem.textContent = `${formatSeconds(remaining)}`;
  }
}

function renderLeaderboard(state) {
  document.getElementById("phase-pill").textContent = `phase: ${state.phase}`;
  const tbody = document.getElementById("teams-body");
  if (!state.leaderboard.length) {
    tbody.innerHTML = '<tr><td colspan="6" class="muted">No team registered</td></tr>';
    return;
  }
  tbody.innerHTML = state.leaderboard
    .map((row) => {
      return `
        <tr>
          <td class="rank">${row.rank}</td>
          <td>#${row.number} ${row.name}</td>
          <td>${row.laps_count}</td>
          <td>${formatSeconds(row.running_lap_seconds)}</td>
          <td>${formatSeconds(row.last_lap_seconds)}</td>
          <td>${formatSeconds(row.best_lap_seconds)}</td>
        </tr>
      `;
    })
    .join("");
}

function toDatasets(series) {
  return series.map((item, index) => {
    return {
      label: item.label,
      data: item.points,
      borderColor: COLORS[index % COLORS.length],
      backgroundColor: COLORS[index % COLORS.length],
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
    return;
  }

  section.style.display = "block";
  ensureCharts();

  chartLaps.data.datasets = toDatasets(state.charts.laps_over_time || []);
  chartLaps.update();

  chartDurations.data.datasets = toDatasets(state.charts.lap_durations || []);
  chartDurations.update();
}

async function refreshState() {
  const res = await fetch("/api/state");
  const state = await res.json();
  renderClock(state);
  renderLeaderboard(state);
  renderChartsIfFinished(state);
}

refreshState();
window.setInterval(refreshState, 1000);

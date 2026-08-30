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
  const clockRemEls = document.querySelectorAll(".js-remaining-time");
  if (!clockEl && clockRemEls.length === 0) {
    return;
  }
  if (!state.race_start_at) {
    if (clockEl) clockEl.textContent = "Waiting";
    clockRemEls.forEach((el) => { el.textContent = "Waiting"; });
    return;
  }
  const endAt = state.phase === "finished" ? state.race_end_at : state.now;
  const elapsed = Math.max(0, endAt - state.race_start_at);
  const remaining = Math.max(0, state.race_duration_seconds - elapsed);
  if (clockEl) clockEl.textContent = formatSeconds(elapsed);
  clockRemEls.forEach((el) => { el.textContent = formatSeconds(remaining); });
}

async function fetchState() {
  const res = await fetch("/api/state");
  return res.json();
}

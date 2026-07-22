// all business logic, state schema, persistence and broadcast
// loaded by both operator and scoreboard pages

function nowTs() {
  return Date.now() / 1000;
}

function newState() {
  return {
    phase: "registry",
    race_duration_seconds: 3 * 60 * 60,
    lap_distance_km: 9,
    race_start_at: null,
    race_end_at: null,
    teams: [],
    next_team_id: 1,
    audit: [],
  };
}

function findTeam(state, teamId) {
  return state.teams.find(t => t.id === teamId) || null;
}

function pushAudit(state, action, message) {
  state.audit.push({ at: nowTs(), action, message });
  if (state.audit.length > 500) {
    state.audit = state.audit.slice(-500);
  }
}

function addLap(team, durationSeconds, source) {
  const crossing = nowTs();
  const duration = Math.max(0, parseFloat(durationSeconds));
  team.laps.push({ duration_seconds: duration, crossing_at: crossing, source });
  team.lap_started_at = crossing;
}

function meanLapDurationForTeam(team) {
  if (!team.laps.length) return null;
  return team.laps.reduce((acc, l) => acc + l.duration_seconds, 0) / team.laps.length;
}

function meanLapDurationGlobal(state) {
  const values = state.teams.flatMap(t => t.laps.map(l => l.duration_seconds));
  if (!values.length) return null;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function teamSnapshot(team, nowValue, phase) {
  const lapsCount = team.laps.length;
  const lastLap = lapsCount > 0 ? team.laps[lapsCount - 1].duration_seconds : null;
  const bestLap = lapsCount > 0 ? Math.min(...team.laps.map(l => l.duration_seconds)) : null;
  const lastCrossing = lapsCount > 0 ? team.laps[lapsCount - 1].crossing_at : null;
  const running = phase === "race" && team.lap_started_at != null
    ? Math.max(0, nowValue - team.lap_started_at)
    : null;
  return {
    id: team.id,
    number: team.number,
    name: team.name,
    laps_count: lapsCount,
    last_lap_seconds: lastLap,
    best_lap_seconds: bestLap,
    running_lap_seconds: running,
    last_crossing_at: lastCrossing,
  };
}

function buildLeaderboard(state, nowValue) {
  const items = state.teams.map(t => teamSnapshot(t, nowValue, state.phase));
  items.sort((a, b) => {
    if (b.laps_count !== a.laps_count) return b.laps_count - a.laps_count;
    const ac = a.last_crossing_at ?? Infinity;
    const bc = b.last_crossing_at ?? Infinity;
    if (ac !== bc) return ac - bc;
    return a.id - b.id;
  });
  items.forEach((row, i) => { row.rank = i + 1; });
  return items;
}

function buildChartsData(state) {
  if (!state.race_start_at) return { laps_over_time: [], lap_durations: [] };
  const start = state.race_start_at;
  const lapProgress = [];
  const lapDurations = [];
  for (const team of state.teams) {
    const lapPoints = [{ x: 0, y: 0 }];
    const lapDurationPoints = [];
    let lapCount = 0;
    for (const lap of team.laps) {
      lapCount++;
      const elapsedMinutes = Math.max(0, (lap.crossing_at - start) / 60);
      lapPoints.push({ x: elapsedMinutes, y: lapCount });
      lapDurationPoints.push({ x: elapsedMinutes, y: lap.duration_seconds });
    }
    lapProgress.push({ team_id: team.id, label: `#${team.number} ${team.name}`, points: lapPoints });
    lapDurations.push({ team_id: team.id, label: `#${team.number} ${team.name}`, points: lapDurationPoints });
  }
  return { laps_over_time: lapProgress, lap_durations: lapDurations };
}

function stateSnapshot(state) {
  const nowValue = nowTs();
  return {
    phase: state.phase,
    race_duration_seconds: state.race_duration_seconds,
    lap_distance_km: state.lap_distance_km,
    race_start_at: state.race_start_at,
    race_end_at: state.race_end_at,
    now: nowValue,
    teams: state.teams.map(t => teamSnapshot(t, nowValue, state.phase)),
    leaderboard: buildLeaderboard(state, nowValue),
    charts: buildChartsData(state),
    audit: state.audit.slice(-100),
  };
}

// mutation functions - validate, mutate state in place, return {ok, error?}

function applySetConfig(state, lapDistanceKm, raceDurationMinutes) {
  if (state.phase !== "registry") return { ok: false, error: "configuration can only be changed during registry phase" };
  if (isNaN(lapDistanceKm) || lapDistanceKm <= 0) return { ok: false, error: "lap distance must be > 0" };
  if (isNaN(raceDurationMinutes) || raceDurationMinutes <= 0) return { ok: false, error: "race duration must be > 0" };
  state.lap_distance_km = lapDistanceKm;
  state.race_duration_seconds = raceDurationMinutes * 60;
  pushAudit(state, "set-config", `config: ${lapDistanceKm} km, ${raceDurationMinutes} min`);
  return { ok: true };
}

function applyRegisterTeam(state, number, name) {
  number = parseInt(number, 10);
  name = String(name).trim();
  if (!name) return { ok: false, error: "team name is required" };
  if (!Number.isInteger(number) || number <= 0) return { ok: false, error: "team number must be an integer >= 1" };
  if (state.phase !== "registry") return { ok: false, error: "cannot add team outside registry phase" };
  if (state.teams.find(t => t.number === number)) return { ok: false, error: "team number already exists" };
  const teamId = state.next_team_id++;
  state.teams.push({ id: teamId, number, name, laps: [], lap_started_at: null });
  pushAudit(state, "register-team", `added team #${number} ${name}`);
  return { ok: true };
}

function applyRemoveTeam(state, teamId) {
  if (state.phase !== "registry") return { ok: false, error: "teams can only be removed during registry phase" };
  const team = findTeam(state, teamId);
  if (!team) return { ok: false, error: "team not found" };
  state.teams = state.teams.filter(t => t.id !== teamId);
  pushAudit(state, "remove-team", `removed team #${team.number} ${team.name}`);
  return { ok: true };
}

function applyStartRace(state) {
  if (state.phase !== "registry") return { ok: false, error: "race can only start from registry phase" };
  if (state.teams.length < 1) return { ok: false, error: "add at least one team before starting race" };
  const start = nowTs();
  state.phase = "race";
  state.race_start_at = start;
  state.race_end_at = null;
  for (const team of state.teams) {
    team.laps = [];
    team.lap_started_at = start;
  }
  pushAudit(state, "start-race", "race started");
  return { ok: true };
}

function applyIncrementLap(state, teamId) {
  if (state.phase !== "race") return { ok: false, error: "laps can only be added during race phase" };
  const team = findTeam(state, teamId);
  if (!team) return { ok: false, error: "team not found" };
  if (team.lap_started_at == null) return { ok: false, error: "team timer is not initialized" };
  addLap(team, nowTs() - team.lap_started_at, "button");
  pushAudit(state, "increment-lap", `team #${team.number} +1 lap`);
  return { ok: true };
}

function applyRevertLastLap(state, teamId) {
  const team = findTeam(state, teamId);
  if (!team) return { ok: false, error: "team not found" };
  if (!team.laps.length) return { ok: false, error: "no lap to revert for this team" };
  const removed = team.laps.pop();
  if (team.laps.length) {
    team.lap_started_at = team.laps[team.laps.length - 1].crossing_at;
  } else {
    team.lap_started_at = state.race_start_at ?? null;
  }
  pushAudit(state, "revert-last-lap", `team #${team.number} reverted lap (${removed.duration_seconds.toFixed(1)}s)`);
  return { ok: true };
}

function applyManualLap(state, teamId, durationSeconds) {
  if (state.phase !== "race") return { ok: false, error: "manual lap can only be added during race phase" };
  const team = findTeam(state, teamId);
  if (!team) return { ok: false, error: "team not found" };
  const duration = parseFloat(durationSeconds);
  if (isNaN(duration) || duration <= 0) return { ok: false, error: "duration must be > 0" };
  addLap(team, duration, "manual");
  pushAudit(state, "manual-lap", `team #${team.number} manual lap (${duration.toFixed(1)}s)`);
  return { ok: true };
}

function applyMagicLap(state, teamId) {
  if (state.phase !== "race") return { ok: false, error: "magic lap can only be added during race phase" };
  const team = findTeam(state, teamId);
  if (!team) return { ok: false, error: "team not found" };
  const mean = meanLapDurationForTeam(team) ?? meanLapDurationGlobal(state);
  if (mean == null) return { ok: false, error: "no lap data available yet to compute a mean duration" };
  addLap(team, mean, "magic");
  pushAudit(state, "magic-lap", `team #${team.number} magic lap (${mean.toFixed(1)}s)`);
  return { ok: true };
}

function applyFinishRace(state) {
  if (state.phase !== "race") return { ok: false, error: "race can only be finished from race phase" };
  state.phase = "finished";
  state.race_end_at = nowTs();
  for (const team of state.teams) team.lap_started_at = null;
  pushAudit(state, "finish-race", "race finished and results locked");
  return { ok: true };
}

function applyResetAll() {
  return newState();
}

// persistence and broadcast

const CHANNEL = new BroadcastChannel("tandem_race");

function loadState() {
  try {
    const saved = localStorage.getItem("tandem_race_raw");
    return saved ? JSON.parse(saved) : newState();
  } catch (_) {
    return newState();
  }
}

function saveAndBroadcast(state) {
  localStorage.setItem("tandem_race_raw", JSON.stringify(state));
  CHANNEL.postMessage(stateSnapshot(state));
}

// STATE is the live mutable state - used by operator, read on init by scoreboard
var STATE = loadState();

const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const SOURCE_PATH = path.join(__dirname, "..", "..", "static", "shared.js");
const SOURCE = fs.readFileSync(SOURCE_PATH, "utf8");

function makeFakeElement() {
  return { textContent: "" };
}

/** shared.js has no top-level side effects (only function declarations), so it's
 * safe to run the whole file in a sandboxed global context and pull the declared
 * functions off that context afterward. */
function loadSharedModule({ withClockEl = true, remainingCount = 1 } = {}) {
  const clockEl = withClockEl ? makeFakeElement() : null;
  const remainingEls = Array.from({ length: remainingCount }, makeFakeElement);

  const fakeDocument = {
    getElementById(id) {
      return id === "race-clock-elapsed" ? clockEl : null;
    },
    querySelectorAll(selector) {
      return selector === ".js-remaining-time" ? remainingEls : [];
    },
  };

  const sandbox = { document: fakeDocument, fetch: async () => ({ json: async () => ({}) }) };
  vm.createContext(sandbox);
  vm.runInContext(SOURCE, sandbox, { filename: SOURCE_PATH });

  return { formatSeconds: sandbox.formatSeconds, renderClock: sandbox.renderClock, clockEl, remainingEls };
}

test("formatSeconds: null/undefined render as placeholder", () => {
  const { formatSeconds } = loadSharedModule();
  assert.equal(formatSeconds(null), "--");
  assert.equal(formatSeconds(undefined), "--");
});

test("formatSeconds: zero and sub-minute values", () => {
  const { formatSeconds } = loadSharedModule();
  assert.equal(formatSeconds(0), "00:00:00");
  assert.equal(formatSeconds(45), "00:00:45");
});

test("formatSeconds: sub-hour and multi-hour values", () => {
  const { formatSeconds } = loadSharedModule();
  assert.equal(formatSeconds(125), "00:02:05");
  assert.equal(formatSeconds(3661), "01:01:01");
  assert.equal(formatSeconds(36000), "10:00:00");
});

test("formatSeconds: negative values clamp to zero", () => {
  const { formatSeconds } = loadSharedModule();
  assert.equal(formatSeconds(-50), "00:00:00");
});

test("formatSeconds: fractional seconds are floored", () => {
  const { formatSeconds } = loadSharedModule();
  assert.equal(formatSeconds(59.9), "00:00:59");
});

test("renderClock: no race started yet shows Waiting everywhere", () => {
  const { renderClock, clockEl, remainingEls } = loadSharedModule({ remainingCount: 2 });
  renderClock({ race_start_at: null });
  assert.equal(clockEl.textContent, "Waiting");
  assert.equal(remainingEls[0].textContent, "Waiting");
  assert.equal(remainingEls[1].textContent, "Waiting");
});

test("renderClock: during race phase, elapsed counts from race_start_at to now", () => {
  const { renderClock, clockEl, remainingEls } = loadSharedModule();
  renderClock({
    phase: "race",
    race_start_at: 1000,
    now: 1090,
    race_duration_seconds: 600,
  });
  assert.equal(clockEl.textContent, "00:01:30"); // 90s elapsed
  assert.equal(remainingEls[0].textContent, "00:08:30"); // 600 - 90
});

test("renderClock: finished phase uses race_end_at, not now, for elapsed", () => {
  const { renderClock, clockEl } = loadSharedModule();
  renderClock({
    phase: "finished",
    race_start_at: 1000,
    race_end_at: 1300,
    now: 999999, // must be ignored once the race has finished
    race_duration_seconds: 600,
  });
  assert.equal(clockEl.textContent, "00:05:00"); // 300s elapsed, frozen at race_end_at
});

test("renderClock: remaining never goes negative once overtime is reached", () => {
  const { renderClock, remainingEls } = loadSharedModule();
  renderClock({
    phase: "race",
    race_start_at: 1000,
    now: 5000,
    race_duration_seconds: 600,
  });
  assert.equal(remainingEls[0].textContent, "00:00:00");
});

test("renderClock: does nothing and does not throw when no matching elements exist", () => {
  const { renderClock } = loadSharedModule({ withClockEl: false, remainingCount: 0 });
  assert.doesNotThrow(() => renderClock({ race_start_at: null }));
});

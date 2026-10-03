const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const OPERATOR_PATH = path.join(__dirname, "..", "..", "static", "operator.js");
const SHARED_PATH = path.join(__dirname, "..", "..", "static", "shared.js");
const OPERATOR_SOURCE = fs.readFileSync(OPERATOR_PATH, "utf8");
const SHARED_SOURCE = fs.readFileSync(SHARED_PATH, "utf8");

/** operator.js wires ~20 addEventListener calls directly at the top level against
 * real element IDs, so executing the whole file would need a near-complete DOM.
 * Instead (same approach as scoreboard.test.js) we slice out just the rendering
 * functions we want to test, by balanced-brace matching, and run only those. */
function extractFunctionSource(source, name, sourcePathForError) {
  const marker = `function ${name}(`;
  const start = source.indexOf(marker);
  if (start === -1) {
    throw new Error(`could not find function ${name} in ${sourcePathForError}`);
  }
  let depth = 0;
  let bodyStarted = false;
  for (let i = start; i < source.length; i += 1) {
    const char = source[i];
    if (char === "{") {
      depth += 1;
      bodyStarted = true;
    } else if (char === "}") {
      depth -= 1;
      if (bodyStarted && depth === 0) {
        return source.slice(start, i + 1);
      }
    }
  }
  throw new Error(`unbalanced braces while extracting function ${name}`);
}

/** Extracts a single `let`/`const` declaration line and rewrites it to `var` so it
 * becomes a settable/readable property on the vm sandbox object (plain `let`/`const`
 * top-level bindings run via vm.runInContext do NOT attach to the context object). */
function extractDeclarationAsVar(source, marker) {
  const start = source.indexOf(marker);
  if (start === -1) {
    throw new Error(`could not find "${marker}" in ${OPERATOR_PATH}`);
  }
  const end = source.indexOf(";", start);
  return source.slice(start, end + 1).replace(/^(let|const)\b/, "var");
}

function makeClassList() {
  const classes = new Set();
  return {
    add: (c) => classes.add(c),
    remove: (c) => classes.delete(c),
    contains: (c) => classes.has(c),
    toggle(c, force) {
      const shouldHave = force === undefined ? !classes.has(c) : Boolean(force);
      if (shouldHave) classes.add(c); else classes.delete(c);
      return shouldHave;
    },
  };
}

function makeElement({ withQuerySelectorButton = false } = {}) {
  const el = {
    textContent: "",
    innerHTML: "",
    value: "",
    disabled: false,
    classList: makeClassList(),
  };
  if (withQuerySelectorButton) {
    el.querySelector = () => makeElement();
  }
  return el;
}

const ELEMENT_IDS = [
  "error-box",
  "manual-team-id",
  "magic-team-id",
  "edit-team-id",
  "lap-editor-preview",
  "lap-editor-pending",
  "lap-editor-confirm-btn",
  "lap-editor-laps",
  "audit-list",
  "teams-body",
  "phase-pill",
  "save-config-btn",
  "start-race-btn",
  "finish-race-btn",
  "manual-lap-form",
  "magic-lap-form",
  "registry-setup-group",
  "registry-summary-card",
  "registry-summary-text",
  "lap-distance",
  "race-duration",
  "auto-scroll-btn",
  "lap-preview-current-rank",
  "lap-preview-current-laps",
  "lap-preview-current-last",
  "lap-preview-current-best",
  "lap-preview-new-rank",
  "lap-preview-new-laps",
  "lap-preview-new-last",
  "lap-preview-new-best",
];
const FORM_IDS_WITH_BUTTON = ["register-form", "manual-lap-form", "magic-lap-form"];

function makeDocumentStub() {
  const elements = {};
  for (const id of ELEMENT_IDS) {
    elements[id] = makeElement();
  }
  for (const id of FORM_IDS_WITH_BUTTON) {
    elements[id] = makeElement({ withQuerySelectorButton: true });
  }
  return {
    getElementById(id) {
      return elements[id] || null;
    },
    elements,
  };
}

const RENDER_FUNCTION_NAMES = [
  "setError",
  "updateTeamSelects",
  "hideLapPreview",
  "resetLapEditor",
  "updateConfirmButtonLabel",
  "renderPendingSummary",
  "renderLapEditorLaps",
  "buildEditsPayload",
  "renderAudit",
  "renderTable",
  "updatePhaseControls",
];

function loadOperatorModule(documentStub) {
  const pieces = [
    extractFunctionSource(SHARED_SOURCE, "formatSeconds", SHARED_PATH),
    extractDeclarationAsVar(OPERATOR_SOURCE, "let configDirty"),
    extractDeclarationAsVar(OPERATOR_SOURCE, "let editorTeamId"),
    extractDeclarationAsVar(OPERATOR_SOURCE, "let editorLaps"),
    extractDeclarationAsVar(OPERATOR_SOURCE, "const pendingEdits"),
    ...RENDER_FUNCTION_NAMES.map((name) => extractFunctionSource(OPERATOR_SOURCE, name, OPERATOR_PATH)),
  ].join("\n");

  const sandbox = { document: documentStub };
  vm.createContext(sandbox);
  vm.runInContext(pieces, sandbox, { filename: OPERATOR_PATH });
  return sandbox;
}

test("setError: writes the message into the error box, empty string clears it", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.setError("boom");
  assert.equal(doc.elements["error-box"].textContent, "boom");
  mod.setError("");
  assert.equal(doc.elements["error-box"].textContent, "");
  mod.setError(undefined);
  assert.equal(doc.elements["error-box"].textContent, "");
});

test("updateTeamSelects: renders one option per team into all three selects", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.updateTeamSelects([
    { id: 1, number: 1, name: "Alpha" },
    { id: 2, number: 2, name: "Bravo" },
  ]);
  for (const id of ["manual-team-id", "magic-team-id"]) {
    assert.match(doc.elements[id].innerHTML, /#1 Alpha/);
    assert.match(doc.elements[id].innerHTML, /#2 Bravo/);
  }
  assert.match(doc.elements["edit-team-id"].innerHTML, /Select a team/);
});

test("updateTeamSelects: preserves the previously selected value", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  doc.elements["manual-team-id"].value = "2";
  mod.updateTeamSelects([{ id: 2, number: 2, name: "Bravo" }]);
  assert.equal(doc.elements["manual-team-id"].value, "2");
});

test("hideLapPreview: hides both the preview and pending panels", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.hideLapPreview();
  assert.ok(doc.elements["lap-editor-preview"].classList.contains("is-hidden"));
  assert.ok(doc.elements["lap-editor-pending"].classList.contains("is-hidden"));
});

test("resetLapEditor: clears pending edits and hides the preview panels", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.pendingEdits.set(0, { action: "remove" });
  mod.resetLapEditor();
  assert.equal(mod.pendingEdits.size, 0);
  assert.ok(doc.elements["lap-editor-preview"].classList.contains("is-hidden"));
});

test("updateConfirmButtonLabel: singular vs plural wording, disabled when empty", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.updateConfirmButtonLabel();
  assert.equal(doc.elements["lap-editor-confirm-btn"].textContent, "Confirm change");
  assert.equal(doc.elements["lap-editor-confirm-btn"].disabled, true);

  mod.pendingEdits.set(0, { action: "remove" });
  mod.updateConfirmButtonLabel();
  assert.equal(doc.elements["lap-editor-confirm-btn"].textContent, "Confirm change");
  assert.equal(doc.elements["lap-editor-confirm-btn"].disabled, false);

  mod.pendingEdits.set(1, { action: "remove" });
  mod.updateConfirmButtonLabel();
  assert.equal(doc.elements["lap-editor-confirm-btn"].textContent, "Confirm 2 changes");
});

test("renderPendingSummary: hides itself when there are no pending edits", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderPendingSummary();
  assert.ok(doc.elements["lap-editor-pending"].classList.contains("is-hidden"));
  assert.equal(doc.elements["lap-editor-pending"].innerHTML, "");
});

test("renderPendingSummary: describes an edit as old -> new duration", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.editorLaps = [{ index: 0, duration_seconds: 30.0, source: "button +1" }];
  mod.pendingEdits.set(0, { action: "edit", new_duration: 45.5 });
  mod.renderPendingSummary();
  assert.match(doc.elements["lap-editor-pending"].innerHTML, /30\.0s -&gt; <strong>45\.5s<\/strong>/);
});

test("renderPendingSummary: describes a removal", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.pendingEdits.set(2, { action: "remove" });
  mod.renderPendingSummary();
  assert.match(doc.elements["lap-editor-pending"].innerHTML, /Lap 3: will be <strong>removed<\/strong>/);
});

test("renderLapEditorLaps: shows a placeholder when the team has no laps", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.editorLaps = [];
  mod.renderLapEditorLaps();
  assert.match(doc.elements["lap-editor-laps"].innerHTML, /No laps recorded/);
});

test("renderLapEditorLaps: marks a pending removal as disabled with a Removed badge", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.editorLaps = [{ index: 0, duration_seconds: 12.0, source: "manual" }];
  mod.pendingEdits.set(0, { action: "remove" });
  mod.renderLapEditorLaps();
  const html = doc.elements["lap-editor-laps"].innerHTML;
  assert.match(html, /is-removed/);
  assert.match(html, /Removed/);
  assert.match(html, /disabled/);
});

test("renderLapEditorLaps: marks a pending edit as Changed and shows the new value", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.editorLaps = [{ index: 0, duration_seconds: 12.0, source: "manual" }];
  mod.pendingEdits.set(0, { action: "edit", new_duration: 20.0 });
  mod.renderLapEditorLaps();
  const html = doc.elements["lap-editor-laps"].innerHTML;
  assert.match(html, /is-edited/);
  assert.match(html, /Changed/);
  assert.match(html, /value="20\.0"/);
});

test("buildEditsPayload: maps pending edits/removals into the API shape", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.pendingEdits.set(1, { action: "edit", new_duration: 15.5 });
  mod.pendingEdits.set(0, { action: "remove" });
  const payload = mod.buildEditsPayload();
  // buildEditsPayload runs inside the vm sandbox, so the returned array/objects
  // belong to that realm - JSON round-trip normalizes them to host-realm plain
  // values before comparing (strict deepEqual otherwise fails on prototype identity)
  assert.deepEqual(JSON.parse(JSON.stringify(payload)), [
    { lap_index: 1, action: "edit", new_duration: 15.5 },
    { lap_index: 0, action: "remove", new_duration: null },
  ]);
});

test("renderAudit: shows a placeholder when there is no history yet", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderAudit([]);
  assert.match(doc.elements["audit-list"].innerHTML, /No action yet/);
});

test("renderAudit: renders newest entry first", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderAudit([
    { at: 1_700_000_000, action: "register-team", message: "added team #1 Alpha" },
    { at: 1_700_000_100, action: "start-race", message: "race started" },
  ]);
  const html = doc.elements["audit-list"].innerHTML;
  assert.ok(html.indexOf("race started") < html.indexOf("added team #1 Alpha"));
});

test("renderTable: shows a placeholder row when no team is registered", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderTable({ phase: "registry", leaderboard: [] });
  assert.match(doc.elements["teams-body"].innerHTML, /No team registered/);
});

test("renderTable: race phase shows +1/Revert but not Remove", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderTable({
    phase: "race",
    leaderboard: [
      { id: 1, rank: 1, number: 1, name: "Alpha", laps_count: 3, running_lap_seconds: 12, last_lap_seconds: 30, best_lap_seconds: 25 },
    ],
  });
  const html = doc.elements["teams-body"].innerHTML;
  assert.match(html, /data-action="inc"/);
  assert.match(html, /data-action="revert"/);
  assert.doesNotMatch(html, /data-action="remove"/);
});

test("renderTable: registry phase shows Remove but not +1/Revert", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.renderTable({
    phase: "registry",
    leaderboard: [
      { id: 1, rank: 1, number: 1, name: "Alpha", laps_count: 0, running_lap_seconds: null, last_lap_seconds: null, best_lap_seconds: null },
    ],
  });
  const html = doc.elements["teams-body"].innerHTML;
  assert.match(html, /data-action="remove"/);
  assert.doesNotMatch(html, /data-action="inc"/);
  assert.doesNotMatch(html, /data-action="revert"/);
});

test("updatePhaseControls: registry phase enables setup controls and shows the setup group", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.updatePhaseControls({
    phase: "registry",
    race_duration_seconds: 10800,
    lap_distance_km: 9,
    teams: [],
    auto_scroll: false,
  });
  assert.equal(doc.elements["phase-pill"].textContent, "phase: registry");
  assert.equal(doc.elements["save-config-btn"].disabled, false);
  assert.equal(doc.elements["start-race-btn"].disabled, false);
  assert.equal(doc.elements["finish-race-btn"].disabled, true);
  assert.equal(doc.elements["registry-setup-group"].classList.contains("is-hidden"), false);
  assert.equal(doc.elements["registry-summary-card"].classList.contains("is-hidden"), true);
});

test("updatePhaseControls: race phase disables setup controls and shows the summary card", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.updatePhaseControls({
    phase: "race",
    race_duration_seconds: 5400,
    lap_distance_km: 5,
    teams: [{ id: 1 }, { id: 2 }],
    auto_scroll: true,
  });
  assert.equal(doc.elements["save-config-btn"].disabled, true);
  assert.equal(doc.elements["start-race-btn"].disabled, true);
  assert.equal(doc.elements["finish-race-btn"].disabled, false);
  assert.equal(doc.elements["registry-setup-group"].classList.contains("is-hidden"), true);
  assert.equal(doc.elements["registry-summary-card"].classList.contains("is-hidden"), false);
  assert.match(doc.elements["registry-summary-text"].textContent, /5 km \/ 90 min \/ 2 teams/);
  assert.equal(doc.elements["auto-scroll-btn"].textContent, "Auto-scroll leaderboard: ON");
});

test("updatePhaseControls: does not overwrite the config inputs while the user is editing them", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  doc.elements["lap-distance"].value = "not-yet-saved";
  mod.configDirty = true;
  mod.updatePhaseControls({ phase: "registry", race_duration_seconds: 10800, lap_distance_km: 9, teams: [], auto_scroll: false });
  assert.equal(doc.elements["lap-distance"].value, "not-yet-saved");
});

test("updatePhaseControls: leaving race phase resets the lap editor selection", () => {
  const doc = makeDocumentStub();
  const mod = loadOperatorModule(doc);
  mod.editorTeamId = 7;
  mod.editorLaps = [{ index: 0, duration_seconds: 10, source: "manual" }];
  mod.updatePhaseControls({ phase: "finished", race_duration_seconds: 10800, lap_distance_km: 9, teams: [], auto_scroll: false });
  assert.equal(doc.elements["edit-team-id"].disabled, true);
  assert.equal(mod.editorTeamId, null);
  assert.equal(mod.editorLaps.length, 0);
});

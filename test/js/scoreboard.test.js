const test = require("node:test");
const assert = require("node:assert/strict");
const vm = require("node:vm");
const fs = require("node:fs");
const path = require("node:path");

const SOURCE_PATH = path.join(__dirname, "..", "..", "static", "scoreboard.js");
const SOURCE = fs.readFileSync(SOURCE_PATH, "utf8");

/** scoreboard.js runs `refreshState()` and `window.setInterval(...)` at the top
 * level, which would require stubbing Chart.js + a fetch loop just to load the
 * file at all. teamColor/toDatasets are pure, so instead of executing the whole
 * file, slice out just those two function declarations by balanced-brace
 * matching and evaluate only that in an isolated context. */
function extractFunctionSource(source, name) {
  const marker = `function ${name}(`;
  const start = source.indexOf(marker);
  if (start === -1) {
    throw new Error(`could not find function ${name} in ${SOURCE_PATH}`);
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

function loadPureHelpers() {
  const wrapped = `${extractFunctionSource(SOURCE, "teamColor")}\n${extractFunctionSource(SOURCE, "toDatasets")}\n({ teamColor, toDatasets });`;
  return vm.runInNewContext(wrapped, {}, { filename: SOURCE_PATH });
}

test("teamColor: single team gets the fixed top-of-scale hue", () => {
  const { teamColor } = loadPureHelpers();
  assert.equal(teamColor(0, 1), "hsl(270, 80%, 45%)");
});

test("teamColor: first and last of several teams sit at the hue boundaries", () => {
  const { teamColor } = loadPureHelpers();
  assert.equal(teamColor(0, 5), "hsl(270, 80%, 45%)");
  assert.equal(teamColor(4, 5), "hsl(0, 80%, 45%)");
});

test("teamColor: middle index lands between the boundaries", () => {
  const { teamColor } = loadPureHelpers();
  const color = teamColor(2, 5);
  assert.match(color, /^hsl\(\d+, 80%, 45%\)$/);
  assert.notEqual(color, "hsl(270, 80%, 45%)");
  assert.notEqual(color, "hsl(0, 80%, 45%)");
});

test("toDatasets: maps label/points through and assigns a color per series", () => {
  const { toDatasets } = loadPureHelpers();
  const series = [
    { team_id: 1, label: "#1 Alpha", points: [{ x: 0, y: 0 }] },
    { team_id: 2, label: "#2 Bravo", points: [{ x: 0, y: 0 }, { x: 1, y: 1 }] },
  ];
  const datasets = toDatasets(series);

  assert.equal(datasets.length, 2);
  assert.equal(datasets[0].label, "#1 Alpha");
  assert.deepEqual(datasets[0].data, series[0].points);
  assert.equal(datasets[1].label, "#2 Bravo");
  assert.deepEqual(datasets[1].data, series[1].points);
  // same color used for borderColor and backgroundColor, distinct between series
  assert.equal(datasets[0].borderColor, datasets[0].backgroundColor);
  assert.notEqual(datasets[0].borderColor, datasets[1].borderColor);
});

test("toDatasets: empty series list returns an empty dataset list", () => {
  const { toDatasets } = loadPureHelpers();
  assert.deepEqual(toDatasets([]), []);
});

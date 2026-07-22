# tandem race app

simple tandem race app with two pages:
- operator page: `http://localhost:8080/`
- scoreboard page: `http://localhost:8080/scoreboard`

## run

```bash
python app.py
```

## features

- phase 1 registry: add teams with number and name
- phase 2 race:
  - start race (3h)
  - +1 lap per team
  - revert last lap per team
  - manual lap entry with duration
  - magic lap entry using mean lap duration
- phase 3 finish:
  - finish race and lock results
  - final charts:
    - laps over time
    - lap duration over time

## notes

- state is in-memory only in v1 (restart resets race data)
- backend is python (bottle), frontend is html/css with lightweight js polling

---
# simplist local

Replace the Python/Bottle backend with a state.js file holding all business logic, state, and BroadcastChannel broadcasting. The operator mutates state directly; the scoreboard listens. A minimal server.py (~15 lines, stdlib only) replaces app.py just to serve static files. All render functions stay unchanged — only how state is produced and distributed changes.

- static/state.js	new — all business logic, state schema, mutations, BroadcastChannel, localStorage
- static/operator.js	rewritten — no fetch, calls apply*() directly, synchronous handlers
- static/scoreboard.js	rewritten — no polling, BroadcastChannel listener + localStorage init, local clock tick
- static/operator.html	added <script src="/static/state.js">
- static/scoreboard.html	added <script src="/static/state.js">
- server.py	new — 20 lines, stdlib only, python server.py to start
- app.py	still present but unused — delete when ready


Start with python server.py (no uv, no dependencies). Open http://localhost:8094 for operator, http://localhost:8094/scoreboard in a second window for scoreboard.
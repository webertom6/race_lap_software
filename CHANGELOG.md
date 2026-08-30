# main
## context
First development cycle, from the initial Bottle scaffold through styling, leaderboard polish, backend features, a responsive/mobile pass, a module-split refactor, and the auto-scroll feature. This is the exact version delivered to the client for their first live event.

## changes

### initial scaffold
date : 2026-07-16

- branch : `main` (direct commit)
- changes : first working version - Bottle backend serving two static pages (operator control panel, public scoreboard) with a basic leaderboard and phase model
- impact files : `app.py` (single-file backend with all routes + state), `static/operator.html`/`operator.js`, `static/scoreboard.html`/`scoreboard.js`, `static/style.css` all created from scratch; `requirements.txt` for dependencies
- fix : removed a stray compiled `.pyc` file that had been committed by mistake and added it to `.gitignore`

### visual redesign and clock robustness
date : 2026-07-17

- branch : `main` (direct commit)
- changes : large first styling pass (colors, layout, typography) replacing the initial look, plus a first `.github/copilot-instructions.md`; fixed elapsed/remaining clock rendering
- impact files : `static/style.css` (major rewrite), `static/operator.html`/`scoreboard.html` (markup adjusted for the new style), `static/operator.js`/`scoreboard.js` (guard against missing clock elements)
- fix : `TypeError: Cannot set properties of null (setting 'textContent')` when a clock element didn't exist on a given page - added existence checks before every `textContent` write

### leaderboard display polish
date : 2026-07-18

- branch : `main` (direct commit)
- changes : several small leaderboard refinements - hid the row-number/team-count column, restyled the reset/important buttons, tuned timer font and CSS specificity, added color highlighting for the best lap and a color spectrum across chart series, added a row hover effect
- impact files : `static/scoreboard.js` (leaderboard rendering and chart coloring), `static/style.css` (button/timer/hover styling), `static/operator.html` (reset button markup)
- fix : none reported

### backend features and dev tooling
date : 2026-07-18

- branch : `main` (direct commit)
- changes : migrated dependency management to `uv`, added a remove-team endpoint, made lap distance/race duration configurable via API, switched the server to multi-threaded Waitress, and added a small `pyautogui` script to auto-fill team registration while manually testing
- impact files : `app.py` (new routes, threaded `serve()` call), `pyproject.toml`/`uv.lock` (uv migration), `filling_team_kb.py` (new dev-only script), `static/operator.js`/`operator.html` (config form and remove-team wiring)
- fix : none reported

### charts behavior
date : 2026-07-18

- branch : `main` (direct commit)
- changes : stopped re-rendering the post-race charts on every poll once already drawn, and generated a distinct color per team across a spectrum instead of a fixed palette
- impact files : `static/scoreboard.js` (chart render-once guard, per-team color generation)
- fix : none reported

### request logging
date : 2026-07-22

- branch : `main` (direct commit)
- changes : added basic request logging to the backend for visibility during operation
- impact files : `app.py` (logging setup), `pyproject.toml`/`uv.lock` (logging dependency)
- fix : none reported

### mobile/TV responsive pass and QR access
date : 2026-08-06 to 2026-08-07

- branch : `main` (direct commit)
- changes : made the operator console usable on phones/tablets (fixed overflow and oversized cards below Mobile L), scaled up scoreboard typography for large TV displays, added LAN IP + ASCII QR code printing at server startup for quick device access
- impact files : `static/style.css` (responsive breakpoints, 4K scoreboard type scale), `app.py` (QR/LAN IP printing at startup)
- fix : operator card layout overflowing/oversized below the Mobile L (425px) breakpoint, and header overflow at narrow widths

### touch-friendly lap buttons
date : 2026-08-07

- branch : `fix/phone_layout_style`, merged into `main` via PR #1 on 2026-08-07
- changes : adjusted the +1/revert buttons and their press feedback for mobile/laptop touch use
- impact files : `static/operator.html`/`operator.js` (button markup/behavior), `static/style.css` (touch button styling)
- fix : none reported

### licensing and install docs
date : 2026-08-07

- branch : `main` (direct commit)
- changes : added an MIT license and expanded the README with full install/usage instructions
- impact files : `LICENSE` (new), `README.md` (expanded)
- fix : none reported

> `develop` merged into `main` via PR #2 on 2026-08-07 - no unique changes beyond what's listed above; this was a sync point confirming the branch was ready to fold back in

### shared JS/CSS refactor
date : 2026-08-08 to 2026-08-09

- branch : `main` (direct commit)
- changes : extracted duplicated clock-rendering code into a shared `static/shared.js`, and reorganized `style.css`/`scoreboard.html` for clarity
- impact files : `static/shared.js` (new, shared code), `static/style.css`/`scoreboard.html`/`operator.html` (reorganization)
- fix : none reported

### backend module split
date : 2026-08-09

- branch : `feature/refactoring_simplicty`, merged into `main` via PR #3 on 2026-08-09
- changes : split the single-file `app.py` backend into dedicated modules for state, routes, and network helpers
- impact files : `app.py` (shrunk to composition root), `race_state.py`/`api_handlers.py`/`network.py` (new - state model, routes, and network/QR helpers respectively)
- fix : none reported

### project rename
date : 2026-08-09

- branch : `feature/change_name`, merged into `main` via PR #4 on 2026-08-09
- changes : renamed the project to a more generic name
- impact files : `README.md`
- fix : none reported

> `develop` merged into `main` via PR #5 on 2026-08-09 - no unique changes beyond what's listed above; this was the sync point right before the client-delivered version

### auto-scroll leaderboard (delivered milestone)
date : 2026-08-22

- branch : `main` (direct commit)
- changes : added an operator-toggled auto-scroll for the public scoreboard so an unattended display scrolls on its own; this is the version delivered to the client for first real-world use
- impact files : `static/scoreboard.js` (scroll loop via `requestAnimationFrame`, teleports back to top on reaching the bottom), `static/operator.js`/`operator.html` (toggle button + state wiring), `api_handlers.py` (`POST /api/toggle-auto-scroll`), `race_state.py` (`auto_scroll` field persisted in the snapshot), `static/style.css` (toggle button active state)
- fix : none reported

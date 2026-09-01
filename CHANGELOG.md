# main
## context
First development cycle, from the initial Bottle scaffold through styling, leaderboard polish, backend features, a responsive/mobile pass, a module-split refactor, and the auto-scroll feature. This is the exact version delivered to the client for their first live event.

Second cycle, starting right after that delivery: post-event corrections (`feature/correction_post_1stused`, PR #6 - export/import state, autosave, team-data editing, imported-state timer fix) tagged as `v1.0.0` on `main`, followed by an ongoing design-cleaning pass (`feature/design_cleaning`, not yet merged - operator layout rework, an impeccable-generated design system, repo/codebase cleanup, and non-technical install-and-run launcher scripts with a colored ASCII banner).

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

> `main`'s auto-scroll commit merged into `develop` via commit `604d043` on 2026-08-26 - no unique changes, sync point so post-delivery correction work could branch off with auto-scroll included

### venv naming, localhost QR, scroll speed tweaks
date : 2026-08-28

- branch : `feature/correction_post_1stused`
- changes : renamed the local venv reference, pointed the QR code at the localhost variant, tuned auto-scroll speed
- impact files : `app.py`, `pyproject.toml`/`uv.lock`, `static/scoreboard.js` (scroll speed)
- fix : none reported

### auto scroll up and down
date : 2026-08-29

- branch : `feature/correction_post_1stused`
- changes : extended the auto-scroll loop to reverse direction and scroll back up instead of only teleporting to the top
- impact files : `static/scoreboard.js`
- fix : none reported

### QR code of the project added
date : 2026-08-29

- branch : `feature/correction_post_1stused`
- changes : added a project QR code route/display, tightened shared clock code and scoreboard markup
- impact files : `api_handlers.py` (new QR route), `static/scoreboard.html`, `static/shared.js`, `static/style.css`, `pyproject.toml`/`uv.lock`
- fix : none reported

### export and import state
date : 2026-08-29

- branch : `feature/correction_post_1stused`
- changes : implemented exporting/importing the full race state as a file, with operator UI controls to trigger both
- impact files : `api_handlers.py`/`race_state.py` (export/import logic), `static/operator.html`/`operator.js` (controls), `static/style.css`
- fix : none reported

### sticky table-wrap column tile
date : 2026-08-29

- branch : `feature/correction_post_1stused`
- changes : made a leaderboard table column stick in place while the table scrolls
- impact files : `static/style.css`
- fix : none reported

### sticky footer with GitHub link and remaining clock
date : 2026-08-30

- branch : `feature/correction_post_1stused`
- changes : added a sticky footer showing a GitHub link and the remaining-time clock; dropped the stale `requirements.txt`
- impact files : `app.py`, `requirements.txt` (removed), `static/operator.html`, `static/scoreboard.html`, `static/shared.js`, `static/style.css`
- fix : none reported

### editing team data tool
date : 2026-08-30

- branch : `feature/correction_post_1stused`
- changes : added an operator tool to edit a team's recorded lap data directly - new API handlers, race-state logic, and an operator UI form
- impact files : `api_handlers.py`, `race_state.py`, `static/operator.html`/`operator.js` (new editing form), `static/style.css`
- fix : none reported

### autosave mechanism
date : 2026-08-30

- branch : `feature/correction_post_1stused`
- changes : added `autosave.py` and wired state-change-triggered autosave to disk, to prevent data loss on a crash
- impact files : `.gitignore` (ignore autosave file), `app.py`, `autosave.py` (new), `race_state.py`
- fix : none reported

### fix still-running timer on imported state
date : 2026-08-30

- branch : `feature/correction_post_1stused`, merged into `develop` via PR #6 on 2026-08-30
- changes : fixed the elapsed/remaining timer continuing from the wrong reference point after importing a saved race-state file
- impact files : `api_handlers.py`, `app.py`, `autosave.py`, `race_state.py`
- fix : imported race-state files kept the timer running from the current time instead of respecting the imported elapsed time

> `develop` merged `main` back in via `e658e8a` on 2026-08-31 (picks up the `add changelog` commit below) - no unique changes

### delete top QR code for now
date : 2026-08-30

- branch : `feature/design_cleaning`
- changes : removed the top-of-page QR code from the scoreboard, temporarily
- impact files : `static/scoreboard.html`, `static/style.css`
- fix : none reported

### fix blocked auto scroll
date : 2026-08-30

- branch : `feature/design_cleaning`
- changes : fixed the auto-scroll loop getting stuck and no longer advancing under some conditions
- impact files : `static/scoreboard.js`
- fix : auto-scroll could get blocked and stop advancing

### operator layout rework, locked setup params, sticky phase controls
date : 2026-08-30

- branch : `feature/design_cleaning`
- changes : reorganized the operator page cards, locked setup parameters once a race starts, made phase controls sticky
- impact files : `static/operator.html`/`operator.js`, `static/style.css`
- fix : none reported

### background discontinuity and detached sticky head fix
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : fixed a visible page/card background color seam and the leaderboard's sticky header visually detaching while scrolling
- impact files : `static/style.css`
- fix : background color discontinuity and sticky table header detaching during scroll

### tab icon
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : added a favicon/tab icon to both operator and scoreboard pages
- impact files : `static/logo_charneux.svg` (new), `static/operator.html`, `static/scoreboard.html`
- fix : none reported

### remove old tandem name
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : removed leftover references to the project's earlier "tandem" name from copilot instructions and page markup
- impact files : `.github/copilot-instructions.md`, `static/operator.html`, `static/scoreboard.html`
- fix : none reported

> `develop` (now including `main`'s `add changelog` commit, tagged `v1.0.0`) merged into `feature/design_cleaning` via commit `47f5796` on 2026-08-31

### impeccable design system and product docs
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : ran the impeccable skill's init to generate `PRODUCT.md` and `DESIGN.md` (the "Timing Booth Console" design system) plus its sidecar config
- impact files : `DESIGN.md` (new), `PRODUCT.md` (new), `.impeccable/design.json` (new), `.impeccable/live/config.json` (new)
- fix : none reported

### codebase cleanup, ruff lint
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : removed the dev-only `pyautogui` team-filling script, tightened ruff config, small lint fixes across backend and frontend
- impact files : `filling_team_kb.py` (removed), `.github/copilot-instructions.md`, `api_handlers.py`, `pyproject.toml`, `race_state.py`, `static/operator.html`/`scoreboard.html`/`shared.js`/`style.css`, `uv.lock`
- fix : none reported

### install-and-run launcher scripts (Windows/macOS/Linux)
date : 2026-08-31

- branch : `feature/design_cleaning`
- changes : added double-click launcher entry points for non-technical users (`run-windows.bat`, `run-macos.command`, `run-linux.sh`) that install `uv` if missing, run `uv sync`, launch the app, and auto-open the browser once the server is ready; added a first ASCII logo/name banner; documented the quick-start in the README
- impact files : `app.py` (browser-auto-open, gated behind a `RACE_LAP_LAUNCHER` env var so it never fires on a plain `uv run app.py`), `README.md` (install/run quick-start), `ascii/ascii-logo.txt`/`ascii-name.txt` (new), `run-windows.bat`/`run-macos.command`/`run-linux.sh` (new), `.gitattributes` (forces LF on `.sh`/`.command`, CRLF on the `.bat`)
- fix : none reported

### ASCII logo fix and rainbow name
date : 2026-09-01

- branch : `feature/design_cleaning`
- changes : swapped the ASCII logo to a Braille dot-matrix version, added a rotating rainbow ANSI gradient to the name banner
- impact files : `ascii/ascii-logo.txt`, `scripts/print-logo.ps1` (new), `scripts/print-rainbow-name.ps1`/`.sh` (new), `run-windows.bat`/`run-macos.command`/`run-linux.sh`, `.gitignore`
- fix : the Braille dot logo displayed as garbled/mojibake text on Windows terminals even after `chcp 65001` - root cause was `cmd.exe`'s `type` command (not the encoding itself); fixed by printing the logo through PowerShell's own UTF-8 file read instead

### blue-to-white gradient logo and red warning text
date : 2026-09-01

- branch : `feature/design_cleaning`
- changes : replaced the flat logo print with a top-to-bottom blue-to-white gradient (smoothstep-eased, matching the app's action-blue brand color), added a bold alert-red warning about not clicking inside the console window, centered the logo, replaced the redundant plain "Race Lap App" text line with a one-line tagline
- impact files : `scripts/print-gradient-logo.ps1`/`.sh` (new), `scripts/print-warning.ps1` (new), `ascii/ascii-logo.txt`/`ascii-name.txt`, `run-windows.bat`/`run-macos.command`/`run-linux.sh`, `README.md`
- fix : none reported

### clearer repo root - server/ package
date : 2026-09-01

- branch : `feature/design_cleaning`
- changes : moved the backend modules (`api_handlers.py`, `autosave.py`, `network.py`, `race_state.py`) into a new `server/` package, keeping `app.py` as the sole root-level launcher, to reduce root-level clutter
- impact files : `app.py`, `server/__init__.py` (new), `server/api_handlers.py`/`autosave.py`/`network.py`/`race_state.py` (moved via `git mv`)
- fix : none reported

### diagonal blue/white logo, no gradient
date : 2026-09-02

- branch : `feature/design_cleaning`
- changes : replaced the blue-to-white gradient logo with a hard diagonal blue/white split (bottom-left to top-right corner), matching a bi-color cheatsheet worked out for future reuse; removed the now-unused gradient logo scripts
- impact files : `scripts/print-diagonal-logo.ps1`/`.sh` (new), `run-windows.bat`/`run-macos.command`/`run-linux.sh`
- fix : none reported

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Two distinct user groups in a live, offline lap-race event context:

- **Operators**: non-technical volunteers/organizers running the event from a laptop or tablet, registering teams, recording laps, and managing race phases during a live, time-pressured event
- **Public/spectators**: viewers watching the scoreboard on a phone, tablet, or large TV display, wanting a live, glanceable leaderboard with no interaction required

## Product Purpose

A free, open-source race-timing tool for youth movements, associations, and community groups running a lap-race event. Tracks team registration, lap timing, and results through a `registry -> race -> finished` phase model, and displays a live public leaderboard - all without requiring internet/WIFI access. Success looks like a non-technical organizer being able to install (`uv sync` + `uv run app.py`), run, and operate the whole event with zero paid tools or vendor lock-in.

## Positioning

A race-timing tool a paid or cloud-hosted competitor cannot truthfully copy: fully offline (LAN-only, shareable via a phone hotspot, no internet or account required to run), free and open-source (MIT), and installable/operable by a non-technical volunteer with a single `uv sync` + `uv run app.py`. State survives crashes and restarts via autosave, and resuming after a real-world downtime gap does not corrupt the displayed race clock - resilience most free/DIY tools do not offer.

## Operating Context

A live, time-pressured community event (youth movement, association, club) with no reliable internet access:
- Operator runs the console from a laptop/tablet, optionally shared to other devices over a phone Wi-Fi hotspot
- Public scoreboard is displayed on a phone, tablet, or large TV (up to 4K) for spectators, read-only, auto-refreshing every second
- Race proceeds through three phases in order: `registry` (team setup) -> `race` (live lap recording) -> `finished` (locked results + charts)
- Sessions can be interrupted (crash, restart, network drop) and must resume without corrupting elapsed time

## Capabilities and Constraints

- Confirmed: state persists across restarts via atomic autosave to `race_state_autosave.json`; a restart or crash mid-race resumes correctly, shifting elapsed-time fields forward by the real downtime gap so the clock doesn't appear to have kept running. (Older README/CHANGELOG text describing "in-memory only, resets on restart" is stale - it describes the first release; the project has since moved to a more advanced branch and that documentation hasn't been updated yet.)
- Backend (`RaceState`) is the sole source of truth; frontend never computes rankings, durations, or stats - it only renders what `/api/state` returns
- Lap edits support a batch of mixed edit/remove actions validated atomically (all-or-nothing) per team
- No authentication/session/multi-race isolation - a single shared race state per running server instance
- No formal WCAG target (see Accessibility & Inclusion)
- Undecided: no plan yet to support more than one concurrent race per server instance

## Brand Commitments

Practical, honest, community-built. Explicitly avoids a generic corporate SaaS or AI-templated look - the tone (per the README) is scrappy-but-reliable, not slick marketing.

Anti-references: generic AI-slop SaaS templates (gradient hero sections, cookie-cutter dashboards); paid/vendor-locked race-timing software; anything that requires an internet connection or cloud account to function.

## Evidence on Hand

- README.md and CHANGELOG.md document install/run steps and version history (CHANGELOG currently lags the advanced branch's actual behavior, per confirmed note above)
- MIT License, copyright Tom Weber
- `icon/` directory exists but is currently empty - no app icon/logo asset on hand yet
- No testimonials, case studies, or real event usage data on hand; none should be invented

## Product Principles

- Backend is the source of truth; the UI only ever renders what the server sends, never computes its own numbers
- Clarity over cleverness - built for non-technical operators under live-event time pressure, not for admins comfortable with dense tooling
- Works everywhere it's needed - operator console adapts to phone/tablet, scoreboard scales up to 4K TV displays, everything works with zero internet access
- Resilient by default - state survives crashes and restarts, and resuming after downtime never corrupts the displayed race clock
- No unnecessary dependencies - install and run with just `uv`, nothing else to configure

## Accessibility & Inclusion

No formal WCAG target; keep the interface usable and legible (large timer/leaderboard text, sufficient color contrast) without dedicated colorblind or reduced-motion accommodations at this time.

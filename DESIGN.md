---
name: Race Lap App
description: Offline-first race-timing console and public scoreboard for community lap-race events
colors:
  navy: "#061534"
  action-blue: "#005eff"
  alert-red: "#e11d22"
  success-green: "#00b33c"
  spectrum-purple: "#8b35ff"
  ink: "#04122f"
  muted-slate: "#5f6f86"
  grid-line: "#d9e6f4"
  page-tint: "#eaf1f8"
  surface: "#ffffff"
  danger-red: "#b91c1c"
typography:
  display:
    fontFamily: "Barlow Condensed, sans-serif"
    fontSize: "27px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.04em"
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  label:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.14em"
  mono:
    fontFamily: "Roboto Mono, ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: "16px"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "normal"
rounded:
  none: "0px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "16px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "10px 14px"
  button-secondary:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "10px 14px"
  button-important:
    backgroundColor: "{colors.alert-red}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "10px 14px"
  button-danger:
    backgroundColor: "{colors.danger-red}"
    textColor: "#ffffff"
    rounded: "{rounded.none}"
    padding: "10px 14px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "14px"
---

# Design System: Race Lap App

## 1. Overview

**Creative North Star: "The Timing Booth Console"**

The look is a physical race-timing console, not a SaaS dashboard: flat surfaces, hard corners, thin borders instead of shadows, uppercase mono/condensed labels like a scoreboard display. Every visual decision favors instant legibility over decoration - operators are tapping buttons mid-event under time pressure, and spectators are reading numbers from across a room. Nothing here tries to look "designed"; it tries to look like it's doing a job reliably.

This system explicitly rejects the generic AI-templated SaaS look: no gradients, no soft drop shadows, no rounded pill everything, no decorative color for its own sake. Color is functional (blue = primary action, red = destructive/urgent, green/purple = ranking signal) and never purely aesthetic.

**Key Characteristics:**
- Flat, bordered surfaces - zero border-radius, zero box-shadow anywhere in the codebase
- Condensed uppercase display type for headings/labels, monospace for every number that changes (timers, laps)
- A tight, functional color palette where every hue has exactly one job
- Two distinct surfaces for two distinct audiences: a dense operator console and a large-type public scoreboard

## 2. Colors

A restrained, functional palette: navy anchors the brand chrome, blue carries primary actions, and red/green/purple are reserved for meaning (danger, success, ranking) rather than decoration.

### Primary
- **Action Blue** (#005eff): primary buttons, links, rank numbers, sticky scoreboard header accent border. The one color used for "click this" and "this is the current rank".

### Secondary
- **Navy** (#061534): brand header, scoreboard top shell, sticky leaderboard header background. Reserved for structural chrome, never for body text or buttons.

### Tertiary
- **Alert Red** (#e11d22): "important"-class actions (Finish race, Reset) and the scoreboard's live indicator strip - always urgent or destructive, never neutral.

### Neutral
- **Ink** (#04122f): all body text.
- **Muted Slate** (#5f6f86): labels, secondary/meta text (uppercase field labels, status captions).
- **Grid Line** (#d9e6f4): borders on cards, inputs, table rules.
- **Page Tint** (#eaf1f8): page and body background - kept identical on purpose so there is never a visible seam between the two.
- **Surface** (#ffffff): card and table backgrounds.

### Named Rules
**The Function-Only Color Rule.** Green (#00b33c) and purple (#8b35ff) exist solely to mark best-lap and top-of-field highlights in the leaderboard - never used as decoration or brand color elsewhere. Danger red (#b91c1c) is reserved for destructive confirmations and error text, kept visually distinct from the brighter alert red used for urgent-but-routine actions.

## 3. Typography

**Display Font:** Barlow Condensed (with sans-serif fallback)
**Body Font:** Barlow (with system-ui, sans-serif fallback)
**Label/Mono Font:** Roboto Mono (with ui-monospace, SFMono-Regular, Menlo fallback)

**Character:** A condensed, uppercase-leaning display face paired with a workmanlike grotesque body face and a monospace for data - the pairing reads as "instrument panel", not "editorial".

### Hierarchy
- **Display** (700, 27px card headings up to 56px scoreboard brand title, letter-spacing 0.04em, uppercase): section headings and the scoreboard's big brand title.
- **Body** (400-600, 14px): form labels, buttons, general UI copy.
- **Label** (600, 11px, letter-spacing 0.14em, uppercase): field labels and small status captions.
- **Mono** (700, 16px base up to 150px on 4K scoreboard displays): every number that represents live data - lap timers, elapsed/remaining clock, rank.

### Named Rules
**The Numbers-Are-Mono Rule.** Any value that changes in real time (timers, lap counts, durations) renders in Roboto Mono. Static labels never use mono; this is the only visual cue distinguishing "live data" from "chrome" at a glance.

## 4. Elevation

This system uses no shadows at all. Depth and hierarchy are conveyed entirely through flat color blocks and 1px borders (`border: 1px solid var(--grid)`), never through `box-shadow`. A card is "elevated" only in the sense that it sits on a `--surface` white block against the `--page-tint` background, bordered, with hard corners.

### Named Rules
**The Flat-By-Default Rule.** No `box-shadow` declarations exist anywhere in the stylesheet, and `border-radius: 0` is set globally on inputs/selects/buttons. If a future component needs to imply depth, use a border or a background-color tint change, never a shadow.

## 5. Components

### Buttons
- **Shape:** hard corners (`border-radius: 0`), uppercase text, `letter-spacing: 0.08em`.
- **Primary:** action blue background, white text, `10px 14px` padding.
- **Secondary:** white background, grid-line border, ink text.
- **Important:** alert-red background, white text - used for urgent/primary-of-the-moment actions (Finish race, Reset all).
- **Danger:** danger-red background, white text - reserved for destructive confirmations distinct from "important".
- **Hover / Active:** hover darkens via `filter: brightness(0.88)`; active darkens further (`brightness(0.75)`) and scales down slightly (`transform: scale(0.97)`) for tactile press feedback. Disabled buttons drop to `opacity: 0.5` with `cursor: not-allowed`.

### Cards / Containers
- **Corner Style:** none - `border-radius: 0` throughout.
- **Background:** white (`--surface`) against the tinted page background.
- **Shadow Strategy:** none (see Elevation) - a single 1px `--grid` border is the only surface delineation.
- **Border:** 1px solid grid-line on all cards.
- **Internal Padding:** 14px standard, 12px for compact variants (`.card-compact`).

### Inputs / Fields
- **Style:** flat, 1px grid-line border, white background, hard corners, 10px/12px padding.
- **Focus / Error:** no dedicated focus-ring styling defined yet; errors surface as red text in a shared error box rather than field-level highlighting.

### Navigation
- **Style:** a two-item nav in the operator header (active tab = navy background/white text, inactive = white background/bordered), no dropdowns or nested navigation.

### Sticky Leaderboard Header (signature component)
The scoreboard's `<thead>` is deliberately given its own identity distinct from the flat white body rows: navy background, white text, and a 2px action-blue bottom border, so it reads as an anchored control surface rather than a floating white box while the table scrolls underneath it.

## 6. Do's and Don'ts

### Do:
- **Do** keep `border-radius: 0` and no `box-shadow` on every new component - flatness is the entire visual identity.
- **Do** render any live/changing number in Roboto Mono; keep static labels in Barlow/Barlow Condensed.
- **Do** reserve green/purple exclusively for best-lap/top-rank highlighting, never as general accent color.
- **Do** keep `body` and `.page` backgrounds on the same `page-tint` token so there is never a visible seam.

### Don't:
- **Don't** introduce gradients, soft drop shadows, or rounded-pill buttons/cards - that reads as generic AI-templated SaaS, which this project explicitly rejects.
- **Don't** add decorative color; every hue in this palette has exactly one functional job.
- **Don't** compute or format any leaderboard/timer value in the frontend - the backend snapshot is the only source of truth, and the UI's job is purely to render it.

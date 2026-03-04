# Busters Den

Hello, this is a scouting app I create for my FRC (FIRST Robotics Competition) team, 9097 machbusters. It can be used by anyone. I create this because I wanted a place that is consise while also using all the stuff from both blue alliance and statobotics in order to make better judgments, and also just to show about. That is all I have to say, now read the AI slop that explains this code (Which is also somewhat of AI slop :>)

---

## What It Does

This dashboard pulls live competition data and gives your team a clean, organized view of everything happening at an FRC event:

- **Command Center** — Event stats at a glance: average match score, total teams, match progress, and upcoming matches
- **Leaderboard** — Full team rankings with win/loss records and OPR (Offensive Power Rating)
- **My Team** — Focused view on your own team: current rank, record, average score, EPA, next match preview, previous match result, and win probability for the next match
- **Match Schedule** — All qualification matches with filters (All / Upcoming / Completed / My Team), each clickable for a detailed breakdown
- **Match Analysis** — Per-match deep dive showing predicted winner, win percentages, and EPA breakdown for every team in both alliances
- **Alliance Builder** — Enter any 6 teams (3 vs 3) and instantly get a win probability prediction based on EPA

---

## Data Sources

| Source | What it provides |
|---|---|
| [The Blue Alliance (TBA)](https://www.thebluealliance.com/) | Match results, rankings, OPR, team lists, event info |
| [Statbotics](https://www.statbotics.io/) | EPA (Expected Points Added), Unitless/Normalized EPA |

---

## Setup

### First Launch
When you open the app for the first time, a setup wizard walks you through two steps:

1. **API Key** — Get a free Read API key from [thebluealliance.com/account](https://www.thebluealliance.com/account) and paste it in
2. **Event Key** — Enter the TBA event key for your competition (e.g. `2025txhou` for a Texas regional) and optionally your team number

Settings are saved in `localStorage` so you only need to set this up once per browser.

### Event Key Format
Event keys follow the pattern `YEAR` + `EVENT_CODE`, for example:
- `2025cmptx` → Houston World Championship 2025
- `2025nytr` → NY Tech Valley Regional 2025

Find event keys at [thebluealliance.com/events](https://www.thebluealliance.com/events).

---

## Files

| File | Purpose |
|---|---|
| `scouting.html` | Main app shell — all HTML structure, UI layout, navigation, modals |
| `main.py` | All app logic written in Python (runs in-browser via PyScript) |
| `pyscript.json` | PyScript config — declares Python packages and entry point |
| `StyleSCOUTING.css` | Base styles (dark theme, glass card effect, neon glow, animations) |

---

## How It Works Technically

The app uses **PyScript** to run Python directly in the browser (no backend). Here's the flow:

1. **PyScript** loads `main.py` and the `pyodide-http` package into a WebAssembly Python runtime
2. On startup, `Dashboard` checks `localStorage` for saved credentials. If found, it fetches data automatically; otherwise the setup wizard appears
3. **TBAClient** makes authenticated `GET` requests to the TBA v3 REST API using your API key
4. **StatboticsClient** hits the Statbotics v3 REST API (no auth required) to fetch EPA data for all teams at the event
5. All fetched data is cached in memory (`self.matches_data`, `self.epa_lookup`, etc.) so switching views is fast
6. The UI is rendered by building HTML strings in Python and injecting them via `element.innerHTML`

### EPA (Expected Points Added)
EPA is a stat from Statbotics that estimates how many points a team contributes to their alliance per match. The app uses it to:
- Show each team's performance on the leaderboard and match analysis pages
- Calculate win probabilities by comparing total alliance EPA
- Power the Alliance Builder predictions

Two modes are available:
- **EPA** — Raw expected points (game-specific, easier to interpret)
- **Unitless EPA** — Normalized across seasons, useful for cross-year comparisons

---

## Requirements

- A modern browser (Chrome, Firefox, Safari, Edge)
- An internet connection (to load PyScript and fetch API data)
- A free TBA API key

No installs, no build steps, no server. Just open `scouting.html`.
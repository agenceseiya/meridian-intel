# MERIDIAN INTEL

**Geopolitical Intelligence Monitor — Iran / US / Israel Conflict**

A real-time open-source intelligence (OSINT) aggregation dashboard monitoring the Iran-US-Israel conflict. Built as a public resource for journalists, analysts, and anyone following the situation.

---

## Overview

MERIDIAN INTEL is an intelligence dashboard with a **real-time backend** that automatically aggregates live data from multiple open sources every 60 seconds:

- **RSS Feeds** — Reuters, Al Jazeera, BBC World, AP News, Times of Israel (auto-fetched and filtered)
- **X (Twitter)** — OSINT accounts, official military/government feeds from all parties
- **Telegram** — Verified channels (Mossad Farsi, Iran International, IRGC Official)
- **Official Government Accounts** — US (White House, POTUS, Pentagon, State Dept, CENTCOM), Israel (PMO, IDF, MFA), Iran (Khamenei, FM Araghchi, PressTV), regional MFAs (Saudi, Qatar, Turkey, Jordan, Egypt, UAE, Iraq), global powers (Russia, France, UK, IAEA, UN)

## Features

- **Live Intelligence Feed** — Auto-refreshing timeline (60-second polling) with classification tags (FLASH / URGENT / ROUTINE) and color-coded source attribution
- **Real-Time Feed Engine** — Backend CGI service fetches and filters RSS feeds for conflict-relevant headlines, with file-based caching and fault tolerance
- **Platform Analytics** — Built-in visitor tracking: total views, today's views, active watchers, unique sessions
- **Feed Status Bar** — Shows fetch status (LIVE / FETCHING / ERROR), last fetch time, countdown to next fetch, and per-source health indicators
- **Situation Metrics** — Conflict status, threat levels, oil prices, Strait of Hormuz risk, airspace closures, nuclear risk assessment
- **Regional Schematic Map** — SVG-based operational map showing strike paths, retaliation arcs, US carrier groups, military bases
- **Strategic Analysis** — Military assessment, diplomatic status, economic impact, key figures tracking
- **Intelligence Sources Directory** — 50+ monitored X accounts organized by country, Telegram channels, and live media coverage links
- **Dark/Light Mode** — Intelligence-grade dark theme by default, with light mode toggle
- **Live IST Clock** — Real-time clock synced to Israel Standard Time
- **Fully Responsive** — Desktop, tablet, and mobile layouts

## Architecture

```
Client (browser)                    Server (CGI-bin)
  |                                    |
  |-- Every 60s --- GET /feed.py ----->| Fetch RSS feeds
  |<------------ JSON response --------| Filter by keywords
  |                                    | Classify priority
  |                                    | Cache 60s
  |                                    |
  |-- On load ---- POST /analytics --->| Record pageview
  |                                    | Store in SQLite
  |                                    |
  |-- Every 2min - GET /heartbeat ---->| Track active users
  |                                    |
  |-- Every 60s -- GET /summary ------>| Return analytics
```

## Tech Stack

- HTML5, CSS3, JavaScript — no frameworks, no build tools
- Python 3 CGI backend (stdlib only — no pip dependencies)
- SQLite for analytics storage
- IBM Plex Sans + IBM Plex Mono (Google Fonts)
- CSS Grid layout with fluid typography (`clamp()`)
- SVG-based regional map

## Getting Started

### Option 1: Static site (no live feed)

Just open `index.html` in any modern browser. The feed will show baseline hardcoded entries.

### Option 2: Full stack with live feed

```bash
# Python CGI server (built-in)
python -m http.server --cgi 8000
```

Then navigate to `http://localhost:8000`.

## File Structure

```
meridian-intel/
├── index.html           # Main dashboard
├── base.css             # CSS reset and base styles
├── style.css            # Design tokens, color palette, animations
├── dashboard.css        # Dashboard component styles + analytics + feed status
├── app.js               # Real-time polling, analytics tracking, clock, theme
├── cgi-bin/
│   ├── feed.py          # Live intelligence feed API (RSS aggregation)
│   └── analytics.py     # Analytics tracking & reporting API (SQLite)
└── README.md            # This file
```

## API Endpoints

### `GET /cgi-bin/feed.py`
Returns filtered, prioritized intelligence entries from RSS feeds.

### `POST /cgi-bin/analytics.py`
Record a pageview event.

### `GET /cgi-bin/analytics.py?action=summary`
Returns analytics summary (total views, today views, active users, sessions, referrers, device breakdown).

### `GET /cgi-bin/analytics.py?action=heartbeat&session_id=xxx`
Record an active-user heartbeat for live "watching now" count.

## Sources & Attribution

This dashboard aggregates publicly available information from:

- Reuters, Associated Press, Al Jazeera, CNN, BBC, Times of Israel
- IDF Spokesperson, Pentagon / US Department of Defense, CENTCOM
- White House, State Department, Israel PMO, Israel MFA
- Iran Supreme Leader office, Iran FM, PressTV
- Regional MFAs: Saudi Arabia, Qatar, Turkey, Jordan, Egypt, UAE, Iraq
- Russia MFA, France MFA, UK FCDO, IAEA, United Nations
- X/Twitter OSINT community (@Osinttechnical, @Osint613, @IntelCrab, @sentdefender)
- Telegram channels (Iran International, Middle East Spectator, Mossad Farsi)

## Disclaimer

**MERIDIAN INTEL** is an open-source intelligence aggregation platform. Information is compiled from publicly available sources and may contain unverified reports. Always cross-reference with official sources.

## License

MIT License — free to use, modify, and distribute.

---

Built with open-source intelligence principles. Stay informed. Stay safe.
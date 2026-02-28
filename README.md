# MERIDIAN INTEL

**Geopolitical Intelligence Monitor — Iran / US / Israel Conflict**

A real-time open-source intelligence (OSINT) aggregation dashboard monitoring the Iran-US-Israel conflict. Built as a public resource for journalists, analysts, and anyone following the situation.

---

## Overview

MERIDIAN INTEL is a static, client-side intelligence dashboard that aggregates and presents information from multiple open sources:

- **X (Twitter)** — OSINT accounts, official military/government feeds
- **Telegram** — Verified channels (Mossad Farsi, Iran International, IRGC Official)
- **Wire Services** — Reuters, AP, Al Jazeera, CNN, BBC
- **OSINT Community** — Geolocation, satellite imagery analysis, flight tracking

## Features

- **Live Intelligence Feed** — Chronological timeline with classification tags (FLASH / URGENT / ROUTINE) and color-coded source attribution (IDF, IRGC, POTUS, MEDIA, OSINT)
- **Situation Metrics** — Conflict status, threat levels, oil prices, Strait of Hormuz risk, airspace closures, nuclear risk assessment
- **Regional Schematic Map** — SVG-based operational map showing strike paths, retaliation arcs, US carrier groups, military bases, and the Strait of Hormuz
- **Strategic Analysis** — Military assessment, diplomatic status, economic impact, key figures tracking
- **Intelligence Sources Directory** — Curated list of monitored X accounts, Telegram channels, and live media coverage links
- **Dark/Light Mode** — Intelligence-grade dark theme by default, with light mode toggle
- **Live IST Clock** — Real-time clock synced to Israel Standard Time
- **Fully Responsive** — Desktop, tablet, and mobile layouts

## Tech Stack

- Pure HTML5, CSS3, JavaScript — no frameworks, no build tools
- IBM Plex Sans + IBM Plex Mono (Google Fonts)
- CSS Grid layout with fluid typography (`clamp()`)
- SVG-based regional map
- Zero dependencies, zero tracking, zero cookies

## Getting Started

### Option 1: Open directly

Just open `index.html` in any modern browser.

### Option 2: Local server

```bash
# Python
python -m http.server 8000

# Node.js
npx serve .

# PHP
php -S localhost:8000
```

Then navigate to `http://localhost:8000`.

## File Structure

```
meridian-intel/
├── index.html       # Main dashboard
├── base.css         # CSS reset and base styles
├── style.css        # Design tokens, color palette, animations
├── dashboard.css    # Dashboard-specific component styles
├── app.js           # Clock, theme toggle, scroll animations
└── README.md        # This file
```

## Sources & Attribution

This dashboard aggregates publicly available information from:

- Reuters, Associated Press, Al Jazeera, CNN, BBC, NBC News
- IDF Spokesperson, Pentagon / US Department of Defense
- X/Twitter OSINT community (@Osinttechnical, @Osint613, @IntelCrab, @sentdefender)
- Telegram channels (Iran International, Middle East Spectator)
- The Jerusalem Post, Times of Israel, Euronews

## Disclaimer

**MERIDIAN INTEL** is an open-source intelligence aggregation platform. Information is compiled from publicly available sources and may contain unverified reports. Always cross-reference with official sources. This platform does not represent the views of any government, military, or intelligence agency.

## Contributing

Contributions welcome. If you want to:

- Add new intelligence entries to the timeline
- Improve the regional map accuracy
- Add new monitored sources
- Connect live data feeds (X API, Telegram API, RSS)
- Translate the interface

Please open an issue or submit a pull request.

## License

MIT License — free to use, modify, and distribute.

---

Built with open-source intelligence principles. Stay informed. Stay safe.
#!/usr/bin/env python3
"""
MERIDIAN INTEL — Live Intelligence Feed API
CGI endpoint: /cgi-bin/feed.py

Aggregates real-time intelligence from RSS feeds, filters for geopolitical
relevance, and returns JSON. Uses file-based caching (60-second TTL).
"""

import json
import os
import sys
import hashlib
import re
import time
import email.utils
import html as html_module
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

# ─── IST timezone (UTC+5:30) ──────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

# ─── Cache settings ───────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
CACHE_FILE = os.path.join(PROJECT_DIR, "feed_cache.json")
CACHE_TTL = 60  # seconds

# ─── RSS Sources ──────────────────────────────────────────────────────────────
RSS_SOURCES = [
    {
        "key": "reuters",
        "tag": "REUTERS",
        "urls": [
            "https://www.reuters.com/rssFeed/worldNews/",
            "https://feeds.reuters.com/Reuters/worldNews",
        ],
    },
    {
        "key": "aljazeera",
        "tag": "ALJAZEERA",
        "urls": ["https://www.aljazeera.com/xml/rss/all.xml"],
    },
    {
        "key": "bbc",
        "tag": "BBC",
        "urls": ["http://feeds.bbci.co.uk/news/world/rss.xml"],
    },
    {
        "key": "ap",
        "tag": "AP",
        "urls": ["https://rsshub.app/apnews/topics/apf-topnews"],
    },
    {
        "key": "toi",
        "tag": "TOI",
        "urls": ["https://www.timesofisrael.com/feed/"],
    },
]

# ─── Relevance keywords (case-insensitive) ────────────────────────────────────
KEYWORDS = [
    "iran", "israel", "idf", "irgc", "tehran", "isfahan",
    "netanyahu", "khamenei", "trump", "pentagon", "centcom",
    "middle east", "hezbollah", "houthi", "hormuz", "nuclear",
    "ballistic", "missile", "strike", "attack", "war", "conflict",
    "military", "airspace", "ceasefire", "retaliation", "sanctions",
]

# ─── Priority word lists ──────────────────────────────────────────────────────
FLASH_WORDS  = ["breaking", "flash", "missile", "strike", "attack", "killed", "launch"]
URGENT_WORDS = ["urgent", "warning", "retaliation", "emergency"]

# ─── Hardcoded baseline entries (always included as fallback) ─────────────────
BASELINE_ENTRIES = [
    {
        "id": "baseline_001",
        "time": "2026-02-28T17:30:00+05:30",
        "time_display": "28 FEB 2026 / 17:30 IST",
        "priority": "flash",
        "source_tag": "IRGC",
        "source_class": "official",
        "title": "IRGC confirms second wave of ballistic missiles launched toward Israel",
        "content": "Second wave of ballistic missiles launched toward Israel. IRGC confirms additional strikes incoming.",
    },
    {
        "id": "baseline_002",
        "time": "2026-02-28T17:18:00+05:30",
        "time_display": "28 FEB 2026 / 17:18 IST",
        "priority": "flash",
        "source_tag": "IDF",
        "source_class": "official",
        "title": "IDF intercepting second Iranian missile barrage — Arrow and Iron Dome active across Israel",
        "content": "Israeli Air Force intercepting second barrage of Iranian missiles. Iron Dome and Arrow systems active across northern and central Israel.",
    },
    {
        "id": "baseline_003",
        "time": "2026-02-28T17:05:00+05:30",
        "time_display": "28 FEB 2026 / 17:05 IST",
        "priority": "urgent",
        "source_tag": "OSINT",
        "source_class": "media",
        "title": "Shamkhani reportedly killed in strikes — Khamenei evacuated to secure location",
        "content": "Reports: Ali Shamkhani, Secretary of Supreme National Security Council, killed in strikes. Khamenei status unknown — relocated to secure location. Information unverified.",
    },
    {
        "id": "baseline_004",
        "time": "2026-02-28T16:58:00+05:30",
        "time_display": "28 FEB 2026 / 16:58 IST",
        "priority": "urgent",
        "source_tag": "OSINT",
        "source_class": "media",
        "title": "Trump: 'We are going to obliterate their missiles' — operation continues indefinitely",
        "content": "Trump: \"We are going to obliterate their missiles and dismantle their missile industry completely.\" Operation to continue \"as long as necessary.\"",
    },
    {
        "id": "baseline_005",
        "time": "2026-02-28T16:45:00+05:30",
        "time_display": "28 FEB 2026 / 16:45 IST",
        "priority": "flash",
        "source_tag": "IDF",
        "source_class": "official",
        "title": "IDF: broad strike on Iran defense systems complete — state of emergency declared",
        "content": "IDF declares \"broad strike\" on Iran's defense systems completed. State of emergency declared across Israel. Home front command issues instructions to civilians.",
    },
    {
        "id": "baseline_006",
        "time": "2026-02-28T16:30:00+05:30",
        "time_display": "28 FEB 2026 / 16:30 IST",
        "priority": "urgent",
        "source_tag": "REUTERS",
        "source_class": "media",
        "title": "Iran FM: Armed Forces will respond decisively — emergency parliament session convened",
        "content": "Iran's foreign ministry: \"Armed Forces will respond decisively to aggressors.\" Tehran preparing \"crushing\" retaliation. Parliament session convened in emergency.",
    },
    {
        "id": "baseline_007",
        "time": "2026-02-28T16:12:00+05:30",
        "time_display": "28 FEB 2026 / 16:12 IST",
        "priority": "flash",
        "source_tag": "OSINT",
        "source_class": "media",
        "title": "Explosions confirmed: Tehran, Isfahan, Qom, Karaj, Kermanshah — strikes near Khamenei compound",
        "content": "Explosions confirmed in Tehran, Isfahan, Qom, Karaj, Kermanshah. Strikes near Supreme Leader Khamenei's compound — 7 missiles confirmed hitting the area. Heavy smoke over Parchin.",
    },
    {
        "id": "baseline_008",
        "time": "2026-02-28T15:50:00+05:30",
        "time_display": "28 FEB 2026 / 15:50 IST",
        "priority": "urgent",
        "source_tag": "OSINT",
        "source_class": "media",
        "title": "Trump confirms major combat operations — Operation Epic Fury / Operation Roaring Lion",
        "content": "Trump confirms \"major combat operations\" in Iran. Operation codenamed \"Epic Fury.\" Netanyahu: \"Operation Roaring Lion / Shield of Judah.\" Joint statement from White House and PMO.",
    },
    {
        "id": "baseline_009",
        "time": "2026-02-28T15:32:00+05:30",
        "time_display": "28 FEB 2026 / 15:32 IST",
        "priority": "flash",
        "source_tag": "IDF",
        "source_class": "official",
        "title": "Israel launches pre-emptive strike on Iran — IAF and naval forces participating",
        "content": "Israel launches pre-emptive strike on Iran. IAF aircraft and naval forces participating. Defense Minister Katz declares immediate state of emergency across all districts.",
    },
    {
        "id": "baseline_010",
        "time": "2026-02-27T14:00:00+05:30",
        "time_display": "27 FEB 2026 / 14:00 IST",
        "priority": "routine",
        "source_tag": "REUTERS",
        "source_class": "media",
        "title": "Geneva nuclear talks end without deal — Oman mediation effort officially collapses",
        "content": "Nuclear talks in Geneva conclude without deal. Iran rejects demands to dismantle Fordow, Natanz, Isfahan facilities. Oman mediation effort officially collapsed.",
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def now_ist():
    """Return current datetime in IST."""
    return datetime.now(IST)


def format_display(dt):
    """Format datetime as '28 FEB 2026 / 17:30 IST'."""
    return dt.strftime("%d %b %Y / %H:%M IST").upper()


def make_id(url_or_title):
    """SHA-1 hash truncated to 16 chars for use as entry ID."""
    return hashlib.sha1(url_or_title.encode("utf-8")).hexdigest()[:16]


def classify_priority(title):
    """Classify entry priority based on title keywords."""
    t = title.lower()
    for w in FLASH_WORDS:
        if w in t:
            return "flash"
    for w in URGENT_WORDS:
        if w in t:
            return "urgent"
    return "routine"


def is_relevant(text):
    """Return True if text contains any geopolitical keyword."""
    t = text.lower()
    for kw in KEYWORDS:
        if kw in t:
            return True
    return False


def strip_html(text):
    """Remove HTML tags and decode entities from a string."""
    cleaned = re.sub(r"<[^>]+>", "", text or "").strip()
    return html_module.unescape(cleaned)


def parse_date(date_str):
    """
    Parse RFC 2822 (RSS pubDate) or ISO 8601 (Atom) date strings.
    Returns a timezone-aware datetime in IST, or None on failure.
    """
    if not date_str:
        return None
    date_str = date_str.strip()
    # Try RFC 2822 first (typical RSS)
    try:
        parsed = email.utils.parsedate_to_datetime(date_str)
        return parsed.astimezone(IST)
    except Exception:
        pass
    # Try ISO 8601
    try:
        normalized = date_str.replace("Z", "+00:00")
        normalized = re.sub(r"\.\d+", "", normalized)  # strip fractional seconds
        return datetime.fromisoformat(normalized).astimezone(IST)
    except Exception:
        pass
    return None


def extract_rss_items(root):
    """
    Extract raw (title, link, description, date_str) tuples from either
    RSS 2.0 or Atom XML root element.
    """
    items = []
    tag = root.tag  # e.g. '{http://www.w3.org/2005/Atom}feed' or 'rss'

    ATOM_NS = "http://www.w3.org/2005/Atom"

    # ── Atom ──────────────────────────────────────────────────────────────────
    if ATOM_NS in tag or tag.endswith("}feed") or tag == "feed":
        def af(el, name):
            return (
                el.find(f"{{{ATOM_NS}}}{name}")
                or el.find(name)
            )
        entries = root.findall(f"{{{ATOM_NS}}}entry") or root.findall("entry")
        for entry in entries:
            title_el = af(entry, "title")
            link_el  = af(entry, "link")
            summ_el  = af(entry, "summary") or af(entry, "content")
            date_el  = af(entry, "updated") or af(entry, "published")

            title = (title_el.text or "").strip() if title_el is not None else ""
            link  = ""
            if link_el is not None:
                link = link_el.get("href", "") or (link_el.text or "")
            desc = strip_html((summ_el.text or "") if summ_el is not None else "")
            date_str = (date_el.text or "").strip() if date_el is not None else ""
            items.append((title, link.strip(), desc, date_str))

    # ── RSS 2.0 ───────────────────────────────────────────────────────────────
    else:
        channel = root.find("channel")
        elements = channel.findall("item") if channel is not None else root.findall(".//item")
        DC_NS = "http://purl.org/dc/elements/1.1/"
        for item in elements:
            title_el = item.find("title")
            link_el  = item.find("link")
            desc_el  = item.find("description")
            date_el  = item.find("pubDate")
            if date_el is None:
                date_el = item.find(f"{{{DC_NS}}}date")

            title    = strip_html((title_el.text or "") if title_el is not None else "")
            link     = ((link_el.text or "") if link_el is not None else "").strip()
            desc     = strip_html((desc_el.text or "") if desc_el is not None else "")
            date_str = ((date_el.text or "") if date_el is not None else "").strip()
            items.append((title, link, desc, date_str))

    return items


def fetch_source(source):
    """
    Fetch and parse one RSS source definition.
    Returns (list_of_entries, status_string).
    Tries each URL in order; stops at first successful parse.
    """
    cutoff = now_ist() - timedelta(hours=2)
    last_err = "no_urls_tried"

    for url in source["urls"]:
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "MeridianIntel/1.0 RSS Aggregator",
                    "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*",
                },
            )
            with urlopen(req, timeout=5) as resp:
                raw = resp.read()

            root = ET.fromstring(raw)
            raw_items = extract_rss_items(root)

            entries = []
            for (title, link, description, date_str) in raw_items:
                if not title:
                    continue
                combined = title + " " + description
                if not is_relevant(combined):
                    continue
                pub_dt = parse_date(date_str)
                # Skip articles older than 2 hours if we have a date
                if pub_dt is not None and pub_dt < cutoff:
                    continue
                entry_dt = pub_dt if pub_dt is not None else now_ist()
                entry_id = make_id(link or title)
                content = (description[:280] if description else title[:280])
                entries.append({
                    "id": entry_id,
                    "time": entry_dt.isoformat(),
                    "time_display": format_display(entry_dt),
                    "priority": classify_priority(title),
                    "source_tag": source["tag"],
                    "source_class": "media",
                    "title": title,
                    "content": content,
                })
            return entries, "ok"

        except (URLError, HTTPError) as e:
            last_err = f"network: {e}"
        except ET.ParseError as e:
            last_err = f"xml: {e}"
        except Exception as e:
            last_err = f"error: {e}"

    return [], f"error: {last_err}"


# ─── Cache ────────────────────────────────────────────────────────────────────

def load_cache():
    """
    Load feed_cache.json.
    Returns (data_dict, age_in_seconds). age=inf if cache missing or unreadable.
    """
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = data.get("_cached_at", 0)
        age = time.time() - cached_at
        return data, age
    except Exception:
        return None, float("inf")


def save_cache(data):
    """Write data dict to feed_cache.json with a _cached_at epoch timestamp."""
    try:
        payload = dict(data)
        payload["_cached_at"] = time.time()
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        pass  # Cache failure is non-fatal


# ─── Feed builder ─────────────────────────────────────────────────────────────

def build_feed():
    """
    Fetch all configured RSS sources, merge with baseline entries,
    deduplicate, sort newest-first, and return the response dict.
    """
    sources_status = {}
    all_entries = []
    seen_ids = set()

    for source in RSS_SOURCES:
        entries, status = fetch_source(source)
        sources_status[source["key"]] = status
        for e in entries:
            if e["id"] not in seen_ids:
                seen_ids.add(e["id"])
                all_entries.append(e)

    # Always include baseline entries as fallback content
    for e in BASELINE_ENTRIES:
        if e["id"] not in seen_ids:
            seen_ids.add(e["id"])
            all_entries.append(e)

    # Sort by time descending (newest first)
    def sort_key(e):
        try:
            return datetime.fromisoformat(e["time"])
        except Exception:
            return datetime.min.replace(tzinfo=IST)

    all_entries.sort(key=sort_key, reverse=True)
    all_entries = all_entries[:50]

    n = now_ist()
    return {
        "status": "ok",
        "updated": n.isoformat(),
        "updated_display": format_display(n),
        "entry_count": len(all_entries),
        "entries": all_entries,
        "sources_status": sources_status,
    }


# ─── CGI entry point ──────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8")

    # Always print CGI headers first
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Cache-Control: no-cache, no-store")
    print()

    try:
        # Try to serve from cache if still fresh
        cached, age = load_cache()
        if cached is not None and age < CACHE_TTL:
            # Mark all source statuses as "cached"
            if "sources_status" in cached:
                for k in list(cached["sources_status"].keys()):
                    cached["sources_status"][k] = "cached"
            cached.pop("_cached_at", None)
            print(json.dumps(cached, ensure_ascii=False))
            return

        # Cache is stale or missing — fetch fresh data
        response = build_feed()
        save_cache(response)
        # Remove internal cache key from response
        response.pop("_cached_at", None)
        print(json.dumps(response, ensure_ascii=False))

    except Exception as e:
        # Last-resort error response — always includes baseline entries
        n = now_ist()
        error_payload = {
            "status": "error",
            "error": str(e),
            "updated": n.isoformat(),
            "updated_display": format_display(n),
            "entry_count": len(BASELINE_ENTRIES),
            "entries": BASELINE_ENTRIES,
            "sources_status": {s["key"]: "error" for s in RSS_SOURCES},
        }
        print(json.dumps(error_payload, ensure_ascii=False))


if __name__ == "__main__":
    main()

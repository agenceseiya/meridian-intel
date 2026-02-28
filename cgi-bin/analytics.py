#!/usr/bin/env python3
"""
MERIDIAN INTEL — Analytics Tracking & Reporting API
CGI endpoint: /cgi-bin/analytics.py

POST: Record a pageview or event.
GET ?action=summary: Return analytics summary.
GET ?action=heartbeat&session_id=xxx: Record active-user heartbeat.
"""

import json
import os
import sys
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, "..")
DB_PATH = os.path.join(PROJECT_DIR, "analytics.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event        TEXT    DEFAULT 'pageview',
    path         TEXT    DEFAULT '/',
    referrer     TEXT,
    user_agent   TEXT,
    screen_width INTEGER,
    country      TEXT,
    timestamp    TEXT    DEFAULT (datetime('now')),
    session_id   TEXT
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);
"""

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute(CREATE_TABLE_SQL)
    db.execute(CREATE_INDEX_SQL)
    db.commit()
    return db

def now_ist_str():
    return datetime.now(IST).isoformat()

def parse_qs(query_string):
    params = {}
    if not query_string: return params
    for part in query_string.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k.strip()] = v.strip()
        elif part.strip():
            params[part.strip()] = ""
    return params

def device_type(screen_width):
    if screen_width is None: return "unknown"
    try: w = int(screen_width)
    except (ValueError, TypeError): return "unknown"
    if w >= 1024: return "desktop"
    if w >= 768: return "tablet"
    return "mobile"

def handle_post():
    content_length = int(os.environ.get("CONTENT_LENGTH", 0) or 0)
    raw_body = sys.stdin.read(content_length) if content_length > 0 else sys.stdin.read()
    try: body = json.loads(raw_body) if raw_body.strip() else {}
    except json.JSONDecodeError: body = {}
    event        = str(body.get("event", "pageview"))[:64]
    path         = str(body.get("path", "/"))[:1024]
    referrer     = str(body.get("referrer", "") or "")[:2048]
    user_agent   = str(body.get("user_agent", "") or "")[:512]
    screen_width = body.get("screen_width")
    country      = str(body.get("country", "") or "")[:8]
    session_id   = str(body.get("session_id", "") or str(uuid.uuid4()))[:64]
    timestamp    = now_ist_str()
    db = get_db()
    db.execute("""INSERT INTO events (event, path, referrer, user_agent, screen_width, country, timestamp, session_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (event, path, referrer, user_agent, screen_width, country, timestamp, session_id))
    db.commit()
    db.close()
    return {"status": "recorded"}

def handle_heartbeat(session_id):
    session_id = (str(session_id) or str(uuid.uuid4()))[:64]
    timestamp  = now_ist_str()
    db = get_db()
    db.execute("""INSERT INTO events (event, path, timestamp, session_id) VALUES ('heartbeat', '/', ?, ?)""", (timestamp, session_id))
    db.commit()
    db.close()
    return {"status": "ok"}

def handle_summary():
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS cnt FROM events WHERE event != 'heartbeat'").fetchone()
    total_views = row["cnt"] if row else 0
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    row = db.execute("""SELECT COUNT(*) AS cnt FROM events WHERE event != 'heartbeat' AND date(timestamp) = ?""", (today_str,)).fetchone()
    today_views = row["cnt"] if row else 0
    now_ist_dt    = datetime.now(IST)
    five_min_ago  = (now_ist_dt - timedelta(minutes=5)).isoformat()
    row = db.execute("""SELECT COUNT(DISTINCT session_id) AS cnt FROM events WHERE timestamp >= ? AND session_id IS NOT NULL AND session_id != ''""", (five_min_ago,)).fetchone()
    active_last_5min = row["cnt"] if row else 0
    row = db.execute("""SELECT COUNT(DISTINCT session_id) AS cnt FROM events WHERE date(timestamp) = ? AND session_id IS NOT NULL AND session_id != ''""", (today_str,)).fetchone()
    unique_sessions_today = row["cnt"] if row else 0
    rows = db.execute("""SELECT referrer, COUNT(*) AS cnt FROM events WHERE event != 'heartbeat' AND referrer IS NOT NULL AND referrer != '' GROUP BY referrer ORDER BY cnt DESC LIMIT 10""").fetchall()
    top_referrers = [{"referrer": r["referrer"], "count": r["cnt"]} for r in rows]
    twenty_four_ago = (now_ist_dt - timedelta(hours=24)).isoformat()
    rows = db.execute("""SELECT substr(timestamp, 12, 2) AS hour, COUNT(*) AS cnt FROM events WHERE event != 'heartbeat' AND timestamp >= ? GROUP BY hour ORDER BY hour""", (twenty_four_ago,)).fetchall()
    views_by_hour = [{"hour": r["hour"], "count": r["cnt"]} for r in rows]
    rows = db.execute("""SELECT screen_width, COUNT(*) AS cnt FROM events WHERE event != 'heartbeat' GROUP BY screen_width""").fetchall()
    device_counts = {"desktop": 0, "mobile": 0, "tablet": 0}
    for r in rows:
        dtype = device_type(r["screen_width"])
        if dtype in device_counts: device_counts[dtype] += r["cnt"]
    db.close()
    return {"total_views": total_views, "today_views": today_views, "active_last_5min": active_last_5min, "unique_sessions_today": unique_sessions_today, "top_referrers": top_referrers, "views_by_hour": views_by_hour, "device_breakdown": device_counts}

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Content-Type: application/json")
    print("Access-Control-Allow-Origin: *")
    print("Cache-Control: no-cache, no-store")
    print()
    try:
        method       = os.environ.get("REQUEST_METHOD", "GET").upper()
        query_string = os.environ.get("QUERY_STRING", "")
        params       = parse_qs(query_string)
        if method == "POST":
            result = handle_post()
        elif method == "GET":
            action = params.get("action", "summary")
            if action == "heartbeat":
                session_id = params.get("session_id", "")
                result = handle_heartbeat(session_id)
            else:
                result = handle_summary()
        elif method == "OPTIONS":
            print("Access-Control-Allow-Methods: GET, POST, OPTIONS")
            print("Access-Control-Allow-Headers: Content-Type")
            result = {"status": "ok"}
        else:
            result = {"status": "error", "error": f"method_not_allowed: {method}"}
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
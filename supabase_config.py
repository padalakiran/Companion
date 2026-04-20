# ── supabase_config.py ────────────────────────────────────────────────────────
# Single source of truth for all remote config.
# Every module calls get_key("column_name") — no .env, no caching, no fallback.
#
# YOUR TABLE COLUMNS (from screenshot):
#   Gemini_key   — Gemini API key
#   Weather_key  — OpenWeatherMap API key
#   City         — default weather city
#   Version      — minimum/current app version (float8)
#   Link         — download URL for updates
#   Repo         — GitHub repo (e.g. kiran/desktop-cat-companion)
#
# SETUP (one time):
#   1. Supabase dashboard → Settings → API
#   2. Copy "Project URL"  → SUPABASE_URL below
#   3. Copy "anon public"  → SUPABASE_ANON_KEY below
#   4. Enable RLS on app_config table
#   5. Add policy: allow SELECT for everyone (role: anon)

import urllib.request
import json

# ── Paste your credentials here ───────────────────────────────────────────────
SUPABASE_URL      = "https://ncauihwaicrjpkkwwats.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5jYXVpaHdhaWNyanBra3d3YXRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY1OTAyNTAsImV4cCI6MjA5MjE2NjI1MH0.kGJnu36YlNjhVxyITz5EMKbADRZ3aZMZpi8QUA6TlzI"
TABLE_NAME        = "app_config"
#─────────────────────────────────────────────────────────────────────────────

_config: dict = {}    # populated on first call to get_key()
_loaded: bool = False


def _fetch() -> dict:
    """Fetch the first row from app_config table. Returns {} on any error."""
    url = f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}?limit=1"
    try:
        req = urllib.request.Request(url, headers={
            "apikey":        SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
            "Content-Type":  "application/json",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            rows = json.loads(resp.read().decode())
           # print(rows[0])
            if rows and isinstance(rows, list):
                print(f"[supabase] loaded: {list(rows[0].keys())}")
                return rows[0]
            
            

           # print(rows)
    except Exception as e:
        print(f"[supabase] fetch error: {e}")
    return {}


def get_key(column: str, fallback: str = "") -> str:
    """
    Get a value from Supabase app_config by column name.
    Fetches on first call, then returns from memory.

    Usage:
        supabase_config.get_key("Gemini_key")
        supabase_config.get_key("Weather_key")
        supabase_config.get_key("City", "Bengaluru")
        supabase_config.get_key("Repo")
        supabase_config.get_key("Version")
        supabase_config.get_key("Link")
    """
    global _config, _loaded
    if not _loaded:
        _config = _fetch()
        _loaded = True
    val = _config.get(column)
    return str(val).strip() if val else fallback

# print(get_key("Version"))
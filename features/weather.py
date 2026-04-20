# ── features/weather.py ───────────────────────────────────────────────────────
# Phase 7: Weather Widget
# - Current weather + 5-day forecast
# - OpenWeatherMap free API
# - City configurable (default: Bengaluru, IN)
# - Weather icons drawn on Canvas (no image files needed)
# - Cached to avoid repeated API calls (refreshes every 30 min)

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import threading
import time
import json
import os
import urllib.request
import urllib.error
import config

import theme as _theme_mod
def _c(k): return _theme_mod.get(k)
GREEN  = "#A6E3A1"; YELLOW = "#F9E2AF"; RED    = "#F38BA8"
ORANGE = "#E07B54"; BLUE   = "#74C7EC"

# ── Config ────────────────────────────────────────────────────────────────────
CACHE_FILE   = os.path.join(config.DATA_DIR, "weather_cache.json")
CACHE_EXPIRY = 30 * 60   # 30 minutes in seconds
DEFAULT_CITY = "Bengaluru"
DEFAULT_UNIT = "metric"  # metric = Celsius

# ── Weather condition → canvas icon key ───────────────────────────────────────
def _condition_key(weather_id: int) -> str:
    if weather_id < 300:   return "thunder"
    if weather_id < 400:   return "drizzle"
    if weather_id < 600:   return "rain"
    if weather_id < 700:   return "snow"
    if weather_id < 800:   return "fog"
    if weather_id == 800:  return "clear"
    if weather_id <= 802:  return "partly_cloudy"
    return "cloudy"

def _draw_weather_icon(canvas, key: str, cx: int, cy: int, size: int = 48):
    """Draw a weather icon using canvas shapes. No image files."""
    s = size // 2
    canvas.delete("all")

    if key == "clear":
        # Sun
        canvas.create_oval(cx-s//2, cy-s//2, cx+s//2, cy+s//2,
                           fill=_c("YELLOW"), outline="")
        for a in range(0, 360, 45):
            import math
            r1, r2 = s//2+4, s//2+10
            x1 = cx + int(r1 * math.cos(math.radians(a)))
            y1 = cy + int(r1 * math.sin(math.radians(a)))
            x2 = cx + int(r2 * math.cos(math.radians(a)))
            y2 = cy + int(r2 * math.sin(math.radians(a)))
            canvas.create_line(x1, y1, x2, y2, fill=_c("YELLOW"), width=2)

    elif key == "partly_cloudy":
        import math
        # Sun behind cloud
        canvas.create_oval(cx-s//2+4, cy-s//2-4, cx+s//2+4, cy+s//2-4,
                           fill=_c("YELLOW"), outline="")
        # Cloud
        canvas.create_oval(cx-s+2, cy-4, cx+2,     cy+s-4, fill=_c("ACCENT"), outline="")
        canvas.create_oval(cx-s+8, cy-s//2+4, cx+8, cy+s-4, fill=_c("ACCENT"), outline="")
        canvas.create_oval(cx-4,   cy-2, cx+s-4,   cy+s-4, fill=_c("ACCENT"), outline="")
        canvas.create_rectangle(cx-s+2, cy+4, cx+s-4, cy+s-4, fill=_c("ACCENT"), outline="")

    elif key == "cloudy":
        # Two overlapping clouds
        canvas.create_oval(cx-s+4,  cy-6,    cx+4,    cy+s-4, fill=_c("SUB"), outline="")
        canvas.create_oval(cx-s+10, cy-s//2, cx+10,   cy+s-4, fill=_c("SUB"), outline="")
        canvas.create_oval(cx-4,    cy-2,    cx+s-4,  cy+s-4, fill=_c("TEXT"), outline="")
        canvas.create_oval(cx-s+4,  cy+4,    cx+s-4,  cy+s-2, fill=_c("TEXT"), outline="")

    elif key == "rain":
        import math
        # Cloud
        canvas.create_oval(cx-s+4,  cy-s//2, cx+4,   cy+4, fill=_c("SUB"), outline="")
        canvas.create_oval(cx-s+10, cy-s,    cx+10,  cy+4, fill=_c("SUB"), outline="")
        canvas.create_oval(cx-4,    cy-s//2, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        canvas.create_rectangle(cx-s+4, cy, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        # Raindrops
        for i, dx in enumerate([-10, 0, 10]):
            y0 = cy + 10 + (i % 2) * 4
            canvas.create_line(cx+dx, y0, cx+dx-2, y0+8,
                               fill=_c("BLUE"), width=2, capstyle="round")

    elif key == "drizzle":
        import math
        canvas.create_oval(cx-s+4,  cy-s//2+4, cx+4,   cy+8, fill=_c("SUB"),  outline="")
        canvas.create_oval(cx-4,    cy-s//2+4, cx+s-4, cy+8, fill=_c("TEXT"), outline="")
        canvas.create_rectangle(cx-s+4, cy+4, cx+s-4, cy+8, fill=_c("TEXT"), outline="")
        for dx in [-8, 0, 8]:
            canvas.create_line(cx+dx, cy+12, cx+dx-1, cy+18,
                               fill=_c("BLUE"), width=1, capstyle="round")

    elif key == "thunder":
        import math
        canvas.create_oval(cx-s+4,  cy-s//2, cx+4,   cy+4, fill=_c("SUB"),  outline="")
        canvas.create_oval(cx-4,    cy-s//2, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        canvas.create_rectangle(cx-s+4, cy, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        # Lightning bolt
        canvas.create_polygon(cx+2, cy+6, cx-4, cy+18, cx+2, cy+16, cx-2, cy+28,
                              cx+8, cy+14, cx+2, cy+16, cx+8, cy+6,
                              fill=_c("YELLOW"), outline="")

    elif key == "snow":
        import math
        canvas.create_oval(cx-s+4,  cy-s//2, cx+4,   cy+4, fill=_c("TEXT"), outline="")
        canvas.create_oval(cx-4,    cy-s//2, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        canvas.create_rectangle(cx-s+4, cy, cx+s-4, cy+4, fill=_c("TEXT"), outline="")
        for dx in [-10, 0, 10]:
            canvas.create_text(cx+dx, cy+18, text="❄", font=("Segoe UI",10), fill=_c("BLUE"))

    elif key == "fog":
        for i, dy in enumerate([-6, 0, 6]):
            #alpha = 200 - i*40
            canvas.create_line(cx-s+4, cy+dy, cx+s-4, cy+dy,
                               fill=_c("SUB"), width=4, capstyle="round")

    else:
        # Default: question mark
        canvas.create_text(cx, cy, text="?", font=("Segoe UI",24,"bold"), fill=_c("SUB"))

# ── API helpers ───────────────────────────────────────────────────────────────

def _load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            if time.time() - data.get("timestamp", 0) < CACHE_EXPIRY:
                return data
    except Exception:
        pass
    return None

def _save_cache(data: dict):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    try:
        data["timestamp"] = time.time()
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def _get_api_key() -> str:
    import supabase_config
    return supabase_config.get_key("Weather_key")

def _get_city() -> str:
    import supabase_config
    return supabase_config.get_key("City", DEFAULT_CITY)

def _fetch_weather(api_key: str, city: str) -> dict | None:
    """Fetch current + forecast from OpenWeatherMap. Returns parsed dict or None."""
    base = "https://api.openweathermap.org/data/2.5"
    unit = DEFAULT_UNIT
    try:
        # Current weather
        url_cur = f"{base}/weather?q={city}&appid={api_key}&units={unit}"
        with urllib.request.urlopen(url_cur, timeout=8) as r:
            cur = json.loads(r.read())

        # 5-day forecast (3-hour intervals)
        url_fc = f"{base}/forecast?q={city}&appid={api_key}&units={unit}&cnt=40"
        with urllib.request.urlopen(url_fc, timeout=8) as r:
            fc = json.loads(r.read())

        # Parse daily forecast (take noon reading per day)
        days = {}
        for item in fc["list"]:
            dt   = datetime.fromtimestamp(item["dt"])
            day  = dt.strftime("%A")
            hour = dt.hour
            if day not in days or abs(hour - 12) < abs(days[day]["hour"] - 12):
                days[day] = {
                    "hour":  hour,
                    "day":   day,
                    "date":  dt.strftime("%d %b"),
                    "temp":  round(item["main"]["temp"]),
                    "min":   round(item["main"]["temp_min"]),
                    "max":   round(item["main"]["temp_max"]),
                    "desc":  item["weather"][0]["description"].capitalize(),
                    "id":    item["weather"][0]["id"],
                }
        # Remove today from forecast
        today = datetime.now().strftime("%A")
        days.pop(today, None)
        forecast = list(days.values())[:5]

        result = {
            "city":      cur["name"],
            "country":   cur["sys"]["country"],
            "temp":      round(cur["main"]["temp"]),
            "feels":     round(cur["main"]["feels_like"]),
            "humidity":  cur["main"]["humidity"],
            "wind":      round(cur["wind"]["speed"] * 3.6, 1),  # m/s → km/h
            "desc":      cur["weather"][0]["description"].capitalize(),
            "id":        cur["weather"][0]["id"],
            "forecast":  forecast,
        }
        return result
    except urllib.error.HTTPError as e:
        print(f"[weather] HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"[weather] fetch error: {e}")
        return None

# ── Main view ─────────────────────────────────────────────────────────────────

def build(parent: tk.Frame, root: tk.Tk):
    fh   = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    fb   = tkfont.Font(family="Segoe UI", size=11)
    fs   = tkfont.Font(family="Segoe UI", size=9)
    fbn  = tkfont.Font(family="Segoe UI", size=10, weight="bold")
    ftemp= tkfont.Font(family="Segoe UI", size=44, weight="bold")
    fdesc= tkfont.Font(family="Segoe UI", size=11)
    fday = tkfont.Font(family="Segoe UI", size=9, weight="bold")

    #state = {"loading": False, "data": None, "error": None}

    # ── Loading / error / content frames ─────────────────────────────────────
    def show_loading():
        for w in parent.winfo_children(): w.destroy()
        spinner = tk.Label(parent, text="Fetching weather…",
                           font=fb, bg=_c("BG"), fg=_c("SUB"))
        spinner.pack(expand=True)

    def show_setup():
        """Show API key setup prompt."""
        for w in parent.winfo_children(): w.destroy()

        tk.Label(parent, text="Weather Setup", font=fh, bg=_c("BG"), fg=_c("ACCENT")).pack(pady=(30,8))
        tk.Label(parent,
                 text="Enter your OpenWeatherMap API key\nand city to get started.\n\n"
                      "Free key at: openweathermap.org/api",
                 font=fs, bg=_c("BG"), fg=_c("SUB"), justify="center").pack()

        form = tk.Frame(parent, bg=_c("BG"))
        form.pack(pady=20)

        # API key entry
        tk.Label(form, text="API Key:", font=fs, bg=_c("BG"), fg=_c("SUB")).grid(
            row=0, column=0, sticky="e", padx=(0,8), pady=4)
        key_wrap = tk.Frame(form, bg=_c("BORDER"))
        key_wrap.grid(row=0, column=1, pady=4)
        key_var = tk.StringVar(value=_get_api_key())
        tk.Entry(key_wrap, textvariable=key_var, font=fb,
                 bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
                 relief="flat", bd=0, width=26, show="•"
                 ).pack(padx=1, pady=1, ipady=6)

        # City entry
        tk.Label(form, text="City:", font=fs, bg=_c("BG"), fg=_c("SUB")).grid(
            row=1, column=0, sticky="e", padx=(0,8), pady=4)
        city_wrap = tk.Frame(form, bg=_c("BORDER"))
        city_wrap.grid(row=1, column=1, pady=4)
        city_var = tk.StringVar(value=_get_city())
        tk.Entry(city_wrap, textvariable=city_var, font=fb,
                 bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
                 relief="flat", bd=0, width=26
                 ).pack(padx=1, pady=1, ipady=6)

        err_lbl = tk.Label(parent, text="", font=fs, bg=_c("BG"), fg=_c("RED"))
        err_lbl.pack()

        def save_and_fetch():
            #city = city_var.get().strip() or DEFAULT_CITY
            _save_cache({})   # invalidate cache
            load_weather()

        tk.Button(parent, text="Get Weather  →",
                  font=fbn, bg=_c("ACCENT"), fg=_c("BG"),
                  activebackground=_c("TEXT"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=save_and_fetch
                  ).pack(ipady=8, ipadx=20)

    def show_error(msg: str):
        for w in parent.winfo_children(): w.destroy()
        tk.Label(parent, text="⚠  Could not load weather",
                 font=fh, bg=_c("BG"), fg=_c("RED")).pack(pady=(40,8))
        tk.Label(parent, text=msg, font=fs, bg=_c("BG"), fg=_c("SUB"),
                 wraplength=400, justify="center").pack()
        tk.Button(parent, text="↺  Retry",
                  font=fbn, bg=_c("BORDER"), fg=_c("ACCENT"),
                  activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=load_weather
                  ).pack(pady=14, ipady=6, ipadx=16)
        tk.Button(parent, text="⚙  Change API key / city",
                  font=fs, bg=_c("BG"), fg=_c("SUB"),
                  activebackground=_c("BG"), activeforeground=_c("TEXT"),
                  relief="flat", cursor="hand2", bd=0,
                  command=show_setup
                  ).pack(ipady=4, ipadx=10)

    def show_weather(data: dict):
        for w in parent.winfo_children(): w.destroy()

        cond  = _condition_key(data["id"])
        color = MODES_COLOR.get(cond, _c("ACCENT"))

        # ── Top card: current weather ─────────────────────────────────────────
        top_b = tk.Frame(parent, bg=_c("BORDER"))
        top_b.pack(fill="x", pady=(0,10))
        top   = tk.Frame(top_b, bg=_c("CARD"))
        top.pack(fill="x", padx=1, pady=1)

        left = tk.Frame(top, bg=_c("CARD"))
        left.pack(side="left", padx=16, pady=14)

        # Big icon
        ic = tk.Canvas(left, width=72, height=72, bg=_c("CARD"),
                       bd=0, highlightthickness=0)
        ic.pack()
        _draw_weather_icon(ic, cond, 36, 36, 64)

        # City name
        tk.Label(left,
                 text=f"{data['city']}, {data['country']}",
                 font=fb, bg=_c("CARD"), fg=_c("SUB")).pack(anchor="w")

        right = tk.Frame(top, bg=_c("CARD"))
        right.pack(side="right", padx=16, pady=14)

        # Temperature
        tk.Label(right, text=f"{data['temp']}°C",
                 font=ftemp, bg=_c("CARD"), fg=color).pack(anchor="e")

        tk.Label(right, text=data["desc"],
                 font=fdesc, bg=_c("CARD"), fg=_c("TEXT")).pack(anchor="e")

        # Details row
        det_row = tk.Frame(top, bg=_c("CARD"))
        det_row.pack(fill="x", padx=16, pady=(0,12))

        for icon, val in [
            ("💧", f"Humidity {data['humidity']}%"),
            ("💨", f"Wind {data['wind']} km/h"),
            ("🌡", f"Feels {data['feels']}°C"),
        ]:
            cell = tk.Frame(det_row, bg=_c("CARD"))
            cell.pack(side="left", expand=True)
            tk.Label(cell, text=f"{icon}  {val}",
                     font=fs, bg=_c("CARD"), fg=_c("SUB")).pack()

        # ── Forecast row ──────────────────────────────────────────────────────
        tk.Label(parent, text="5-day forecast",
                 font=fh, bg=_c("BG"), fg=_c("SUB")).pack(anchor="w", pady=(4,6))

        fc_row = tk.Frame(parent, bg=_c("BG"))
        fc_row.pack(fill="x")

        for i, day in enumerate(data.get("forecast", [])):
            day_b = tk.Frame(fc_row, bg=_c("BORDER"))
            day_b.pack(side="left", expand=True, fill="x",
                       padx=(0 if i==0 else 4, 0))
            day_c = tk.Frame(day_b, bg=_c("CARD"))
            day_c.pack(fill="both", padx=1, pady=1)

            d_cond  = _condition_key(day["id"])
            d_color = MODES_COLOR.get(d_cond, _c("ACCENT"))

            tk.Label(day_c, text=day["day"][:3],
                     font=fday, bg=_c("CARD"), fg=_c("TEXT")).pack(pady=(8,2))

            ic2 = tk.Canvas(day_c, width=36, height=36, bg=_c("CARD"),
                            bd=0, highlightthickness=0)
            ic2.pack()
            _draw_weather_icon(ic2, d_cond, 18, 18, 32)

            tk.Label(day_c, text=f"{day['temp']}°",
                     font=fday, bg=_c("CARD"), fg=d_color).pack()
            tk.Label(day_c,
                     text=f"{day['min']}°–{day['max']}°",
                     font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(pady=(0,8))

        # ── Last updated + refresh button ─────────────────────────────────────
        bot = tk.Frame(parent, bg=_c("BG"))
        bot.pack(fill="x", pady=(12,0))

        cache = _load_cache()
        if cache and cache.get("timestamp"):
            ts = datetime.fromtimestamp(cache["timestamp"]).strftime("%H:%M")
            tk.Label(bot, text=f"Updated at {ts}",
                     font=fs, bg=_c("BG"), fg=_c("BORDER")).pack(side="left")

        tk.Button(bot, text="↺  Refresh",
                  font=fs, bg=_c("BORDER"), fg=_c("ACCENT"),
                  activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=lambda: [_save_cache({}), load_weather()]
                  ).pack(side="right", ipady=4, ipadx=10)

        tk.Button(bot, text="⚙  Settings",
                  font=fs, bg=_c("BG"), fg=_c("SUB"),
                  activebackground=_c("BG"), activeforeground=_c("TEXT"),
                  relief="flat", cursor="hand2", bd=0,
                  command=show_setup
                  ).pack(side="right", padx=6, ipady=4, ipadx=8)

    # Colour map for weather conditions
    MODES_COLOR = {
        "clear":        YELLOW,
        "partly_cloudy":_c("ACCENT"),
        "cloudy":       _c("SUB"),
        "rain":         BLUE,
        "drizzle":      BLUE,
        "thunder":      ORANGE,
        "snow":         _c("TEXT"),
        "fog":          _c("SUB"),
    }

    # ── Data loading ──────────────────────────────────────────────────────────

    def load_weather():
        api_key = _get_api_key()
        if not api_key:
            show_setup(); return

        # Try cache first
        cached = _load_cache()
        if cached and "temp" in cached:
            show_weather(cached); return

        show_loading()

        def fetch():
            city = _get_city()
            data = _fetch_weather(api_key, city)
            if data:
                _save_cache(data)
                root.after(0, lambda: show_weather(data))
            else:
                root.after(0, lambda: show_error(
                    "Check your API key and internet connection.\n"
                    "Free key at openweathermap.org/api"))

        threading.Thread(target=fetch, daemon=True).start()

    load_weather()

# ── Settings helper ────────────────────────────────────────────────────────────

def _save_setting(key: str, value: str):
    """Keys are managed via Supabase dashboard — no local save."""
    print(f"[weather] {key} is managed via Supabase")

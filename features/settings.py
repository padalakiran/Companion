# # ── features/settings.py ──────────────────────────────────────────────────────
# # Phase 9: Settings — all preferences in one place
# # Saves to user.xlsx + .env (for API keys/city)

# import tkinter as tk
# from tkinter import font as tkfont
# import os
# import openpyxl
# import config

# import theme as _theme_mod
# def _c(k): return _theme_mod.get(k)

# # ── Helpers ───────────────────────────────────────────────────────────────────
# def _load_user() -> dict:
#     data = {}
#     if not os.path.exists(config.USER_DATA): return data
#     try:
#         wb = openpyxl.load_workbook(config.USER_DATA)
#         ws = wb.active
#         for row in ws.iter_rows(values_only=True):
#             if row[0] and row[1] and row[0] != "key":
#                 data[str(row[0])] = str(row[1])
#     except: pass
#     return data

# def _save_user(key: str, value: str):
#     os.makedirs(config.DATA_DIR, exist_ok=True)
#     try:
#         if os.path.exists(config.USER_DATA):
#             wb = openpyxl.load_workbook(config.USER_DATA)
#             ws = wb.active
#             for row in ws.iter_rows():
#                 if row[0].value == key:
#                     row[1].value = value
#                     wb.save(config.USER_DATA); return
#             ws.append([key, value])
#             wb.save(config.USER_DATA)
#         else:
#             wb = openpyxl.Workbook(); ws = wb.active
#             ws.title = "User"
#             ws.append(["key","value"])
#             ws.append([key, value])
#             wb.save(config.USER_DATA)
#     except Exception as e:
#         print(f"[settings] user save: {e}")

# # ── Section builder helper ─────────────────────────────────────────────────────
# def _section(parent, title: str):
#     """Returns the inner frame of a labelled section card."""
#     tk.Label(parent, text=title,
#              font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
#              bg=_c("BG"), fg=_c("SUB")).pack(anchor="w", pady=(14,4))
#     border = tk.Frame(parent, bg=_c("BORDER"))
#     border.pack(fill="x")
#     inner = tk.Frame(border, bg=_c("CARD"))
#     inner.pack(fill="x", padx=1, pady=1)
#     return inner

# def _row(parent, label: str, widget_fn):
#     """Build a label + widget row inside a section."""
#     row = tk.Frame(parent, bg=_c("CARD"))
#     row.pack(fill="x", padx=14, pady=8)
#     tk.Label(row, text=label,
#              font=tkfont.Font(family="Segoe UI", size=10),
#              bg=_c("CARD"), fg=_c("TEXT"), width=22, anchor="w").pack(side="left")
#     widget_fn(row)
#     return row

# def _entry_widget(parent, var: tk.StringVar, show=""):
#     wrap = tk.Frame(parent, bg=_c("BORDER"))
#     wrap.pack(side="left", fill="x", expand=True)
#     e = tk.Entry(wrap, textvariable=var,
#                  font=tkfont.Font(family="Segoe UI", size=10),
#                  bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
#                  relief="flat", bd=0, highlightthickness=0,
#                  show=show)
#     e.pack(fill="x", padx=1, pady=1, ipady=6)
#     return e

# def _save_badge(parent, fn):
#     """Small Save button."""
#     tk.Button(parent, text="Save",
#               font=tkfont.Font(family="Segoe UI", size=9, weight="bold"),
#               bg=_c("ACCENT"), fg=_c("BG"),
#               activebackground=_c("TEXT"), activeforeground=_c("BG"),
#               relief="flat", cursor="hand2", bd=0,
#               command=fn).pack(side="left", padx=(8,0), ipady=4, ipadx=10)

# # ── Main view ─────────────────────────────────────────────────────────────────
# def build(parent: tk.Frame, root: tk.Tk, user: dict = None,
#           cat_widget=None, on_name_change=None, on_interval_change=None,
#           on_tile_update=None):
#     if user is None: user = {}

#     import supabase_config
#     user_data = _load_user()

#     fb  = tkfont.Font(family="Segoe UI", size=10)
#     #fbn = tkfont.Font(family="Segoe UI", size=10, weight="bold")
#     fs  = tkfont.Font(family="Segoe UI", size=9)

#     # Feedback label at top
#     feedback = tk.Label(parent, text="", font=fs, bg=_c("BG"), fg=_c("GREEN"))
#     feedback.pack(anchor="w", pady=(0,4))

#     def show_saved(msg="Settings saved ✓"):
#         feedback.config(text=msg, fg=_c("GREEN"))
#         parent.after(2500, lambda: feedback.config(text=""))

#     def show_error(msg):
#         feedback.config(text=msg, fg=_c("RED"))
#         parent.after(2500, lambda: feedback.config(text=""))

#     # ── Scrollable content ────────────────────────────────────────────────────
#     outer = tk.Frame(parent, bg=_c("BG"))
#     outer.pack(fill="both", expand=True)

#     cv = tk.Canvas(outer, bg=_c("BG"), bd=0, highlightthickness=0)
#     cv.pack(side="left", fill="both", expand=True)

#     SB_W = 4
#     sb = tk.Canvas(outer, width=SB_W, bg=_c("BG"), bd=0, highlightthickness=0)
#     sb.pack(side="right", fill="y")
#     thumb = sb.create_rectangle(0,0,SB_W,30, fill=_c("ACCENT"), outline="")

#     content = tk.Frame(cv, bg=_c("BG"))
#     cwin = cv.create_window((0,0), window=content, anchor="nw")

#     def update_thumb(*_):
#         try:
#             t,b = cv.yview(); h=max(sb.winfo_height(),1)
#             sb.coords(thumb,0,t*h,SB_W,max(b*h,t*h+14))
#         except: pass

#     def scroll(d): cv.yview_scroll(d,"units"); update_thumb()

#     def _safe_scroll(e):
#         top,bot=cv.yview()
#         if top==0.0 and bot==1.0: return
#         scroll(-1*(e.delta//120))
#     for w in (cv,content,sb):
#         w.bind("<MouseWheel>", _safe_scroll)

#     def bind_scroll_recursive(widget):
#         """Bind mouse wheel on every widget so scroll works everywhere."""
#         def _safe_scroll(e):
#             top, bot = cv.yview()
#             if top == 0.0 and bot == 1.0: return
#             scroll(-1*(e.delta//120))
#         try:
#             widget.bind("<MouseWheel>", _safe_scroll)
#         except Exception: pass
#         for child in widget.winfo_children():
#             bind_scroll_recursive(child)

#     # Re-bind after content is fully built
#     def _bind_all_scroll():
#         bind_scroll_recursive(content)
#     content.bind("<Configure>", lambda e: [
#         cv.configure(scrollregion=cv.bbox("all")),
#         update_thumb(),
#         _bind_all_scroll()
#     ])

#     def sb_drag(e):
#         t,b=cv.yview(); h=max(sb.winfo_height(),1)
#         cv.yview_moveto(max(0,e.y/h-(b-t)/2)); update_thumb()
#     sb.bind("<ButtonPress-1>",sb_drag); sb.bind("<B1-Motion>",sb_drag)
#     cv.bind("<Configure>", lambda e: [
#         cv.itemconfig(cwin,width=e.width), update_thumb()])

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 1 — Profile
#     # ═══════════════════════════════════════════════════════════════════════
#     s1 = _section(content, "👤  Profile")

#     name_var = tk.StringVar(value=user.get("name", user_data.get("name","Friend")))
#     def _row_name(p):
#         _entry_widget(p, name_var)
#         def save_name():
#             n = name_var.get().strip()
#             if not n: show_error("Name cannot be empty."); return
#             _save_user("name", n)
#             user["name"] = n
#             if on_name_change: on_name_change(n)
#             show_saved("Name updated ✓")
#         _save_badge(p, save_name)
#     _row(s1, "Your name", _row_name)

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 2 — Health reminders
#     # ═══════════════════════════════════════════════════════════════════════
#     s2 = _section(content, "💧  Health reminders")

#     water_var   = tk.StringVar(value=user_data.get("water_interval",   str(config.WATER_INTERVAL_MIN)))
#     break_var   = tk.StringVar(value=user_data.get("break_interval",   str(config.BREAK_INTERVAL_MIN)))
#     stretch_var = tk.StringVar(value=user_data.get("stretch_interval", str(config.STRETCH_INTERVAL_MIN)))

#     def _interval_widget(p, var, key, label_suffix="min"):
#         wrap = tk.Frame(p, bg=_c("BORDER"))
#         wrap.pack(side="left")
#         e = tk.Entry(wrap, textvariable=var,
#                      font=fb, bg=_c("CARD"), fg=_c("TEXT"),
#                      insertbackground=_c("ACCENT"),
#                      relief="flat", bd=0, highlightthickness=0,
#                      width=5, justify="center")
#         e.pack(padx=1, pady=1, ipady=6)
#         tk.Label(p, text=label_suffix, font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(side="left", padx=(4,0))

#     def _row_water(p):
#         _interval_widget(p, water_var, "water_interval")
#         def save():
#             try:
#                 v = int(water_var.get())
#                 assert 1 <= v <= 300
#                 _save_user("water_interval", str(v))
#                 config.WATER_INTERVAL_MIN = v
#                 if on_interval_change: on_interval_change("water", v)
#                 show_saved("Water reminder updated ✓")
#             except: show_error("Enter a number between 1–300.")
#         _save_badge(p, save)

#     def _row_break(p):
#         _interval_widget(p, break_var, "break_interval")
#         def save():
#             try:
#                 v = int(break_var.get())
#                 assert 1 <= v <= 300
#                 _save_user("break_interval", str(v))
#                 config.BREAK_INTERVAL_MIN = v
#                 if on_interval_change: on_interval_change("break", v)
#                 show_saved("Break reminder updated ✓")
#             except: show_error("Enter a number between 1–300.")
#         _save_badge(p, save)

#     def _row_stretch(p):
#         _interval_widget(p, stretch_var, "stretch_interval")
#         def save():
#             try:
#                 v = int(stretch_var.get())
#                 assert 1 <= v <= 300
#                 _save_user("stretch_interval", str(v))
#                 config.STRETCH_INTERVAL_MIN = v
#                 if on_interval_change: on_interval_change("stretch", v)
#                 show_saved("Stretch reminder updated ✓")
#             except: show_error("Enter a number between 1–300.")
#         _save_badge(p, save)

#     _row(s2, "Drink water every",  _row_water)
#     _row(s2, "Short break every",  _row_break)
#     _row(s2, "Stretch every",      _row_stretch)

#     # Enable/disable toggles
#     toggle_row = tk.Frame(s2, bg=_c("CARD"))
#     toggle_row.pack(fill="x", padx=14, pady=(4,10))
#     tk.Label(toggle_row, text="Notifications:",
#              font=tkfont.Font(family="Segoe UI", size=10),
#              bg=_c("CARD"), fg=_c("TEXT"), width=22, anchor="w").pack(side="left")

#     for key, label in [("water","Water"), ("break","Break"), ("stretch","Stretch")]:
#         enabled_now = True
#         if on_interval_change and hasattr(on_interval_change, '__self__'):
#             eng = getattr(on_interval_change.__self__, '_health_engine', None)
#             if eng:
#                 enabled_now = eng.is_enabled(key)
#         var = tk.BooleanVar(value=enabled_now)
#         cell = tk.Frame(toggle_row, bg=_c("CARD"))
#         cell.pack(side="left", padx=(0,12))
#         def make_toggle(k=key, v=var):
#             def toggle():
#                 if on_interval_change and hasattr(on_interval_change, '__self__'):
#                     eng = getattr(on_interval_change.__self__, '_health_engine', None)
#                     if eng:
#                         eng.set_enabled(k, v.get())
#                         show_saved(f"{k.capitalize()} notifications {'on' if v.get() else 'off'} ✓")
#             return toggle
#         tk.Checkbutton(cell, text=label,
#                        variable=var,
#                        command=make_toggle(),
#                        font=tkfont.Font(family="Segoe UI", size=9),
#                        bg=_c("CARD"), fg=_c("TEXT"), selectcolor=_c("CARD"),
#                        activebackground=_c("CARD"), activeforeground=_c("ACCENT"),
#                        cursor="hand2", bd=0).pack(side="left")

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 3 — Cat behaviour
#     # ═══════════════════════════════════════════════════════════════════════
#     s3 = _section(content, "🐱  Cat behaviour")

#     speed_var = tk.StringVar(value=user_data.get("cat_speed", str(config.WALK_SPEED)))

#     def _row_speed(p):
#         wrap = tk.Frame(p, bg=_c("BORDER"))
#         wrap.pack(side="left")
#         e = tk.Entry(wrap, textvariable=speed_var,
#                      font=fb, bg=_c("CARD"), fg=_c("TEXT"),
#                      insertbackground=_c("ACCENT"),
#                      relief="flat", bd=0, highlightthickness=0,
#                      width=5, justify="center")
#         e.pack(padx=1, pady=1, ipady=6)
#         tk.Label(p, text="px/tick", font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(side="left", padx=(4,0))
#         def save():
#             try:
#                 v = int(speed_var.get())
#                 assert 1 <= v <= 20
#                 _save_user("cat_speed", str(v))
#                 config.WALK_SPEED = v
#                 show_saved("Cat speed updated ✓")
#             except: show_error("Enter a speed between 1–20.")
#         _save_badge(p, save)
#     _row(s3, "Walking speed", _row_speed)

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 4 — Weather
#     # ═══════════════════════════════════════════════════════════════════════
#     s4 = _section(content, "🌤  Weather")

#     city_var    = tk.StringVar(value=supabase_config.get_key("City", "Bengaluru"))

#     # Major Indian cities for autocomplete
#     CITY_SUGGESTIONS = [
#         "Bengaluru","Mumbai","Delhi","Chennai","Hyderabad","Kolkata","Pune",
#         "Ahmedabad","Jaipur","Lucknow","Surat","Kanpur","Nagpur","Indore",
#         "Bhopal","Visakhapatnam","Patna","Vadodara","Coimbatore","Agra",
#         "New York","London","Tokyo","Sydney","Dubai","Singapore","Paris",
#     ]

#     def _row_city(p):
#         # Use a frame to hold entry + dropdown
#         city_frame = tk.Frame(p, bg=_c("CARD"))
#         city_frame.pack(side="left", fill="x", expand=True, padx=(0,0))

#         entry_wrap = tk.Frame(city_frame, bg=_c("BORDER"))
#         entry_wrap.pack(fill="x")
#         city_entry = tk.Entry(entry_wrap, textvariable=city_var,
#                               font=tkfont.Font(family="Segoe UI", size=10),
#                               bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
#                               relief="flat", bd=0, highlightthickness=0)
#         city_entry.pack(fill="x", padx=1, pady=1, ipady=6)

#         # Autocomplete dropdown
#         suggest_lb = None

#         def on_type(*_):
#             nonlocal suggest_lb
#             typed = city_var.get().strip().lower()
#             if suggest_lb:
#                 try: suggest_lb.destroy()
#                 except: pass
#                 suggest_lb = None
#             if not typed or len(typed) < 2: return
#             matches = [c for c in CITY_SUGGESTIONS if typed in c.lower()][:6]
#             if not matches: return
#             suggest_lb = tk.Listbox(
#                 city_frame, font=tkfont.Font(family="Segoe UI", size=9),
#                 bg=_c("CARD"), fg=_c("TEXT"), selectbackground=_c("ACCENT"), selectforeground=_c("BG"),
#                 relief="flat", bd=0, highlightthickness=1,
#                 highlightcolor=_c("BORDER"), height=len(matches))
#             suggest_lb.pack(fill="x")
#             for m in matches: suggest_lb.insert("end", m)
#             def pick(e):
#                 nonlocal suggest_lb
#                 sel = suggest_lb.curselection()
#                 if sel: city_var.set(suggest_lb.get(sel[0]))
#                 try: suggest_lb.destroy()
#                 except: pass
#                 suggest_lb = None
#             suggest_lb.bind("<<ListboxSelect>>", pick)
#             suggest_lb.bind("<Return>", pick)

#         city_var.trace_add("write", on_type)

#         def save():
#             nonlocal suggest_lb
#             if suggest_lb:
#                 try: suggest_lb.destroy()
#                 except: pass
#                 suggest_lb = None
#             v = city_var.get().strip()
#             if not v: show_error("City cannot be empty."); return
#             # City is managed via Supabase — just refresh the weather cache
#             import json
#             try:
#                 with open(os.path.join(config.DATA_DIR,"weather_cache.json"),"w") as f:
#                     json.dump({},f)
#             except: pass
#             if on_tile_update: on_tile_update("weather", f"{v}, IN")
#             show_saved("City updated ✓")
#         _save_badge(p, save)

#     _row(s4, "City", _row_city)

#     # Weather API key is managed via .env file directly

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 5 — Theme
#     # Predefined character (name matches a theme key) → read-only label
#     # Custom/unknown character → editable dropdown, persists selection
#     # ═══════════════════════════════════════════════════════════════════════
#     import theme as _theme
#     import os as _os
#     import openpyxl as _opxl
#     from features.character import get_active_character

#     _active_path   = get_active_character()
#     theme_is_locked = _theme.is_predefined(_active_path)

#     # Read saved override for custom characters
#     _saved_override = ""
#     try:
#         if _os.path.exists(config.USER_DATA):
#             _wb = _opxl.load_workbook(config.USER_DATA)
#             for _r in _wb.active.iter_rows(values_only=True):
#                 if _r[0] == "theme_override" and _r[1]:
#                     _saved_override = str(_r[1]); break
#     except Exception: pass

#     # What to show: for locked use auto-key, for custom use live theme (set by dropdown save)
#     _current_live   = _theme.name()   # always the currently active theme name
#     _locked_key     = _theme.theme_for_character(_active_path)
#     _locked_label   = _theme.THEMES.get(_locked_key, _theme.THEMES["default"])["name"]
#     # For dropdown: show last saved override, or current live theme
#     _dropdown_key   = _saved_override if _saved_override in _theme.THEMES else _theme.theme_for_character(_active_path)
#     _dropdown_label = _theme.THEMES.get(_dropdown_key, _theme.THEMES["default"])["name"]

#     s5 = _section(content, "🎨  Theme")

#     theme_names  = {k: v["name"] for k,v in _theme.THEMES.items()}
#     theme_labels = list(theme_names.values())
#     theme_var    = tk.StringVar(value=_dropdown_label)  # persists last selection

#     def _row_theme(p):
#         if theme_is_locked:
#             # Read-only — predefined character, theme auto-applied
#             info_f = tk.Frame(p, bg=_c("CARD"))
#             info_f.pack(side="left", fill="x", expand=True)
#             tk.Label(info_f, text=_locked_label,
#                      font=tkfont.Font(family="Segoe UI", size=10),
#                      bg=_c("CARD"), fg=_c("TEXT")).pack(side="left", padx=6, pady=6)
#             tk.Label(info_f, text="(auto — set by character)",
#                      font=tkfont.Font(family="Segoe UI", size=9),
#                      bg=_c("CARD"), fg=_c("SUB")).pack(side="left")
#         else:
#             # Editable dropdown — custom character picks any theme
#             wrap = tk.Frame(p, bg=_c("CARD"))
#             wrap.pack(side="left", fill="x", expand=True)
#             om = tk.OptionMenu(wrap, theme_var, *theme_labels)
#             om.config(bg=_c("BORDER"), fg=_c("TEXT"),
#                       activebackground=_c("ACCENT"), activeforeground=_c("BG"),
#                       highlightthickness=0, relief="flat", bd=0,
#                       font=tkfont.Font(family="Segoe UI", size=10),
#                       cursor="hand2")
#             om["menu"].config(bg=_c("CARD"), fg=_c("TEXT"),
#                               activebackground=_c("ACCENT"), activeforeground=_c("BG"),
#                               font=tkfont.Font(family="Segoe UI", size=9))
#             om.pack(fill="x", padx=4, pady=4)

#             def save_theme():
#                 chosen_label = theme_var.get()
#                 chosen_key   = next(
#                     (k for k,v in _theme.THEMES.items() if v["name"]==chosen_label),
#                     "default")
#                 _theme.apply(chosen_key)
#                 _save_user("theme_override", chosen_key)
#                 if on_interval_change and hasattr(on_interval_change,"__self__"):
#                     dash = on_interval_change.__self__
#                     if hasattr(dash,"_rebuild_with_theme"):
#                         dash._root.after(50, dash._rebuild_with_theme)
#                 show_saved(f"Theme → {chosen_label} ✓")
#             _save_badge(p, save_theme)

#     _row(s5, "Active theme", _row_theme)

#     # ═══════════════════════════════════════════════════════════════════════
#     # Section 6 — About
#     # ═══════════════════════════════════════════════════════════════════════
#     s7 = _section(content, "ℹ  About")
#     about_row = tk.Frame(s7, bg=_c("CARD"))
#     about_row.pack(fill="x", padx=14, pady=10)
#     tk.Label(about_row,
#              text="Desktop Cat Companion  v1.0.0\nBuilt with Python + tkinter\nPhase 16 — Packaging complete",
#              font=fs, bg=_c("CARD"), fg=_c("SUB"), justify="left").pack(anchor="w")

#     # Bottom padding
#     tk.Frame(content, bg=_c("BG"), height=20).pack()



# ── features/settings.py ──────────────────────────────────────────────────────
# Phase 9: Settings — all preferences in one place
# Saves to user.xlsx + .env (for API keys/city)

import tkinter as tk
from tkinter import font as tkfont
import os, openpyxl, config

import theme as _theme_mod
def _c(k): return _theme_mod.get(k)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_user() -> dict:
    data = {}
    if not os.path.exists(config.USER_DATA): return data
    try:
        wb = openpyxl.load_workbook(config.USER_DATA)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            if row[0] and row[1] and row[0] != "key":
                data[str(row[0])] = str(row[1])
    except: pass
    return data

def _save_user(key: str, value: str):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    try:
        if os.path.exists(config.USER_DATA):
            wb = openpyxl.load_workbook(config.USER_DATA)
            ws = wb.active
            for row in ws.iter_rows():
                if row[0].value == key:
                    row[1].value = value
                    wb.save(config.USER_DATA); return
            ws.append([key, value])
            wb.save(config.USER_DATA)
        else:
            wb = openpyxl.Workbook(); ws = wb.active
            ws.title = "User"
            ws.append(["key","value"])
            ws.append([key, value])
            wb.save(config.USER_DATA)
    except Exception as e:
        print(f"[settings] user save: {e}")

# ── Section builder helper ─────────────────────────────────────────────────────
def _section(parent, title: str):
    """Returns the inner frame of a labelled section card."""
    tk.Label(parent, text=title,
             font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
             bg=_c("BG"), fg=_c("SUB")).pack(anchor="w", pady=(14,4))
    border = tk.Frame(parent, bg=_c("BORDER"))
    border.pack(fill="x")
    inner = tk.Frame(border, bg=_c("CARD"))
    inner.pack(fill="x", padx=1, pady=1)
    return inner

def _row(parent, label: str, widget_fn):
    """Build a label + widget row inside a section."""
    row = tk.Frame(parent, bg=_c("CARD"))
    row.pack(fill="x", padx=14, pady=8)
    tk.Label(row, text=label,
             font=tkfont.Font(family="Segoe UI", size=10),
             bg=_c("CARD"), fg=_c("TEXT"), width=22, anchor="w").pack(side="left")
    widget_fn(row)
    return row

def _entry_widget(parent, var: tk.StringVar, show=""):
    wrap = tk.Frame(parent, bg=_c("BORDER"))
    wrap.pack(side="left", fill="x", expand=True)
    e = tk.Entry(wrap, textvariable=var,
                 font=tkfont.Font(family="Segoe UI", size=10),
                 bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
                 relief="flat", bd=0, highlightthickness=0,
                 show=show)
    e.pack(fill="x", padx=1, pady=1, ipady=6)
    return e

def _save_badge(parent, fn):
    """Small Save button."""
    tk.Button(parent, text="Save",
              font=tkfont.Font(family="Segoe UI", size=9, weight="bold"),
              bg=_c("ACCENT"), fg=_c("BG"),
              activebackground=_c("TEXT"), activeforeground=_c("BG"),
              relief="flat", cursor="hand2", bd=0,
              command=fn).pack(side="left", padx=(8,0), ipady=4, ipadx=10)

# ── Main view ─────────────────────────────────────────────────────────────────
def build(parent: tk.Frame, root: tk.Tk, user: dict = None,
          cat_widget=None, on_name_change=None, on_interval_change=None,
          on_tile_update=None):
    if user is None: user = {}

    import supabase_config
    user_data = _load_user()

    fb  = tkfont.Font(family="Segoe UI", size=10)
    #fbn = tkfont.Font(family="Segoe UI", size=10, weight="bold")
    fs  = tkfont.Font(family="Segoe UI", size=9)

    # Feedback label at top
    feedback = tk.Label(parent, text="", font=fs, bg=_c("BG"), fg=_c("GREEN"))
    feedback.pack(anchor="w", pady=(0,4))

    def show_saved(msg="Settings saved ✓"):
        feedback.config(text=msg, fg=_c("GREEN"))
        parent.after(2500, lambda: feedback.config(text=""))

    def show_error(msg):
        feedback.config(text=msg, fg=_c("RED"))
        parent.after(2500, lambda: feedback.config(text=""))

    # ── Scrollable content ────────────────────────────────────────────────────
    outer = tk.Frame(parent, bg=_c("BG"))
    outer.pack(fill="both", expand=True)

    cv = tk.Canvas(outer, bg=_c("BG"), bd=0, highlightthickness=0)
    cv.pack(side="left", fill="both", expand=True)

    SB_W = 4
    sb = tk.Canvas(outer, width=SB_W, bg=_c("BG"), bd=0, highlightthickness=0)
    sb.pack(side="right", fill="y")
    thumb = sb.create_rectangle(0,0,SB_W,30, fill=_c("ACCENT"), outline="")

    content = tk.Frame(cv, bg=_c("BG"))
    cwin = cv.create_window((0,0), window=content, anchor="nw")

    def update_thumb(*_):
        try:
            t,b = cv.yview(); h=max(sb.winfo_height(),1)
            sb.coords(thumb,0,t*h,SB_W,max(b*h,t*h+14))
        except: pass

    def scroll(d): cv.yview_scroll(d,"units"); update_thumb()

    def _safe_scroll(e):
        top,bot=cv.yview()
        if top==0.0 and bot==1.0: return
        scroll(-1*(e.delta//120))
    for w in (cv,content,sb):
        w.bind("<MouseWheel>", _safe_scroll)

    def bind_scroll_recursive(widget):
        """Bind mouse wheel on every widget so scroll works everywhere."""
        def _safe_scroll(e):
            top, bot = cv.yview()
            if top == 0.0 and bot == 1.0: return
            scroll(-1*(e.delta//120))
        try:
            widget.bind("<MouseWheel>", _safe_scroll)
        except Exception: pass
        for child in widget.winfo_children():
            bind_scroll_recursive(child)

    # Re-bind after content is fully built
    def _bind_all_scroll():
        bind_scroll_recursive(content)
    content.bind("<Configure>", lambda e: [
        cv.configure(scrollregion=cv.bbox("all")),
        update_thumb(),
        _bind_all_scroll()
    ])

    def sb_drag(e):
        t,b=cv.yview(); h=max(sb.winfo_height(),1)
        cv.yview_moveto(max(0,e.y/h-(b-t)/2)); update_thumb()
    sb.bind("<ButtonPress-1>",sb_drag); sb.bind("<B1-Motion>",sb_drag)
    cv.bind("<Configure>", lambda e: [
        cv.itemconfig(cwin,width=e.width), update_thumb()])

    # ═══════════════════════════════════════════════════════════════════════
    # Section 1 — Profile
    # ═══════════════════════════════════════════════════════════════════════
    s1 = _section(content, "👤  Profile")

    name_var = tk.StringVar(value=user.get("name", user_data.get("name","Friend")))
    def _row_name(p):
        _entry_widget(p, name_var)
        def save_name():
            n = name_var.get().strip()
            if not n: show_error("Name cannot be empty."); return
            _save_user("name", n)
            user["name"] = n
            if on_name_change: on_name_change(n)
            show_saved("Name updated ✓")
        _save_badge(p, save_name)
    _row(s1, "Your name", _row_name)

    # ═══════════════════════════════════════════════════════════════════════
    # Section 2 — Health reminders
    # ═══════════════════════════════════════════════════════════════════════
    s2 = _section(content, "💧  Health reminders")

    water_var   = tk.StringVar(value=user_data.get("water_interval",   str(config.WATER_INTERVAL_MIN)))
    break_var   = tk.StringVar(value=user_data.get("break_interval",   str(config.BREAK_INTERVAL_MIN)))
    stretch_var = tk.StringVar(value=user_data.get("stretch_interval", str(config.STRETCH_INTERVAL_MIN)))

    def _interval_widget(p, var, key, label_suffix="min"):
        wrap = tk.Frame(p, bg=_c("BORDER"))
        wrap.pack(side="left")
        e = tk.Entry(wrap, textvariable=var,
                     font=fb, bg=_c("CARD"), fg=_c("TEXT"),
                     insertbackground=_c("ACCENT"),
                     relief="flat", bd=0, highlightthickness=0,
                     width=5, justify="center")
        e.pack(padx=1, pady=1, ipady=6)
        tk.Label(p, text=label_suffix, font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(side="left", padx=(4,0))

    def _row_water(p):
        _interval_widget(p, water_var, "water_interval")
        def save():
            try:
                v = int(water_var.get())
                assert 1 <= v <= 300
                _save_user("water_interval", str(v))
                config.WATER_INTERVAL_MIN = v
                if on_interval_change: on_interval_change("water", v)
                show_saved("Water reminder updated ✓")
            except: show_error("Enter a number between 1–300.")
        _save_badge(p, save)

    def _row_break(p):
        _interval_widget(p, break_var, "break_interval")
        def save():
            try:
                v = int(break_var.get())
                assert 1 <= v <= 300
                _save_user("break_interval", str(v))
                config.BREAK_INTERVAL_MIN = v
                if on_interval_change: on_interval_change("break", v)
                show_saved("Break reminder updated ✓")
            except: show_error("Enter a number between 1–300.")
        _save_badge(p, save)

    def _row_stretch(p):
        _interval_widget(p, stretch_var, "stretch_interval")
        def save():
            try:
                v = int(stretch_var.get())
                assert 1 <= v <= 300
                _save_user("stretch_interval", str(v))
                config.STRETCH_INTERVAL_MIN = v
                if on_interval_change: on_interval_change("stretch", v)
                show_saved("Stretch reminder updated ✓")
            except: show_error("Enter a number between 1–300.")
        _save_badge(p, save)

    _row(s2, "Drink water every",  _row_water)
    _row(s2, "Short break every",  _row_break)
    _row(s2, "Stretch every",      _row_stretch)

    # Enable/disable toggles
    toggle_row = tk.Frame(s2, bg=_c("CARD"))
    toggle_row.pack(fill="x", padx=14, pady=(4,10))
    tk.Label(toggle_row, text="Notifications:",
             font=tkfont.Font(family="Segoe UI", size=10),
             bg=_c("CARD"), fg=_c("TEXT"), width=22, anchor="w").pack(side="left")

    for key, label in [("water","Water"), ("break","Break"), ("stretch","Stretch")]:
        enabled_now = True
        if on_interval_change and hasattr(on_interval_change, '__self__'):
            eng = getattr(on_interval_change.__self__, '_health_engine', None)
            if eng:
                enabled_now = eng.is_enabled(key)
        var = tk.BooleanVar(value=enabled_now)
        cell = tk.Frame(toggle_row, bg=_c("CARD"))
        cell.pack(side="left", padx=(0,12))
        def make_toggle(k=key, v=var):
            def toggle():
                if on_interval_change and hasattr(on_interval_change, '__self__'):
                    eng = getattr(on_interval_change.__self__, '_health_engine', None)
                    if eng:
                        eng.set_enabled(k, v.get())
                        show_saved(f"{k.capitalize()} notifications {'on' if v.get() else 'off'} ✓")
            return toggle
        tk.Checkbutton(cell, text=label,
                       variable=var,
                       command=make_toggle(),
                       font=tkfont.Font(family="Segoe UI", size=9),
                       bg=_c("CARD"), fg=_c("TEXT"), selectcolor=_c("CARD"),
                       activebackground=_c("CARD"), activeforeground=_c("ACCENT"),
                       cursor="hand2", bd=0).pack(side="left")

    # ═══════════════════════════════════════════════════════════════════════
    # Section 3 — Cat behaviour
    # ═══════════════════════════════════════════════════════════════════════
    s3 = _section(content, "🐱  Cat behaviour")

    speed_var = tk.StringVar(value=user_data.get("cat_speed", str(config.WALK_SPEED)))

    def _row_speed(p):
        wrap = tk.Frame(p, bg=_c("BORDER"))
        wrap.pack(side="left")
        e = tk.Entry(wrap, textvariable=speed_var,
                     font=fb, bg=_c("CARD"), fg=_c("TEXT"),
                     insertbackground=_c("ACCENT"),
                     relief="flat", bd=0, highlightthickness=0,
                     width=5, justify="center")
        e.pack(padx=1, pady=1, ipady=6)
        tk.Label(p, text="px/tick", font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(side="left", padx=(4,0))
        def save():
            try:
                v = int(speed_var.get())
                assert 1 <= v <= 20
                _save_user("cat_speed", str(v))
                config.WALK_SPEED = v
                show_saved("Cat speed updated ✓")
            except: show_error("Enter a speed between 1–20.")
        _save_badge(p, save)
    _row(s3, "Walking speed", _row_speed)

    # ═══════════════════════════════════════════════════════════════════════
    # Section 4 — Weather
    # ═══════════════════════════════════════════════════════════════════════
    s4 = _section(content, "🌤  Weather")

    # Read city: user's saved preference first, then Supabase default
    _saved_city = user_data.get("weather_city", "") or supabase_config.get_key("City", "Bengaluru")
    city_var    = tk.StringVar(value=_saved_city)

    # Major Indian cities for autocomplete
    CITY_SUGGESTIONS = [
        "Bengaluru","Mumbai","Delhi","Chennai","Hyderabad","Kolkata","Pune",
        "Ahmedabad","Jaipur","Lucknow","Surat","Kanpur","Nagpur","Indore",
        "Bhopal","Visakhapatnam","Patna","Vadodara","Coimbatore","Agra",
        "New York","London","Tokyo","Sydney","Dubai","Singapore","Paris",
    ]

    def _row_city(p):
        # Use a frame to hold entry + dropdown
        city_frame = tk.Frame(p, bg=_c("CARD"))
        city_frame.pack(side="left", fill="x", expand=True, padx=(0,0))

        entry_wrap = tk.Frame(city_frame, bg=_c("BORDER"))
        entry_wrap.pack(fill="x")
        city_entry = tk.Entry(entry_wrap, textvariable=city_var,
                              font=tkfont.Font(family="Segoe UI", size=10),
                              bg=_c("CARD"), fg=_c("TEXT"), insertbackground=_c("ACCENT"),
                              relief="flat", bd=0, highlightthickness=0)
        city_entry.pack(fill="x", padx=1, pady=1, ipady=6)

        # Autocomplete dropdown
        suggest_lb = None

        def on_type(*_):
            nonlocal suggest_lb
            typed = city_var.get().strip().lower()
            if suggest_lb:
                try: suggest_lb.destroy()
                except: pass
                suggest_lb = None
            if not typed or len(typed) < 2: return
            matches = [c for c in CITY_SUGGESTIONS if typed in c.lower()][:6]
            if not matches: return
            suggest_lb = tk.Listbox(
                city_frame, font=tkfont.Font(family="Segoe UI", size=9),
                bg=_c("CARD"), fg=_c("TEXT"), selectbackground=_c("ACCENT"), selectforeground=_c("BG"),
                relief="flat", bd=0, highlightthickness=1,
                highlightcolor=_c("BORDER"), height=len(matches))
            suggest_lb.pack(fill="x")
            for m in matches: suggest_lb.insert("end", m)
            def pick(e):
                nonlocal suggest_lb
                sel = suggest_lb.curselection()
                if sel: city_var.set(suggest_lb.get(sel[0]))
                try: suggest_lb.destroy()
                except: pass
                suggest_lb = None
            suggest_lb.bind("<<ListboxSelect>>", pick)
            suggest_lb.bind("<Return>", pick)

        city_var.trace_add("write", on_type)

        def save():
            nonlocal suggest_lb
            if suggest_lb:
                try: suggest_lb.destroy()
                except: pass
                suggest_lb = None
            v = city_var.get().strip()
            if not v: show_error("City cannot be empty."); return
            # Save city to user.xlsx — stored as plain name (e.g. "Chennai")
            _save_user("weather_city", v)
            print(f"[settings] weather_city saved: {v}")
            # Invalidate weather cache so next open fetches fresh data
            import json
            try:
                with open(os.path.join(config.DATA_DIR,"weather_cache.json"),"w") as f:
                    json.dump({},f)
            except: pass
            # Update tile subtitle live — pass "Chennai, IN" format
            display = f"{v}, IN"
            if on_tile_update: on_tile_update("weather", display)
            show_saved(f"City updated to {v} ✓")
        _save_badge(p, save)

    _row(s4, "City", _row_city)

    # Weather API key is managed via .env file directly

    # ═══════════════════════════════════════════════════════════════════════
    # Section 5 — Theme
    # Predefined character (name matches a theme key) → read-only label
    # Custom/unknown character → editable dropdown, persists selection
    # ═══════════════════════════════════════════════════════════════════════
    import theme as _theme, os as _os, openpyxl as _opxl
    from features.character import get_active_character

    _active_path   = get_active_character()
    theme_is_locked = _theme.is_predefined(_active_path)

    # Read saved override for custom characters
    _saved_override = ""
    try:
        if _os.path.exists(config.USER_DATA):
            _wb = _opxl.load_workbook(config.USER_DATA)
            for _r in _wb.active.iter_rows(values_only=True):
                if _r[0] == "theme_override" and _r[1]:
                    _saved_override = str(_r[1]); break
    except Exception: pass

    # What to show: for locked use auto-key, for custom use live theme (set by dropdown save)
    _current_live   = _theme.name()   # always the currently active theme name
    _locked_key     = _theme.theme_for_character(_active_path)
    _locked_label   = _theme.THEMES.get(_locked_key, _theme.THEMES["default"])["name"]
    # For dropdown: show last saved override, or current live theme
    _dropdown_key   = _saved_override if _saved_override in _theme.THEMES else _theme.theme_for_character(_active_path)
    _dropdown_label = _theme.THEMES.get(_dropdown_key, _theme.THEMES["default"])["name"]

    s5 = _section(content, "🎨  Theme")

    theme_names  = {k: v["name"] for k,v in _theme.THEMES.items()}
    theme_labels = list(theme_names.values())
    theme_var    = tk.StringVar(value=_dropdown_label)  # persists last selection

    def _row_theme(p):
        if theme_is_locked:
            # Read-only — predefined character, theme auto-applied
            info_f = tk.Frame(p, bg=_c("CARD"))
            info_f.pack(side="left", fill="x", expand=True)
            tk.Label(info_f, text=_locked_label,
                     font=tkfont.Font(family="Segoe UI", size=10),
                     bg=_c("CARD"), fg=_c("TEXT")).pack(side="left", padx=6, pady=6)
            tk.Label(info_f, text="(auto — set by character)",
                     font=tkfont.Font(family="Segoe UI", size=9),
                     bg=_c("CARD"), fg=_c("SUB")).pack(side="left")
        else:
            # Editable dropdown — custom character picks any theme
            wrap = tk.Frame(p, bg=_c("CARD"))
            wrap.pack(side="left", fill="x", expand=True)
            om = tk.OptionMenu(wrap, theme_var, *theme_labels)
            om.config(bg=_c("BORDER"), fg=_c("TEXT"),
                      activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                      highlightthickness=0, relief="flat", bd=0,
                      font=tkfont.Font(family="Segoe UI", size=10),
                      cursor="hand2")
            om["menu"].config(bg=_c("CARD"), fg=_c("TEXT"),
                              activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                              font=tkfont.Font(family="Segoe UI", size=9))
            om.pack(fill="x", padx=4, pady=4)

            def save_theme():
                chosen_label = theme_var.get()
                chosen_key   = next(
                    (k for k,v in _theme.THEMES.items() if v["name"]==chosen_label),
                    "default")
                _theme.apply(chosen_key)
                _save_user("theme_override", chosen_key)
                if on_interval_change and hasattr(on_interval_change,"__self__"):
                    dash = on_interval_change.__self__
                    if hasattr(dash,"_rebuild_with_theme"):
                        dash._root.after(50, dash._rebuild_with_theme)
                show_saved(f"Theme → {chosen_label} ✓")
            _save_badge(p, save_theme)

    _row(s5, "Active theme", _row_theme)

    # ═══════════════════════════════════════════════════════════════════════
    # Section 6 — About
    # ═══════════════════════════════════════════════════════════════════════
    s7 = _section(content, "ℹ  About")
    about_row = tk.Frame(s7, bg=_c("CARD"))
    about_row.pack(fill="x", padx=14, pady=10)
    tk.Label(about_row,
             text="Desktop Cat Companion  v1.0.0\nBuilt with Python + tkinter\nPhase 16 — Packaging complete",
             font=fs, bg=_c("CARD"), fg=_c("SUB"), justify="left").pack(anchor="w")

    # Bottom padding
    tk.Frame(content, bg=_c("BG"), height=20).pack()

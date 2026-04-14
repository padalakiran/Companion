# ── features/pomodoro.py ──────────────────────────────────────────────────────
# Patches:
#  1. Mode tabs larger, control buttons smaller
#  2. Timer keeps running in background when navigating away
#  3. Reset resets in place — no popup
#  4. Click centre of timer circle to edit custom time inline

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime, date
import threading, time, os, openpyxl, config

_T=__import__("theme"); BG=_T.get("BG"); CARD=_T.get("CARD"); BORDER=_T.get("BORDER"); ACCENT=_T.get("ACCENT"); TEXT=_T.get("TEXT"); SUB=_T.get("SUB"); GREEN=_T.get("GREEN"); RED=_T.get("RED"); YELLOW=_T.get("YELLOW"); ORANGE=_T.get("ORANGE")

# MODES defined as function so icon is always live from theme
def _get_modes():
    import theme as _t
    return {
        "work":        {"label": "Focus",       "mins": 25, "color": _t.get("ACCENT"), "icon": _t.icon()},
        "short_break": {"label": "Short Break", "mins": 5,  "color": _t.get("GREEN"),  "icon": "☕"},
        "long_break":  {"label": "Long Break",  "mins": 15, "color": _t.get("YELLOW"), "icon": "🧘"},
    }
MODES = _get_modes()
POMODORO_DATA = os.path.join(config.DATA_DIR, "pomodoro.xlsx")

# ── Shared background state (persists across view rebuilds) ───────────────────
# This dict lives at module level so the timer keeps going after back navigation
_bg = {
    "mode":       "work",
    "running":    False,
    "paused":     False,
    "seconds":    25 * 60,
    "total":      25 * 60,
    "pomodoros":  0,
    "custom_mins":None,
    "thread":     None,
    "root":       None,
    "notify_fn":  None,
    "listeners":  [],          # callbacks to update the UI when view is open
}

# ── Excel helpers ─────────────────────────────────────────────────────────────
def _init_wb():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(POMODORO_DATA):
        wb = openpyxl.Workbook(); ws = wb.active
        ws.title = "Sessions"
        ws.append(["date","mode","duration_min","completed","time"])
        wb.save(POMODORO_DATA)

def _log(mode: str, completed: bool):
    _init_wb()
    try:
        wb = openpyxl.load_workbook(POMODORO_DATA); ws = wb.active
        ws.append([str(date.today()), mode,
                   MODES.get(mode,{}).get("mins",0),
                   completed, datetime.now().strftime("%H:%M")])
        wb.save(POMODORO_DATA)
    except Exception as e:
        print(f"[pomodoro] log: {e}")

def _load_today():
    _init_wb(); rows = []
    today = str(date.today())
    try:
        wb = openpyxl.load_workbook(POMODORO_DATA); ws = wb.active
        for i,r in enumerate(ws.iter_rows(values_only=True)):
            if i==0 or not r[0]: continue
            if str(r[0])==today:
                rows.append({"mode":r[1],"mins":r[2],
                             "completed":r[3],"time":r[4]})
    except Exception as e:
        print(f"[pomodoro] load: {e}")
    return rows

# ── Arc drawing ───────────────────────────────────────────────────────────────
def _draw_arc(canvas, frac: float, color: str, size: int):
    canvas.delete("timer_arc","timer_dot")
    cx = cy = size // 2
    r  = size // 2 - 16
    canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                       outline=BORDER, width=10, fill="", tags="timer_arc")
    if frac > 0.001:
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=90, extent=-frac*360,
                          outline=color, width=10,
                          style="arc", tags="timer_arc")
    canvas.create_oval(cx-5, cy-5, cx+5, cy+5,
                       fill=color, outline="", tags="timer_dot")

def _fmt(secs):
    m,s = divmod(max(secs,0), 60)
    return f"{m:02d}:{s:02d}"

# ── Background tick thread ─────────────────────────────────────────────────────
def _ensure_thread():
    """Start the background tick thread if not already running."""
    if _bg["thread"] and _bg["thread"].is_alive():
        return
    t = threading.Thread(target=_tick_loop, daemon=True)
    _bg["thread"] = t
    t.start()

def _tick_loop():
    while True:
        time.sleep(0.25)
        if not _bg["running"]:
            continue
        _bg["seconds"] -= 0.25
        if _bg["seconds"] <= 0:
            _bg["seconds"] = 0
            _bg["running"] = False
            _on_complete_bg()
        # Notify all live UI listeners
        for fn in list(_bg["listeners"]):
            try:
                fn()
            except Exception:
                _bg["listeners"].discard(fn) if hasattr(_bg["listeners"],"discard") else None

def _on_complete_bg():
    global MODES; MODES = _get_modes()  # refresh theme-based colours/icons
    mode = _bg["mode"]
    info = MODES.get(mode, MODES["work"])
    _log(mode, completed=True)

    if mode == "work":
        _bg["pomodoros"] += 1
        next_m = "long_break" if _bg["pomodoros"] % 4 == 0 else "short_break"
        msg    = f"Great focus! Time for a {MODES[next_m]['label'].lower()}."
    else:
        next_m = "work"
        msg    = "Break over — time to focus again! 💪"

    # Fire notification via root.after (thread-safe)
    root = _bg.get("root")
    nfn  = _bg.get("notify_fn")
    if root and nfn:
        try:
            root.after(0, lambda: nfn(
                f"{info['icon']} {info['label']} complete!", msg, info["color"]))
        except Exception:
            pass

    # Auto-switch mode
    _set_mode_bg(next_m)

def _set_mode_bg(m, custom_mins=None):
    _bg["mode"]        = m
    _bg["custom_mins"] = custom_mins
    mins = custom_mins if custom_mins else MODES[m]["mins"]
    _bg["seconds"]     = mins * 60
    _bg["total"]       = mins * 60
    _bg["running"]     = False
    _bg["paused"]      = False

# ── View builder ──────────────────────────────────────────────────────────────
def build(parent: tk.Frame, root: tk.Tk, notify_fn=None):
    import theme; theme.refresh(globals())
    ARC = 210

    # Store root & notify in shared state
    _bg["root"]      = root
    _bg["notify_fn"] = notify_fn

    # Start background thread (idempotent)
    _ensure_thread()

    fhbig = tkfont.Font(family="Segoe UI", size=11, weight="bold")  # mode tabs
    fh    = tkfont.Font(family="Segoe UI", size=12, weight="bold")
    ft    = tkfont.Font(family="Segoe UI", size=36, weight="bold")
    fs    = tkfont.Font(family="Segoe UI", size=9)                   # control btns
    fb    = tkfont.Font(family="Segoe UI", size=9)
    fsl   = tkfont.Font(family="Segoe UI", size=9)
    fedit = tkfont.Font(family="Segoe UI", size=22, weight="bold")   # inline edit

    # ── Mode tabs (larger) ────────────────────────────────────────────────────
    tab_row = tk.Frame(parent, bg=BG)
    tab_row.pack(pady=(0, 10))
    mode_btns = {}

    def refresh_tabs():
        m = _bg["mode"]
        for k, b in mode_btns.items():
            color = MODES[k]["color"]
            b.config(bg=color if k==m else BORDER,
                     fg=BG    if k==m else SUB)

    def set_mode(m):
        if _bg["running"]: return
        _set_mode_bg(m)
        refresh_tabs()
        mode_lbl.config(text=MODES[m]["label"], fg=MODES[m]["color"])
        refresh_display()

    for m, info in MODES.items():
        is_sel = (m == _bg["mode"])
        btn = tk.Button(tab_row, text=info["label"],
                        font=fhbig,
                        bg=info["color"] if is_sel else BORDER,
                        fg=BG if is_sel else SUB,
                        activebackground=info["color"], activeforeground=BG,
                        relief="flat", cursor="hand2", bd=0,
                        command=lambda k=m: set_mode(k))
        btn.pack(side="left", padx=4, ipady=8, ipadx=16)   # bigger tabs
        mode_btns[m] = btn

    # ── Mode label ────────────────────────────────────────────────────────────
    cur_info = MODES[_bg["mode"]]
    mode_lbl = tk.Label(parent,
                        text=cur_info["label"],
                        font=fh, bg=BG, fg=cur_info["color"])
    mode_lbl.pack()

    # ── Arc canvas ────────────────────────────────────────────────────────────
    arc_cv = tk.Canvas(parent, width=ARC, height=ARC,
                       bg=BG, bd=0, highlightthickness=0)
    arc_cv.pack(pady=4)

    frac = _bg["seconds"] / _bg["total"] if _bg["total"] > 0 else 1.0
    _draw_arc(arc_cv, frac, cur_info["color"], ARC)

    # Timer text on canvas (no bg rectangle)
    timer_id = arc_cv.create_text(
        ARC//2, ARC//2,
        text=_fmt(int(_bg["seconds"])),
        font=ft,
        fill=cur_info["color"],
        tags="timer_text"
    )

    # Hint text below timer
    hint_id = arc_cv.create_text(
        ARC//2, ARC//2 + 36,
        text="click to edit",
        font=fsl,
        fill=BORDER,
        tags="hint_text"
    )

    # ── Inline edit overlay ───────────────────────────────────────────────────
    edit_frame = None   # will hold the entry frame when editing

    def open_inline_edit(event=None):
        nonlocal edit_frame
        if _bg["running"]: return
        if edit_frame and edit_frame.winfo_exists():
            return

        color = MODES[_bg["mode"]]["color"]
        # Place an Entry widget directly over the canvas centre
        # Distinct background so edit doesn't merge with timer text
        edit_frame = tk.Frame(parent, bg=ACCENT, bd=0)
        edit_frame.place(in_=arc_cv,
                         relx=0.5, rely=0.5,
                         anchor="center",
                         width=160, height=70)
        inner_edit = tk.Frame(edit_frame, bg=BG, bd=0)
        inner_edit.place(x=2, y=2, width=156, height=66)

        # Minutes field
        min_var = tk.StringVar(value=str(int(_bg["total"]//60)))
        sec_var = tk.StringVar(value=str(int(_bg["total"]%60)).zfill(2))

        row_f = tk.Frame(inner_edit, bg=BG)
        row_f.pack(expand=True, pady=6)

        min_entry = tk.Entry(row_f, textvariable=min_var,
                             font=fedit, bg=BG, fg=color,
                             insertbackground=color, relief="flat", bd=0,
                             justify="center", highlightthickness=0, width=3)
        min_entry.pack(side="left", padx=(4,0))
        tk.Label(row_f, text="m", font=fs, bg=BG, fg=SUB).pack(side="left")

        sec_entry = tk.Entry(row_f, textvariable=sec_var,
                             font=fedit, bg=BG, fg=color,
                             insertbackground=color, relief="flat", bd=0,
                             justify="center", highlightthickness=0, width=3)
        sec_entry.pack(side="left", padx=(6,0))
        tk.Label(row_f, text="s", font=fs, bg=BG, fg=SUB).pack(side="left", padx=(0,4))

        min_entry.select_range(0, "end")
        min_entry.focus()

        def confirm(*_):
            nonlocal edit_frame
            try:
                m = max(0, min(180, int(min_var.get().strip() or "0")))
                s = max(0, min(59,  int(sec_var.get().strip() or "0")))
                total_secs = m*60 + s
                if total_secs > 0:
                    _bg["mode"]        = _bg["mode"]
                    _bg["custom_mins"] = None
                    _bg["seconds"]     = total_secs
                    _bg["total"]       = total_secs
                    mode_lbl.config(
                        text=f"{MODES[_bg['mode']]['label']} ({m}m {s:02d}s)" if s else
                             f"{MODES[_bg['mode']]['label']} ({m}m)")
            except ValueError:
                pass
            if edit_frame and edit_frame.winfo_exists():
                edit_frame.destroy()
            edit_frame = None
            refresh_display()

        def cancel(event=None):
            nonlocal edit_frame
            if edit_frame and edit_frame.winfo_exists():
                edit_frame.destroy()
            edit_frame = None

        min_entry.bind("<Return>", confirm)
        sec_entry.bind("<Return>", confirm)
        min_entry.bind("<Tab>", lambda e: sec_entry.focus())
        min_entry.bind("<Escape>", cancel)
        sec_entry.bind("<Escape>", cancel)
        sec_entry.bind("<FocusOut>", lambda e: inner_edit.after(100, lambda: confirm() if edit_frame and edit_frame.winfo_exists() else None))

    # Bind click on the centre dot / timer text to open inline edit
    arc_cv.tag_bind("timer_text", "<Button-1>", open_inline_edit)
    arc_cv.tag_bind("timer_dot",  "<Button-1>", open_inline_edit)
    arc_cv.tag_bind("hint_text",  "<Button-1>", open_inline_edit)
    # Also bind click anywhere in the inner half of the arc
    arc_cv.bind("<Button-1>", lambda e, s=ARC//2: (
        open_inline_edit() if ((e.x-s)**2+(e.y-s)**2) < (s*0.55)**2 else None
    ))

    # ── Controls (smaller) ────────────────────────────────────────────────────
    ctrl_row = tk.Frame(parent, bg=BG)
    ctrl_row.pack(pady=8)

    start_btn = tk.Button(ctrl_row, text="▶  Start", font=fb,
                          bg=ACCENT, fg=BG,
                          activebackground=TEXT, activeforeground=BG,
                          relief="flat", cursor="hand2", bd=0,
                          command=lambda: toggle_timer())
    start_btn.pack(side="left", padx=4, ipady=5, ipadx=14)

    tk.Button(ctrl_row, text="↺  Reset", font=fb,
              bg=BORDER, fg=SUB,
              activebackground=BORDER, activeforeground=TEXT,
              relief="flat", cursor="hand2", bd=0,
              command=lambda: reset_timer()
              ).pack(side="left", padx=4, ipady=5, ipadx=14)

    # ── Pomodoro dots ─────────────────────────────────────────────────────────
    dots_lbl = tk.Label(parent, text="○○○○", font=fs, bg=BG, fg=ACCENT)
    dots_lbl.pack(pady=(4,0))
    sess_lbl = tk.Label(parent, text="0 pomodoros completed today",
                        font=fsl, bg=BG, fg=SUB)
    sess_lbl.pack(pady=(2,0))

    # ── History ───────────────────────────────────────────────────────────────
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(12,6))
    tk.Label(parent, text="Today's sessions", font=fh, bg=BG, fg=SUB).pack(anchor="w")
    hist_f = tk.Frame(parent, bg=BG)
    hist_f.pack(fill="both", expand=True)

    # ── Refresh helpers ───────────────────────────────────────────────────────

    def refresh_display():
        if not arc_cv.winfo_exists(): return
        secs  = int(_bg["seconds"])
        total = _bg["total"]
        frac  = secs/total if total>0 else 1.0
        color = MODES[_bg["mode"]]["color"]
        try:
            _draw_arc(arc_cv, frac, color, ARC)
            arc_cv.itemconfig(timer_id, text=_fmt(secs), fill=color)
            # Update start button label
            if _bg["running"]:
                start_btn.config(text="⏸  Pause", bg=ORANGE, fg=BG)
            elif _bg["paused"]:
                start_btn.config(text="▶  Resume", bg=ACCENT, fg=BG)
            else:
                start_btn.config(text="▶  Start", bg=ACCENT, fg=BG)
        except tk.TclError:
            pass

    def refresh_dots():
        if not dots_lbl.winfo_exists(): return
        rows = _load_today()
        done = [r for r in rows if r["mode"]=="work" and r["completed"]]
        n    = len(done)
        dots = "🍅" * n + "○" * max(0, 4-n)
        try:
            dots_lbl.config(text=dots)
            sess_lbl.config(text=f"{n} pomodoro{'s' if n!=1 else ''} completed today")
            refresh_history(rows)
        except tk.TclError:
            pass

    def refresh_history(rows=None):
        if not hist_f.winfo_exists(): return
        for w in hist_f.winfo_children(): w.destroy()
        if rows is None: rows = _load_today()
        if not rows:
            tk.Label(hist_f, text="No sessions yet — start your first!",
                     font=fsl, bg=BG, fg=BORDER).pack(pady=8)
            return
        for r in reversed(rows[-8:]):
            m    = r.get("mode","work")
            info = MODES.get(m, MODES["work"])
            col  = info["color"] if r["completed"] else BORDER
            tag  = "✓" if r["completed"] else "✗"
            row  = tk.Frame(hist_f, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=info["icon"], font=fs,
                     bg=BG, fg=col).pack(side="left", padx=(0,6))
            tk.Label(row, text=f"{info['label']} — {r.get('mins',0)} min",
                     font=fs, bg=BG, fg=TEXT).pack(side="left")
            tk.Label(row, text=f"{tag}  {r.get('time','')}",
                     font=fsl, bg=BG, fg=col).pack(side="right")

    # ── Timer controls ────────────────────────────────────────────────────────

    def toggle_timer():
        if not _bg["running"]:
            _bg["running"] = True
            _bg["paused"]  = False
            _ensure_thread()
        else:
            _bg["running"] = False
            _bg["paused"]  = True
        refresh_display()

    def reset_timer():
        _bg["running"] = False
        _bg["paused"]  = False
        m    = _bg["mode"]
        mins = _bg["custom_mins"] if _bg["custom_mins"] else MODES[m]["mins"]
        _bg["seconds"] = mins * 60
        _bg["total"]   = mins * 60
        refresh_display()

    # ── Register this view as a listener for background ticks ─────────────────
    # Use a mutable container so the closure captures the right reference
    listener_active = [True]

    def on_tick():
        if not listener_active[0]: return
        try:
            if arc_cv.winfo_exists():
                refresh_display()
            else:
                listener_active[0] = False
                _bg["listeners"].remove(on_tick)
        except (tk.TclError, ValueError):
            listener_active[0] = False
            try: _bg["listeners"].remove(on_tick)
            except ValueError: pass

    if on_tick not in _bg["listeners"]:
        _bg["listeners"].append(on_tick)

    # When this view is destroyed (back arrow), deregister listener
    def on_destroy(event):
        if event.widget is parent:
            listener_active[0] = False
            try: _bg["listeners"].remove(on_tick)
            except ValueError: pass
    parent.bind("<Destroy>", on_destroy)

    # Initial render
    refresh_display()
    refresh_dots()

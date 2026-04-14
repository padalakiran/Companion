# ── features/planner.py ───────────────────────────────────────────────────────
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime, date, timedelta
import os, openpyxl, config

_notified: set = set()
_timer_running: bool = False

import theme as _theme_mod
def _c(k): return _theme_mod.get(k)

# 00:00 → 23:30 in 30-min steps
SLOTS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0,30)]

# ── Excel helpers ─────────────────────────────────────────────────────────────
def _init():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(config.PLANNER_DATA):
        wb=openpyxl.Workbook(); ws=wb.active
        ws.title="Planner"
        ws.append(["id","date","time","title","done"])
        wb.save(config.PLANNER_DATA)

def _load(target_date:str):
    _init(); rows=[]
    try:
        wb=openpyxl.load_workbook(config.PLANNER_DATA); ws=wb.active
        for i,r in enumerate(ws.iter_rows(values_only=True)):
            if i==0 or not r[0]: continue
            if str(r[1])==target_date:
                rows.append({"id":r[0],"date":str(r[1]),
                             "time":str(r[2]),"title":str(r[3]),
                             "done":bool(r[4])})
    except Exception as e: print(f"[planner] load: {e}")
    return rows

def _save_new(ev):
    _init()
    try:
        wb=openpyxl.load_workbook(config.PLANNER_DATA); ws=wb.active
        ws.append([ev["id"],ev["date"],ev["time"],ev["title"],ev["done"]])
        wb.save(config.PLANNER_DATA)
    except Exception as e: print(f"[planner] save: {e}")

def _update(ev):
    _init()
    try:
        wb=openpyxl.load_workbook(config.PLANNER_DATA); ws=wb.active
        for row in ws.iter_rows():
            if row[0].value==ev["id"]:
                row[2].value=ev["time"]; row[3].value=ev["title"]
                row[4].value=ev["done"]; break
        wb.save(config.PLANNER_DATA)
    except Exception as e: print(f"[planner] update: {e}")

def _delete(eid):
    _init()
    try:
        wb=openpyxl.load_workbook(config.PLANNER_DATA); ws=wb.active
        for row in ws.iter_rows():
            if row[0].value==eid:
                ws.delete_rows(row[0].row); break
        wb.save(config.PLANNER_DATA)
    except Exception as e: print(f"[planner] delete: {e}")

def _next_id():
    _init()
    try:
        wb=openpyxl.load_workbook(config.PLANNER_DATA); ws=wb.active
        ids=[r[0].value for r in ws.iter_rows() if isinstance(r[0].value,int)]
        return max(ids,default=0)+1
    except: return 1

# ── Scrollable frame helper ───────────────────────────────────────────────────
def _make_scroll_area(parent):
    """Returns (inner_frame, update_thumb_fn). Custom 4px accent scrollbar."""
    outer = tk.Frame(parent, bg=_c("BG"))
    outer.pack(fill="both", expand=True)

    cv = tk.Canvas(outer, bg=_c("BG"), bd=0, highlightthickness=0)
    cv.pack(side="left", fill="both", expand=True)

    # 4px accent scrollbar
    SB_W = 5
    sb_cv = tk.Canvas(outer, width=SB_W, bg=_c("BG"), bd=0,
                      highlightthickness=0)
    sb_cv.pack(side="right", fill="y", padx=(2,0))
    thumb = sb_cv.create_rectangle(0,0,SB_W,30, fill=_c("ACCENT"), outline="")

    inner = tk.Frame(cv, bg=_c("BG"))
    win   = cv.create_window((0,0), window=inner, anchor="nw")

    def update_thumb():
        try:
            top,bot = cv.yview()
            h = sb_cv.winfo_height()
            if h < 2: return
            sb_cv.coords(thumb, 0, top*h, SB_W, max(bot*h, top*h+14))
        except: pass

    def on_scroll(delta):
        top, bot = cv.yview()
        if top == 0.0 and bot == 1.0: return   # content fits, nothing to scroll
        cv.yview_scroll(delta, "units")
        update_thumb()

    # Mouse wheel on canvas AND inner frame AND sb_cv
    for w in (cv, inner, sb_cv):
        w.bind("<MouseWheel>",
               lambda e: on_scroll(-1*(e.delta//120)))

    # Drag scrollbar thumb
    def sb_drag(e):
        top,bot = cv.yview()
        span = bot-top
        h = max(sb_cv.winfo_height(),1)
        cv.yview_moveto(max(0, e.y/h - span/2))
        update_thumb()

    sb_cv.bind("<ButtonPress-1>", sb_drag)
    sb_cv.bind("<B1-Motion>",     sb_drag)

    def _on_inner_configure(e):
        bb = cv.bbox("all")
        if bb: cv.configure(scrollregion=(0,0,bb[2],bb[3]))
        update_thumb()
    inner.bind("<Configure>", _on_inner_configure)
    cv.bind("<Configure>", lambda e: [
        cv.itemconfig(win, width=e.width),
        update_thumb()
    ])

    return inner, update_thumb, cv

# ── Main view ─────────────────────────────────────────────────────────────────
def build(parent:tk.Frame, root:tk.Tk, notify_fn=None):
    today   = date.today()
    cur     = {"date": today}

    fh  = tkfont.Font(family="Segoe UI", size=11, weight="bold")
    fb  = tkfont.Font(family="Segoe UI", size=10)
    fs  = tkfont.Font(family="Segoe UI", size=9)
    fe  = tkfont.Font(family="Segoe UI", size=11)
    fbn = tkfont.Font(family="Segoe UI", size=10, weight="bold")
    fsl = tkfont.Font(family="Segoe UI", size=9)   # slot label

    # ── Date navigation ───────────────────────────────────────────────────────
    nav = tk.Frame(parent, bg=_c("BG"))
    nav.pack(fill="x", pady=(0,8))

    def date_str():
        d=cur["date"]
        suf=(" (Today)" if d==today else
             " (Tomorrow)" if d==today+timedelta(1) else
             " (Yesterday)" if d==today-timedelta(1) else "")
        return d.strftime("%A, %d %B %Y")+suf

    date_lbl = tk.Label(nav, text=date_str(), font=fh, bg=_c("BG"), fg=_c("ACCENT"))
    date_lbl.pack(side="left")

    # Define nav functions BEFORE the button loop that references them
    def go(d):
        cur["date"] = cur["date"] + timedelta(d)
        date_lbl.config(text=date_str())
        refresh()

    def go_today():
        cur["date"] = today
        date_lbl.config(text=date_str())
        refresh()

    nav_r = tk.Frame(nav, bg=_c("BG"))
    nav_r.pack(side="right")
    for txt, fn in [("◀", lambda: go(-1)), ("Today", go_today), ("▶", lambda: go(1))]:
        tk.Button(nav_r, text=txt, font=fs, bg=_c("BORDER"), fg=_c("ACCENT"),
                  activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=fn).pack(side="left", padx=2, ipady=5, ipadx=8)

    # ── Add event bar ─────────────────────────────────────────────────────────
    add_row = tk.Frame(parent, bg=_c("BG"))
    add_row.pack(fill="x", pady=(0,8))

    # Time entry
    tw = tk.Frame(add_row, bg=_c("BORDER"))
    tw.pack(side="left", padx=(0,6))
    time_e = tk.Entry(tw, font=fe, bg=_c("CARD"), fg=_c("SUB"),
                      insertbackground=_c("ACCENT"), relief="flat",
                      bd=0, width=6, justify="center")
    time_e.pack(padx=1, pady=1, ipady=7)
    time_e.insert(0,"HH:MM")

    def tfi(e):
        if time_e.get()=="HH:MM": time_e.delete(0,"end"); time_e.config(fg=_c("TEXT"))
    def tfo(e):
        if not time_e.get().strip(): time_e.insert(0,"HH:MM"); time_e.config(fg=_c("SUB"))
    time_e.bind("<FocusIn>",tfi); time_e.bind("<FocusOut>",tfo)
    time_e.bind("<Button-1>",tfi)   # clear placeholder on click

    # Title entry
    titw = tk.Frame(add_row, bg=_c("BORDER"))
    titw.pack(side="left", fill="x", expand=True, padx=(0,6))
    tit_e = tk.Entry(titw, font=fe, bg=_c("CARD"), fg=_c("SUB"),
                     insertbackground=_c("ACCENT"), relief="flat", bd=0)
    tit_e.pack(fill="x", padx=1, pady=1, ipady=7)
    tit_e.insert(0,"Event title…")

    def efi(e):
        if tit_e.get()=="Event title…": tit_e.delete(0,"end"); tit_e.config(fg=_c("TEXT"))
    def efo(e):
        if not tit_e.get().strip(): tit_e.insert(0,"Event title…"); tit_e.config(fg=_c("SUB"))
    tit_e.bind("<FocusIn>",efi); tit_e.bind("<FocusOut>",efo)

    err = tk.Label(parent, text="", font=fs, bg=_c("BG"), fg=_c("RED"))
    err.pack(fill="x")

    def add_event(*_):
        if cur["date"] < today:
            err.config(text="Cannot add events to past days.")
            parent.after(2500, lambda: err.config(text="")); return
        title = tit_e.get().strip()
        if not title or title=="Event title…":
            err.config(text="Please enter a title.")
            parent.after(2500, lambda: err.config(text="")); return
        raw = time_e.get().strip()
        if not raw or raw=="HH:MM": raw=datetime.now().strftime("%H:%M")
        # Normalise – accept H:MM or HH:MM
        raw = raw.zfill(5) if len(raw)==4 else raw
        try: t=datetime.strptime(raw,"%H:%M"); norm=t.strftime("%H:%M")
        except:
            err.config(text="Time must be HH:MM (e.g. 09:24)")
            parent.after(2500, lambda: err.config(text="")); return
        ev={"id":_next_id(),"date":str(cur["date"]),
            "time":norm,"title":title,"done":False}
        _save_new(ev)
        tit_e.delete(0,"end"); tit_e.insert(0,"Event title…"); tit_e.config(fg=_c("SUB"))
        time_e.delete(0,"end"); time_e.insert(0,"HH:MM"); time_e.config(fg=_c("SUB"))
        err.config(text=""); refresh()

    tk.Button(add_row, text="＋ Add", font=fbn, bg=_c("ACCENT"), fg=_c("BG"),
              activebackground=_c("TEXT"), activeforeground=_c("BG"),
              relief="flat", cursor="hand2", bd=0,
              command=add_event).pack(side="left", ipady=7, ipadx=12)
    tit_e.bind("<Return>", add_event)

    # ── Scrollable timeline ───────────────────────────────────────────────────
    inner, update_thumb, cv = _make_scroll_area(parent)

    now_hm = datetime.now().strftime("%H:%M")

    def refresh():
        for w in inner.winfo_children(): w.destroy()

        events      = _load(str(cur["date"]))
        is_today    = (cur["date"]==today)
        is_past     = (cur["date"]<today)

        # Map each event to the nearest slot for display
        # but preserve its exact time for rendering
        def nearest_slot(t):
            """Return the slot key this time falls into."""
            try:
                h,m = map(int,t.split(":"))
                m_rounded = 0 if m < 30 else 30
                return f"{h:02d}:{m_rounded:02d}"
            except: return t

        # Group events by their nearest slot
        slot_events: dict[str,list] = {}
        for ev in events:
            key = nearest_slot(ev["time"])
            slot_events.setdefault(key,[]).append(ev)

        for slot in SLOTS:
            is_half = slot.endswith(":30")
            is_now  = is_today and slot==now_hm[:5]

            row = tk.Frame(inner, bg=_c("BG"))
            row.pack(fill="x", pady=(0,0))

            # Time label
            t_txt = slot if not is_half else "·"
            t_fg  = _c("ACCENT") if is_now else (_c("BORDER") if is_half else _c("SUB"))
            t_w   = 7 if not is_half else 7
            tk.Label(row, text=t_txt, font=fsl,
                     bg=_c("BG"), fg=t_fg, width=t_w, anchor="e"
                     ).pack(side="left")

            # Tick line
            lh = 1 if not is_now else 2
            lc = _c("ACCENT") if is_now else ("#2E2F4A" if is_half else _c("BORDER"))
            tk.Frame(row, bg=lc, height=lh, width=12
                     ).pack(side="left", padx=4, pady=6 if is_half else 10)

            evs = slot_events.get(slot,[])
            if evs:
                # Stack multiple events vertically in a column
                ev_col = tk.Frame(row, bg=_c("BG"))
                ev_col.pack(side="left", fill="x", expand=True)
                for ev in evs:
                    _event_card(ev_col, ev, is_past)
            else:
                if not is_past:
                    ph = tk.Frame(row, bg=_c("BG"), cursor="hand2",
                                  height=24 if not is_half else 14)
                    ph.pack(side="left", fill="x", expand=True)
                    ph.pack_propagate(False)
                    ph.bind("<Button-1>",
                            lambda e,s=slot: _prefill_time(s))

        # Recursively bind mouse wheel on every child widget
        def _bind_scroll(widget):
            widget.bind("<MouseWheel>",
                        lambda e: [cv.yview_scroll(-1*(e.delta//120),"units"),
                                   update_thumb()])
            for child in widget.winfo_children():
                _bind_scroll(child)
        _bind_scroll(inner)

        inner.update_idletasks()
        bb=cv.bbox("all")
        if bb: cv.configure(scrollregion=(0,0,bb[2],bb[3]))
        update_thumb()

        # Scroll to current hour
        if is_today:
            try:
                idx=next(i for i,s in enumerate(SLOTS) if s>=now_hm[:5])
                parent.after(80, lambda: [
                    cv.yview_moveto(max(0,(idx/len(SLOTS))-0.05)),
                    update_thumb()])
            except StopIteration: pass

    def _event_card(row, ev, is_past):
        col = _c("GREEN") if ev["done"] else _c("ACCENT")
        eb  = tk.Frame(row, bg=col)
        eb.pack(fill="x", padx=(0,4), pady=1)
        ei  = tk.Frame(eb, bg=_c("CARD"))
        ei.pack(fill="x", padx=1, pady=1)

        tk.Label(ei, text=ev["time"], font=fs,
                 bg=_c("CARD"), fg=col).pack(side="left", padx=(6,4))

        tl = tk.Label(ei, text=ev["title"], font=fb,
                      bg=_c("CARD"), fg=_c("SUB") if ev["done"] else _c("TEXT"),
                      anchor="w", cursor="hand2")
        tl.pack(side="left", fill="x", expand=True, pady=5)

        done_l = tk.Label(ei, text="✓" if ev["done"] else "○",
                          font=fh, bg=_c("CARD"),
                          fg=_c("GREEN") if ev["done"] else _c("SUB"),
                          cursor="hand2")
        done_l.pack(side="right", padx=6)

        tk.Button(ei, text="✕", font=fs, bg=_c("CARD"), fg=_c("RED"),
                  activebackground=_c("RED"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=lambda eid=ev["id"]: [_delete(eid), refresh()]
                  ).pack(side="right", padx=4, ipady=2)

        def toggle(eid=ev["id"], done=ev["done"]):
            evs2 = _load(str(cur["date"]))
            for e2 in evs2:
                if e2["id"]==eid: e2["done"]=not done; _update(e2); break
            refresh()

        for w in (ei, tl, done_l):
            w.bind("<Button-1>", lambda e: toggle())
            w.bind("<MouseWheel>",
                   lambda e: [cv.yview_scroll(-1*(e.delta//120),"units"),
                               update_thumb()])

    def _prefill_time(slot):
        time_e.delete(0,"end"); time_e.insert(0,slot); time_e.config(fg=_c("TEXT"))
        tit_e.focus()

    refresh()

    # ── Event time notifications ──────────────────────────────────────────────
    def _check_event_times():
        global _timer_running
        if cur["date"] == today:
            now_str = datetime.now().strftime("%H:%M")
            try:
                evs = _load(str(today))
                for ev in evs:
                    guard_key = f"{today}_{ev['id']}_{now_str}"
                    if ev["time"] == now_str and not ev["done"] and guard_key not in _notified:
                        _notified.add(guard_key)
                        import theme as _t
                        if notify_fn:
                            notify_fn(
                                f"{_t.icon()} {ev['title']}",
                                f"Scheduled for {ev['time']} — time to start!",
                                "#4A90D9"
                            )
            except Exception as e:
                print(f"[planner] notify check: {e}")
        root.after(60000, _check_event_times)

    global _timer_running
    if not _timer_running:
        _timer_running = True
        root.after(60000, _check_event_times)

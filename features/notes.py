# ── features/notes.py ─────────────────────────────────────────────────────────
# Rich text editor: Bold, Italic, Underline, Bullet list, Font size picker
# Toolbar buttons highlight when active. Ctrl+B/I/U keyboard shortcuts.
# Content saved as markup string (**bold** //italic// __under__ • bullet).
# Font size saved per note.

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
import os, openpyxl, config

import theme as _theme_mod
def _c(k): return _theme_mod.get(k)

NOTE_COLORS = ["#4A90D9","#7B68EE","#4FC3A1","#E07B54","#D4A843","#E07B9A"]

# ── Excel helpers ─────────────────────────────────────────────────────────────
def _init():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(config.NOTES_DATA):
        wb = openpyxl.Workbook(); ws = wb.active
        ws.title = "Notes"
        ws.append(["id","title","content","color","created","updated","font_size"])
        wb.save(config.NOTES_DATA)

def load_notes():
    _init(); notes = []
    try:
        wb = openpyxl.load_workbook(config.NOTES_DATA); ws = wb.active
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i == 0 or not r[0]: continue
            notes.append({
                "id":        r[0],
                "title":     r[1] or "Untitled",
                "content":   r[2] or "",
                "color":     r[3] or NOTE_COLORS[0],
                "created":   str(r[4]) if r[4] else "",
                "updated":   str(r[5]) if r[5] else "",
                "font_size": int(r[6]) if r[6] else 10,
            })
    except Exception as e:
        print(f"[notes] load: {e}")
    return notes

def _save_all(notes):
    _init()
    try:
        wb = openpyxl.Workbook(); ws = wb.active
        ws.title = "Notes"
        ws.append(["id","title","content","color","created","updated","font_size"])
        for n in notes:
            ws.append([n["id"], n["title"], n["content"],
                       n["color"], n["created"], n["updated"],
                       n.get("font_size", 10)])
        wb.save(config.NOTES_DATA)
    except Exception as e:
        print(f"[notes] save: {e}")

def _new_id(notes):
    return max((n["id"] for n in notes), default=0) + 1

# ── Markup encode / decode ────────────────────────────────────────────────────
# Storage format: **bold** //italic// __underline__ • bullet line
# Encode walks character by character reading tag ranges.
# Decode is a simple state-machine parser.

def encode_rich(ta: tk.Text) -> str:
    """Serialise Text widget content + tags → markup string."""
    total = ta.index("end-1c")
    if ta.compare(total, "==", "1.0"):
        return ""

    result = ""
    idx = "1.0"
    prev_tags: set = set()

    # Close tags in reverse open order
    def close_tags(tags):
        s = ""
        if "under"  in tags: s += "__"
        if "italic" in tags: s += "//"
        if "bold"   in tags: s += "**"
        return s

    def open_tags(tags):
        s = ""
        if "bold"   in tags: s += "**"
        if "italic" in tags: s += "//"
        if "under"  in tags: s += "__"
        return s

    while ta.compare(idx, "<", "end-1c"):
        char = ta.get(idx)
        tags = set(ta.tag_names(idx)) & {"bold","italic","under"}
        if tags != prev_tags:
            result += close_tags(prev_tags)
            result += open_tags(tags)
            prev_tags = tags
        result += char
        idx = ta.index(f"{idx} +1c")

    result += close_tags(prev_tags)
    return result


def decode_rich(ta: tk.Text, markup: str, size: int = 10):
    """Parse markup string and insert into Text widget with tags."""
    ta.delete("1.0", "end")
    if not markup:
        return

    # State machine
    i = 0
    active: set = set()
    while i < len(markup):
        # Check two-char markers
        two = markup[i:i+2]
        if two == "**":
            if "bold" in active: active.discard("bold")
            else:                active.add("bold")
            i += 2; continue
        if two == "//":
            if "italic" in active: active.discard("italic")
            else:                  active.add("italic")
            i += 2; continue
        if two == "__":
            if "under" in active: active.discard("under")
            else:                 active.add("under")
            i += 2; continue

        # Regular character
        char = markup[i]
        start = ta.index("end-1c")
        ta.insert("end", char)
        end = ta.index("end-1c")
        for tag in active:
            ta.tag_add(tag, start, end)
        i += 1


# ── Scrollable list ───────────────────────────────────────────────────────────
def _make_scroll_area(parent):
    bg    = _c("BG")
    outer = tk.Frame(parent, bg=bg)
    outer.pack(fill="both", expand=True)
    cv = tk.Canvas(outer, bg=bg, bd=0, highlightthickness=0)
    cv.pack(side="left", fill="both", expand=True)
    SB_W = 5
    sb   = tk.Canvas(outer, width=SB_W, bg=bg, bd=0, highlightthickness=0)
    sb.pack(side="right", fill="y", padx=(2,0))
    thumb = sb.create_rectangle(0, 0, SB_W, 30, fill=_c("ACCENT"), outline="")
    inner = tk.Frame(cv, bg=bg)
    win   = cv.create_window((0,0), window=inner, anchor="nw")

    def upd_thumb():
        try:
            t,b = cv.yview(); h = sb.winfo_height()
            if h < 2: return
            sb.coords(thumb, 0, t*h, SB_W, max(b*h, t*h+14))
        except: pass

    def scroll(d):
        # Only scroll if content is taller than the canvas
        top, bot = cv.yview()
        if top == 0.0 and bot == 1.0:
            return   # content fits entirely — nothing to scroll
        cv.yview_scroll(d,"units"); upd_thumb()
    for w in (cv, inner, sb, outer):
        w.bind("<MouseWheel>", lambda e: scroll(-1*(e.delta//120)))
    def sb_drag(e):
        t,b = cv.yview(); h = max(sb.winfo_height(),1)
        cv.yview_moveto(max(0, e.y/h-(b-t)/2)); upd_thumb()
    sb.bind("<ButtonPress-1>", sb_drag); sb.bind("<B1-Motion>", sb_drag)

    def _on_cfg(e):
        bb = cv.bbox("all")
        if bb: cv.configure(scrollregion=(0,0,bb[2],bb[3]))
        upd_thumb()
    inner.bind("<Configure>", _on_cfg)
    cv.bind("<Configure>", lambda e: [cv.itemconfig(win,width=e.width), upd_thumb()])
    return inner, upd_thumb, cv, outer, sb


# ── Main build ────────────────────────────────────────────────────────────────
def build(parent: tk.Frame, root: tk.Tk):
    ref = {"data": load_notes(), "editing": None, "list_labels": {}}

    fh  = tkfont.Font(family="Segoe UI", size=11, weight="bold")
    fb  = tkfont.Font(family="Segoe UI", size=10)
    fs  = tkfont.Font(family="Segoe UI", size=9)
    fbn = tkfont.Font(family="Segoe UI", size=10, weight="bold")

    panels = tk.Frame(parent, bg=_c("BG"))
    panels.pack(fill="both", expand=True)

    # Left list
    left = tk.Frame(panels, bg=_c("BG"), width=172)
    left.pack(side="left", fill="y", padx=(0,8))
    left.pack_propagate(False)
    tk.Button(left, text="＋ New note", font=fbn,
              bg=_c("ACCENT"), fg=_c("BG"),
              activebackground=_c("TEXT"), activeforeground=_c("BG"),
              relief="flat", cursor="hand2", bd=0,
              command=lambda: new_note()
              ).pack(fill="x", pady=(0,8), ipady=6)
    list_inner, list_upd, list_cv, list_outer, list_sb = _make_scroll_area(left)

    # Right editor
    right = tk.Frame(panels, bg=_c("CARD"))
    right.pack(side="left", fill="both", expand=True)
    ew = {}

    ph = tk.Label(right, text="Select or create a note",
                  font=fs, bg=_c("CARD"), fg=_c("SUB"))
    ph.pack(pady=80)

    # ── Open editor ───────────────────────────────────────────────────────────
    def open_editor(note: dict):
        ref["editing"] = note
        for w in right.winfo_children(): w.destroy()
        ew.clear()

        sz = note.get("font_size", 10)

        # Colour bar
        cbar = tk.Frame(right, bg=note["color"], height=5)
        cbar.pack(fill="x")

        # Title
        tv = tk.StringVar(value="" if note["title"]=="New note" else note["title"])
        te = tk.Entry(right, textvariable=tv, font=fh,
                      bg=_c("CARD"), fg=_c("TEXT"),
                      insertbackground=_c("ACCENT"),
                      relief="flat", bd=0, highlightthickness=0)
        te.pack(fill="x", padx=12, pady=(10,4), ipady=4)
        if note["title"] == "New note":
            te.insert(0, "Note title…"); te.config(fg=_c("SUB"))
        te.bind("<FocusIn>",  lambda e: (te.get()=="Note title…") and
                (te.delete(0,"end") or te.config(fg=_c("TEXT"))))
        te.bind("<FocusOut>", lambda e: not te.get().strip() and
                (te.insert(0,"Note title…") or te.config(fg=_c("SUB"))))
        def on_tv(*_):
            t = tv.get()
            if t and t != "Note title…":
                note["title"] = t
                lbl = ref["list_labels"].get(note["id"])
                if lbl:
                    try: lbl.config(text=t[:22])
                    except: pass
        tv.trace_add("write", on_tv)
        ew["tv"] = tv; ew["te"] = te

        # Colour picker
        cp = tk.Frame(right, bg=_c("CARD"))
        cp.pack(fill="x", padx=12, pady=(0,4))
        tk.Label(cp, text="Colour:", font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(side="left")
        dot_cv = {}
        def pick_color(col):
            note["color"] = col; cbar.config(bg=col)
            for c, dc in dot_cv.items():
                dc.itemconfig("dot", outline="white" if c==col else "")
            stripe = ref["list_labels"].get(f"s_{note['id']}")
            if stripe:
                try: stripe.config(bg=col)
                except: pass
        for c in NOTE_COLORS:
            dc = tk.Canvas(cp, width=22, height=22, bg=_c("CARD"),
                           bd=0, highlightthickness=0, cursor="hand2")
            dc.pack(side="left", padx=3)
            dc.create_oval(3,3,19,19, fill=c,
                           outline="white" if c==note["color"] else "",
                           width=2, tags="dot")
            dot_cv[c] = dc
            dc.bind("<Button-1>", lambda e, col=c: pick_color(col))

        # ── Toolbar ───────────────────────────────────────────────────────────
        tk.Frame(right, bg=_c("BORDER"), height=1).pack(fill="x")
        tb = tk.Frame(right, bg=_c("CARD"))
        tb.pack(fill="x", padx=8, pady=(4,2))

        btn_refs = {}

        def _btn(parent, label, cmd, bold=False, italic=False, underline=False):
            f = tkfont.Font(family="Segoe UI", size=10,
                            weight="bold" if bold else "normal",
                            slant="italic" if italic else "roman",
                            underline=underline)
            b = tk.Button(parent, text=label, font=f, width=3,
                          bg=_c("CARD"), fg=_c("TEXT"),
                          activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                          relief="flat", cursor="hand2", bd=0, command=cmd)
            b.pack(side="left", padx=1, ipady=3)
            return b

        def toggle_fmt(tag, btn):
            ta = ew.get("ta")
            if not ta: return
            try:
                s = ta.index("sel.first")
                e = ta.index("sel.last")
                # Check if entire selection already has tag
                has = tag in ta.tag_names(s)
                if has: ta.tag_remove(tag, s, e)
                else:   ta.tag_add(tag, s, e)
                _sync_toolbar(ta)
            except tk.TclError:
                pass   # no selection — just update visual state

        bb = _btn(tb, "B", lambda: toggle_fmt("bold",   btn_refs["bold"]),   bold=True)
        bi = _btn(tb, "I", lambda: toggle_fmt("italic", btn_refs["italic"]), italic=True)
        bu = _btn(tb, "U", lambda: toggle_fmt("under",  btn_refs["under"]),  underline=True)
        btn_refs["bold"] = bb; btn_refs["italic"] = bi; btn_refs["under"] = bu

        # Separator
        tk.Frame(tb, bg=_c("BORDER"), width=1).pack(side="left", fill="y", padx=5, pady=3)

        # Bullet
        def insert_bullet():
            ta = ew.get("ta")
            if not ta: return
            ta.focus()
            ls = ta.index("insert linestart")
            lt = ta.get(ls, f"{ls} lineend")
            if lt.startswith("• "):
                ta.delete(ls, f"{ls} +2c")
            else:
                ta.insert(ls, "• ")
        _btn(tb, "•", insert_bullet)

        # Separator
        tk.Frame(tb, bg=_c("BORDER"), width=1).pack(side="left", fill="y", padx=5, pady=3)

        # Font size
        tk.Label(tb, text="Sz:", font=fs, bg=_c("CARD"), fg=_c("SUB")
                 ).pack(side="left", padx=(2,1))
        SIZES = ["8","9","10","11","12","14","16","18","20","24"]
        sv = tk.StringVar(value=str(sz))
        ew["size_var"] = sv

        sm = tk.OptionMenu(tb, sv, *SIZES)
        sm.config(bg=_c("CARD"), fg=_c("TEXT"),
                  activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                  highlightthickness=0, relief="flat", bd=0, font=fs, cursor="hand2")
        sm["menu"].config(bg=_c("CARD"), fg=_c("TEXT"),
                          activebackground=_c("ACCENT"), activeforeground=_c("BG"),
                          font=fs)
        sm.pack(side="left", padx=2)

        # ── Text area ─────────────────────────────────────────────────────────
        tk.Frame(right, bg=_c("BORDER"), height=1).pack(fill="x", padx=12)

        ta_font = tkfont.Font(family="Segoe UI", size=sz)
        ta = tk.Text(right, font=ta_font,
                     bg=_c("CARD"), fg=_c("TEXT"),
                     insertbackground=_c("ACCENT"),
                     selectbackground=_c("ACCENT"), selectforeground=_c("BG"),
                     relief="flat", bd=0, highlightthickness=0,
                     padx=14, pady=10, wrap="word", undo=True,
                     spacing1=2, spacing3=2)
        ew["ta"] = ta   # register before packing bar

        def make_tag_fonts(size):
            ta.tag_config("bold",
                font=tkfont.Font(family="Segoe UI", size=size, weight="bold"))
            ta.tag_config("italic",
                font=tkfont.Font(family="Segoe UI", size=size, slant="italic"))
            ta.tag_config("under",
                font=tkfont.Font(family="Segoe UI", size=size, underline=True))

        make_tag_fonts(sz)

        # Load saved content
        decode_rich(ta, note["content"], sz)
        ta.focus()

        # Font size change handler
        def on_sz(*_):
            ta = ew.get("ta")
            if not ta: return
            try:
                new_sz = int(sv.get())
                note["font_size"] = new_sz
                ta.config(font=tkfont.Font(family="Segoe UI", size=new_sz))
                make_tag_fonts(new_sz)
            except (ValueError, tk.TclError): pass
        sv.trace_add("write", on_sz)

        # Toolbar state sync when cursor moves
        def _sync_toolbar(ta=None):
            ta = ta or ew.get("ta")
            if not ta: return
            try:
                tags = ta.tag_names("insert")
                for fmt, btn in btn_refs.items():
                    active = fmt in tags
                    btn.config(bg=_c("ACCENT") if active else _c("CARD"),
                               fg=_c("BG")     if active else _c("TEXT"))
            except tk.TclError: pass

        ta.bind("<KeyRelease>",    lambda e: _sync_toolbar())
        ta.bind("<ButtonRelease>", lambda e: _sync_toolbar())

        # Keyboard shortcuts
        ta.bind("<Control-b>", lambda e: (toggle_fmt("bold",   btn_refs["bold"]),   "break"))
        ta.bind("<Control-i>", lambda e: (toggle_fmt("italic", btn_refs["italic"]), "break"))
        ta.bind("<Control-u>", lambda e: (toggle_fmt("under",  btn_refs["under"]),  "break"))

        # Auto-continue bullet on Enter
        def on_enter(e):
            ta = ew.get("ta")
            if not ta: return
            ls = ta.index("insert linestart")
            lt = ta.get(ls, f"{ls} lineend")
            if lt == "• ":
                # Empty bullet — remove it
                ta.delete(ls, f"{ls} lineend")
                return "break"
            if lt.startswith("• "):
                ta.insert("insert", "\n• ")
                return "break"
        ta.bind("<Return>", on_enter)
        ta.bind("<MouseWheel>", lambda e: ta.yview_scroll(-1*(e.delta//120),"units"))

        # Save / Delete bar — must be packed BEFORE ta gets expand=True
        bar = tk.Frame(right, bg=_c("CARD"))
        bar.pack(side="bottom", fill="x", padx=12, pady=(4,4))
        ts = note.get("updated") or note.get("created","")
        tk.Label(bar, text=f"Saved: {ts}", font=fs,
                 bg=_c("CARD"), fg=_c("SUB")).pack(side="left")
        tk.Button(bar, text="Delete  ✕", font=fs,
                  bg=_c("CARD"), fg=_c("RED"),
                  activebackground=_c("RED"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=lambda nid=note["id"]: delete_note(nid)
                  ).pack(side="right", padx=(8,0), ipady=4, ipadx=6)
        tk.Button(bar, text="Save  ✓", font=fbn,
                  bg=_c("ACCENT"), fg=_c("BG"),
                  activebackground=_c("TEXT"), activeforeground=_c("BG"),
                  relief="flat", cursor="hand2", bd=0,
                  command=save_current
                  ).pack(side="right", ipady=4, ipadx=10)
        # Now pack ta — AFTER bar so it fills remaining space above bar
        ta.pack(fill="both", expand=True, padx=4, pady=(6,0))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def save_current():
        note = ref["editing"]
        if not note: return
        ta = ew.get("ta"); tv = ew.get("tv"); sv = ew.get("size_var")
        raw = tv.get() if tv else note["title"]
        note["title"]     = raw if raw != "Note title…" and raw.strip() else "Untitled"
        note["content"]   = encode_rich(ta) if ta else ""
        note["updated"]   = datetime.now().strftime("%Y-%m-%d %H:%M")
        note["font_size"] = int(sv.get()) if sv else 10
        found = False
        for i, n in enumerate(ref["data"]):
            if n["id"] == note["id"]: ref["data"][i] = note; found = True; break
        if not found: ref["data"].append(note)
        _save_all(ref["data"])
        refresh_list()

    def new_note():
        note = {"id": _new_id(ref["data"]), "title": "New note",
                "content": "", "color": NOTE_COLORS[0], "font_size": 10,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"), "updated": ""}
        ref["data"].append(note); _save_all(ref["data"])
        refresh_list(); open_editor(note)

    def delete_note(nid):
        ref["data"]    = [n for n in ref["data"] if n["id"] != nid]
        ref["editing"] = None
        _save_all(ref["data"])
        for w in right.winfo_children(): w.destroy()
        tk.Label(right, text="Note deleted. Create a new one.",
                 font=fs, bg=_c("CARD"), fg=_c("SUB")).pack(pady=80)
        refresh_list()

    def refresh_list():
        _bg = _c("BG")
        try:
            list_cv.configure(bg=_bg); list_outer.configure(bg=_bg)
            list_sb.configure(bg=_bg); list_inner.configure(bg=_bg)
        except: pass
        for w in list_inner.winfo_children(): w.destroy()
        ref["list_labels"].clear()

        if not ref["data"]:
            tk.Label(list_inner, text="No notes yet.",
                     font=fs, bg=_c("BG"), fg=_c("SUB")).pack(pady=20)
            return

        for note in reversed(ref["data"]):
            nb = tk.Frame(list_inner, bg=note["color"], cursor="hand2")
            nb.pack(fill="x", pady=2)
            ni = tk.Frame(nb, bg=_c("CARD"), cursor="hand2")
            ni.pack(fill="x", padx=2, pady=(0,2))
            stripe = tk.Frame(ni, bg=note["color"], width=5, cursor="hand2")
            stripe.pack(side="left", fill="y")
            ref["list_labels"][f"s_{note['id']}"] = stripe
            info = tk.Frame(ni, bg=_c("CARD"), cursor="hand2")
            info.pack(side="left", fill="both", expand=True, padx=8, pady=6)
            title_lbl = tk.Label(info, text=note["title"][:22],
                                 font=fb, bg=_c("CARD"), fg=_c("TEXT"),
                                 anchor="w", cursor="hand2")
            title_lbl.pack(anchor="w", fill="x")
            ref["list_labels"][note["id"]] = title_lbl

            tk.Button(ni, text="✕", font=fs,
                      bg=_c("CARD"), fg=_c("RED"),
                      activebackground=_c("RED"), activeforeground=_c("BG"),
                      relief="flat", cursor="hand2", bd=0,
                      command=lambda nid=note["id"]: delete_note(nid)
                      ).pack(side="right", padx=6)

            def _bind(w, n=note):
                w.bind("<Button-1>", lambda e, note=n: open_editor(note))
                w.bind("<MouseWheel>",
                       lambda e: list_cv.event_generate("<MouseWheel>",delta=e.delta))
            for w in (nb, ni, stripe, info, title_lbl):
                _bind(w)

        list_inner.update_idletasks(); list_upd()

    refresh_list()

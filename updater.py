# ── updater.py ────────────────────────────────────────────────────────────────
# Auto-update checker for Desktop Cat Companion.
# Reads GITHUB_REPO and APP_VERSION from .env — no hardcoding needed.
#
# .env keys used:
#   GITHUB_REPO   = your-username/desktop-cat-companion
#   APP_VERSION   = 1.0.0

import threading, urllib.request, urllib.error, json, os, webbrowser
import tkinter as tk
from tkinter import font as tkfont
import config
import theme as _theme

_CHECK_DELAY_MS = 5000

def _read_env() -> dict:
    env = {}
    env_path = os.path.join(config.BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return env
    try:
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    except Exception as e:
        print(f"[updater] .env read error: {e}")
    return env

def _get_config():
    env = _read_env()
    repo    = env.get("GITHUB_REPO", "").strip()
    version = env.get("APP_VERSION",  "").strip()
    if not repo or not version:
        print("[updater] GITHUB_REPO or APP_VERSION missing from .env — skipping check")
        return None, None
    return repo, version

def _parse_version(tag: str) -> tuple:
    tag = tag.lstrip("v").strip()
    try:
        return tuple(int(x) for x in tag.split("."))
    except ValueError:
        return (0, 0, 0)

def _fetch_latest(github_repo: str):
    api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "DesktopCatCompanion-Updater/1.0",
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        tag = data.get("tag_name", "")
        url = data.get("html_url", f"https://github.com/{github_repo}/releases/latest")
        if tag:
            return {"tag": tag, "url": url}
    except Exception as e:
        print(f"[updater] check skipped: {e}")
    return None

def _show_update_popup(root: tk.Tk, latest_tag: str, download_url: str, current_version: str):
    BG=_theme.get("BG"); CARD=_theme.get("CARD"); BORDER=_theme.get("BORDER")
    ACCENT=_theme.get("ACCENT"); TEXT=_theme.get("TEXT"); SUB=_theme.get("SUB")
    W,H=380,210
    sw=root.winfo_screenwidth(); sh=root.winfo_screenheight()
    win=tk.Toplevel(root)
    win.overrideredirect(True); win.attributes("-topmost",True)
    win.configure(bg=ACCENT)
    win.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
    try:
        import ctypes
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.windll.user32.GetParent(win.winfo_id()),
            2, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception: pass
    inner=tk.Frame(win,bg=BG,bd=0); inner.place(x=1,y=1,width=W-2,height=H-2)
    tb=tk.Frame(inner,bg=CARD,height=30); tb.pack(fill="x"); tb.pack_propagate(False)
    tk.Label(tb,text="  Update available",font=tkfont.Font(family="Segoe UI",size=9),
             bg=CARD,fg=SUB,anchor="w").pack(side="left",fill="y")
    tk.Button(tb,text="\u2715",font=tkfont.Font(family="Segoe UI",size=10),
              bg=CARD,fg=SUB,activebackground=CARD,activeforeground=TEXT,
              relief="flat",cursor="hand2",bd=0,padx=10,
              command=win.destroy).pack(side="right",fill="y")
    tk.Frame(inner,bg=BORDER,height=1).pack(fill="x")
    body=tk.Frame(inner,bg=BG); body.pack(fill="both",expand=True,padx=20,pady=14)
    tk.Label(body,text=_theme.icon(),font=tkfont.Font(family="Segoe UI Emoji",size=28),
             bg=BG,fg=ACCENT).pack()
    tk.Label(body,text=f"Version {latest_tag.lstrip('v')} is available!",
             font=tkfont.Font(family="Segoe UI",size=12,weight="bold"),
             bg=BG,fg=ACCENT).pack(pady=(6,2))
    tk.Label(body,text=f"You are on v{current_version}. A newer version is ready.",
             font=tkfont.Font(family="Segoe UI",size=9),bg=BG,fg=SUB).pack()
    br=tk.Frame(body,bg=BG); br.pack(pady=(12,0),fill="x")
    def download(): webbrowser.open(download_url); win.destroy()
    dl=tk.Button(br,text="Download now",font=tkfont.Font(family="Segoe UI",size=10,weight="bold"),
                 bg=ACCENT,fg=BG,activebackground=TEXT,activeforeground=BG,
                 relief="flat",cursor="hand2",bd=0,command=download)
    dl.pack(side="left",fill="x",expand=True,ipady=8)
    dl.bind("<Enter>",lambda e: dl.config(bg=TEXT)); dl.bind("<Leave>",lambda e: dl.config(bg=ACCENT))
    tk.Frame(br,bg=BG,width=10).pack(side="left")
    sk=tk.Button(br,text="Later",font=tkfont.Font(family="Segoe UI",size=10),
                 bg=CARD,fg=SUB,activebackground=BORDER,activeforeground=TEXT,
                 relief="flat",cursor="hand2",bd=0,command=win.destroy)
    sk.pack(side="left",fill="x",expand=True,ipady=8)

def check_in_background(root: tk.Tk):
    """Call once from main.py. Reads GITHUB_REPO and APP_VERSION from .env."""
    def _run():
        repo, current_version = _get_config()
        if repo is None: return
        result = _fetch_latest(repo)
        if result is None: return
        if _parse_version(result["tag"]) > _parse_version(current_version):
            try:
                root.after(0, lambda: _show_update_popup(
                    root, result["tag"], result["url"], current_version))
            except Exception: pass
    def _delayed():
        threading.Thread(target=_run, daemon=True).start()
    root.after(_CHECK_DELAY_MS, _delayed)

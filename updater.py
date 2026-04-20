# ── updater.py ────────────────────────────────────────────────────────────────
# Version check for Desktop Cat Companion.
#
# VERSION LOGIC
# ──────────────
# 1. On first launch  → installed_version is empty in user.xlsx
#                     → fetch version from Supabase
#                     → save it to user.xlsx as installed_version
#                     → run normally (this IS the first install)
#
# 2. On every launch  → read installed_version from user.xlsx
#                     → fetch latest_version from Supabase
#                     → if latest > installed → show update popup
#                     → if latest == installed → run normally, no popup
#
# 3. User updates     → downloads new installer, reinstalls
#                     → save_installed_version() called with new version
#                     → next launch: versions match → no popup
#
# HOW YOU RELEASE A NEW VERSION
# ──────────────────────────────
# 1. Go to Supabase dashboard → app_config table → edit Version column
# 2. Change e.g. 1.0 → 1.1
# 3. All existing users see the update popup on their next launch

import threading
import webbrowser
import tkinter as tk
from tkinter import font as tkfont
import theme as _theme

_CHECK_DELAY_MS = 5000   # 5 s after launch


# ── Version helpers ───────────────────────────────────────────────────────────

def _parse_version(v) -> tuple:
    """
    Convert any version format to a comparable tuple.
    Handles float (1.0, 1.1), string ('1.0', 'v1.0.0'), int (1).
    """
    try:
        # float from Supabase float8 column → "1.1" → (1, 1)
        parts = str(v).lstrip("v").strip().split(".")
        return tuple(int(x) for x in parts if x.isdigit())
    except Exception:
        return (0,)


def _versions_equal(a, b) -> bool:
    return _parse_version(a) == _parse_version(b)


def _version_gt(latest, installed) -> bool:
    """True if latest is strictly greater than installed."""
    return _parse_version(latest) > _parse_version(installed)


# ── Supabase version fetch ────────────────────────────────────────────────────

def _get_supabase_version() -> str:
    """Fetch Version from Supabase. Returns empty string on failure."""
    import supabase_config
    return supabase_config.get_key("Version")


def _get_download_link() -> str:
    """Fetch Link (download URL) from Supabase."""
    import supabase_config
    return supabase_config.get_key("Link", "")


# ── Update popup ──────────────────────────────────────────────────────────────

def _show_update_popup(root: tk.Tk, latest_ver: str,
                       download_url: str, installed_ver: str):
    """Themed frameless popup — Download now or Later."""
    BG     = _theme.get("BG")
    CARD   = _theme.get("CARD")
    BORDER = _theme.get("BORDER")
    ACCENT = _theme.get("ACCENT")
    TEXT   = _theme.get("TEXT")
    SUB    = _theme.get("SUB")

    W, H = 380, 210
    sw   = root.winfo_screenwidth()
    sh   = root.winfo_screenheight()

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg=ACCENT)
    win.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    try:
        import ctypes
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.windll.user32.GetParent(win.winfo_id()),
            2, ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass

    inner = tk.Frame(win, bg=BG, bd=0)
    inner.place(x=1, y=1, width=W-2, height=H-2)

    # Titlebar
    tb = tk.Frame(inner, bg=CARD, height=30)
    tb.pack(fill="x")
    tb.pack_propagate(False)
    tk.Label(tb, text="  Update available",
             font=tkfont.Font(family="Segoe UI", size=9),
             bg=CARD, fg=SUB, anchor="w").pack(side="left", fill="y")
    tk.Button(tb, text="\u2715",
              font=tkfont.Font(family="Segoe UI", size=10),
              bg=CARD, fg=SUB, activebackground=CARD, activeforeground=TEXT,
              relief="flat", cursor="hand2", bd=0, padx=10,
              command=win.destroy).pack(side="right", fill="y")
    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")

    # Body
    body = tk.Frame(inner, bg=BG)
    body.pack(fill="both", expand=True, padx=20, pady=14)

    tk.Label(body, text=_theme.icon(),
             font=tkfont.Font(family="Segoe UI Emoji", size=28),
             bg=BG, fg=ACCENT).pack()
    tk.Label(body,
             text=f"Version {latest_ver} is available!",
             font=tkfont.Font(family="Segoe UI", size=12, weight="bold"),
             bg=BG, fg=ACCENT).pack(pady=(6, 2))
    tk.Label(body,
             text=f"You have v{installed_ver}. A newer version is ready.",
             font=tkfont.Font(family="Segoe UI", size=9),
             bg=BG, fg=SUB).pack()

    # Buttons
    br = tk.Frame(body, bg=BG)
    br.pack(pady=(12, 0), fill="x")

    def download():
        webbrowser.open(download_url)
        win.destroy()

    dl = tk.Button(br, text="Download now",
                   font=tkfont.Font(family="Segoe UI", size=10, weight="bold"),
                   bg=ACCENT, fg=BG,
                   activebackground=TEXT, activeforeground=BG,
                   relief="flat", cursor="hand2", bd=0, command=download)
    dl.pack(side="left", fill="x", expand=True, ipady=8)
    dl.bind("<Enter>", lambda e: dl.config(bg=TEXT))
    dl.bind("<Leave>", lambda e: dl.config(bg=ACCENT))
    tk.Frame(br, bg=BG, width=10).pack(side="left")
    sk = tk.Button(br, text="Later",
                   font=tkfont.Font(family="Segoe UI", size=10),
                   bg=CARD, fg=SUB,
                   activebackground=BORDER, activeforeground=TEXT,
                   relief="flat", cursor="hand2", bd=0, command=win.destroy)
    sk.pack(side="left", fill="x", expand=True, ipady=8)


# ── Public API ────────────────────────────────────────────────────────────────

def check_in_background(root: tk.Tk):
    """
    Call once from main.py.

    Flow:
    - Read installed_version from user.xlsx
    - Fetch latest_version from Supabase
    - First install (no installed_version): save Supabase version, run normally
    - installed < latest: show update popup with download link
    - installed == latest: run normally, no popup
    """
    def _run():
        import user_data

        installed_ver = user_data.get_installed_version()
        latest_ver    = _get_supabase_version()

        if not latest_ver:
            print("[updater] could not fetch version from Supabase — skipping")
            return

        if not installed_ver:
            # First install — save current version, run normally
            user_data.save_installed_version(latest_ver)
            print(f"[updater] first install — saved version {latest_ver}")
            return

        if _version_gt(latest_ver, installed_ver):
            # Newer version available — show popup
            download_url = _get_download_link()
            print(f"[updater] update available: {installed_ver} → {latest_ver}")
            try:
                root.after(0, lambda: _show_update_popup(
                    root, latest_ver, download_url, installed_ver))
            except Exception:
                pass
        else:
            print(f"[updater] up to date: v{installed_ver}")

    root.after(_CHECK_DELAY_MS,
               lambda: threading.Thread(target=_run, daemon=True).start())


def mark_updated(new_version: str):
    """
    Call this after a successful update install to record the new version.
    Typically called once from main.py when the app detects it was just updated.
    """
    import user_data
    user_data.save_installed_version(new_version)
    print(f"[updater] marked as updated to v{new_version}")

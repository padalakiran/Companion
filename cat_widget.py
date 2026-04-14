# ── cat_widget.py ─────────────────────────────────────────────────────────────
# Transparent, always-on-top window containing the animated cat.
# The cat walks left/right along the bottom of the screen (taskbar area).

import tkinter as tk
import random
import config
from sprite_manager import SpriteManager


class CatWidget:
    """
    A borderless, transparent, always-on-top tkinter window.
    The cat sprite walks across the bottom of the screen.

    States
    ------
    walk_right  – cat moves right, walk_right animation
    walk_left   – cat moves left,  walk_left  animation
    idle        – cat stopped randomly, idle animation
    stopped     – cat stopped by user click, stopped animation
    play        – play animation after click (before dashboard opens)
    """

    def __init__(self, root: tk.Tk, on_click_callback=None):
        self._root       = root
        self._on_click   = on_click_callback
        self._sprites = SpriteManager()
        # Load active custom character if one is saved
        try:
            from features.character import get_active_character
            active = get_active_character()
            if active:
                self._sprites.reload(active)
        except Exception as e:
            print(f"[cat] character load error: {e}")

        # ── State ─────────────────────────────────────────────────────────────
        self._state      = "walk_right"
        self._frame_idx  = 0
        self._x          = 100          # current x position
        self._direction  = 1            # +1 right, -1 left
        self._idle_timer = 0            # ms remaining in idle/stopped/play
        self._stopped    = False        # True when user clicked

        # ── Screen dimensions ─────────────────────────────────────────────────
        self._sw = root.winfo_screenwidth()
        self._sh = root.winfo_screenheight()

        # Cat sits just above the taskbar (~48px from bottom on Win11)
        self._y = self._sh - config.DISPLAY_SIZE - 52

        # ── Build window ──────────────────────────────────────────────────────
        self._win = tk.Toplevel(root)
        self._win.overrideredirect(True)          # no title bar / borders
        self._win.attributes("-topmost", True)    # always on top
        self._win.attributes("-transparentcolor", config.CAT_WIN_BG)
        self._win.config(bg=config.CAT_WIN_BG)
        self._win.resizable(False, False)

        self._canvas = tk.Canvas(
            self._win,
            width   = config.DISPLAY_SIZE,
            height  = config.DISPLAY_SIZE,
            bg      = config.CAT_WIN_BG,
            bd      = 0,
            highlightthickness=0,
        )
        self._canvas.pack()

        # ── Image item on canvas ──────────────────────────────────────────────
        first_frame = self._sprites.get_frame("walk_right", 0)
        self._img_item = self._canvas.create_image(
            0, 0, anchor="nw", image=first_frame
        )
        self._current_photo = first_frame   # keep reference

        # ── Events ────────────────────────────────────────────────────────────
        # Click and drag — all handled through drag_start/motion/end
        self._drag_x      = 0
        self._drag_y      = 0
        self._press_time  = 0.0
        self._press_active = False   # True only between ButtonPress and ButtonRelease
        self._canvas.bind("<ButtonPress-1>",   self._drag_start)
        self._canvas.bind("<B1-Motion>",        self._drag_motion)
        self._canvas.bind("<ButtonRelease-1>",  self._drag_end)
        self._is_dragging = False

        # ── Start loops ───────────────────────────────────────────────────────
        self._position_window()
        self._animate()
        self._move()

    # ── Animation loop ─────────────────────────────────────────────────────────

    def _animate(self):
        """Advance sprite frame."""
        photo = self._sprites.get_frame(self._state, self._frame_idx)
        self._canvas.itemconfig(self._img_item, image=photo)
        self._current_photo = photo

        n = self._sprites.frame_count(self._state)
        self._frame_idx = (self._frame_idx + 1) % n

        delay = config.FRAME_MS.get(self._state, 120)
        self._win.after(delay, self._animate)

    # ── Movement loop ──────────────────────────────────────────────────────────

    def _move(self):
        """Move cat horizontally and handle state transitions."""
        if self._stopped:
            self._win.after(config.WALK_TICK_MS, self._move)
            return

        if self._state in ("idle", "play"):
            self._idle_timer -= config.WALK_TICK_MS
            if self._idle_timer <= 0:
                self._resume_walk()
            self._win.after(config.WALK_TICK_MS, self._move)
            return

        # Walking
        self._x += config.WALK_SPEED * self._direction

        # Bounce at screen edges
        if self._x >= self._sw - config.DISPLAY_SIZE:
            self._x = self._sw - config.DISPLAY_SIZE
            self._set_state("walk_left")
            self._direction = -1
        elif self._x <= 0:
            self._x = 0
            self._set_state("walk_right")
            self._direction = 1

        # Random idle chance
        if random.random() < config.IDLE_CHANCE:
            self._set_state("idle")
            self._idle_timer = config.IDLE_DURATION_MS

        self._position_window()
        self._win.after(config.WALK_TICK_MS, self._move)

    # ── Click handling ─────────────────────────────────────────────────────────

    def _drag_start(self, event):
        self._drag_x       = event.x
        self._drag_y       = event.y
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._is_dragging  = False
        self._press_active = True
        import time
        self._press_time   = time.time()
        # Show idle/stopped frame immediately so animation freezes during drag
        self._set_state("stopped")

    def _drag_motion(self, event):
        # Use 2D distance — 8px threshold to ignore micro-movements
        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        if (dx*dx + dy*dy) > 64:   # 8px radius
            self._is_dragging = True
        if self._is_dragging:
            move = event.x - self._drag_x
            self._x = max(0, min(self._sw - config.DISPLAY_SIZE, self._x + move))
            self._position_window()
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_end(self, event):
        was_dragging      = self._is_dragging
        self._is_dragging = False

        if not self._press_active:
            return
        self._press_active = False

        if was_dragging:
            # Resume walking after drag ends
            self._stopped = False
            self._resume_walk()
            return

        # Ignore spurious release with no meaningful hold (< 30ms = phantom)
        import time
        elapsed = time.time() - self._press_time
        if elapsed < 0.03:
            return

        self._handle_click()

    def _on_cat_click(self, event):
        pass   # handled entirely by _drag_end

    def _handle_click(self):
        """Stop the cat, play stopped animation, then open dashboard."""
        if self._stopped:
            # Second click → resume walking
            self._stopped = False
            self._resume_walk()
            return

        self._stopped = True
        self._set_state("stopped")
        self._frame_idx = 0

        # Notify parent to open dashboard
        if self._on_click:
            self._win.after(200, self._on_click)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _set_state(self, state: str):
        if self._state != state:
            self._state     = state
            self._frame_idx = 0

    def _resume_walk(self):
        self._stopped   = False
        self._idle_timer= 0
        state = "walk_right" if self._direction == 1 else "walk_left"
        self._set_state(state)

    def _position_window(self):
        self._win.geometry(
            f"{config.DISPLAY_SIZE}x{config.DISPLAY_SIZE}+{int(self._x)}+{self._y}"
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def play_animation(self, anim: str, duration_ms: int = 3000):
        """Trigger a one-shot animation then return to walking."""
        self._set_state(anim)
        self._idle_timer = duration_ms

    def reload_character(self, folder_or_none):
        """
        Hot-swap the companion character without restarting.
        folder_or_none: path to character folder, or None to restore original cat.
        """
        try:
            self._sprites.reload(folder_or_none)
            print(f"[cat] character changed → {folder_or_none or 'original cat'}")
        except Exception as e:
            print(f"[cat] reload error: {e}")

    def resume(self):
        """Called by dashboard when it closes."""
        self._stopped = False
        self._resume_walk()

    def show(self):
        self._win.deiconify()

    def hide(self):
        self._win.withdraw()

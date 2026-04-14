# ── config.py ─────────────────────────────────────────────────────────────────
# Central config for the Desktop Cat Companion

import os

# Paths
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR    = os.path.join(BASE_DIR, "assets")
DATA_DIR      = os.path.join(BASE_DIR, "data")

SPRITESHEET   = os.path.join(ASSETS_DIR, "cat_spritesheet.png")
USER_DATA     = os.path.join(DATA_DIR,   "user.xlsx")
HEALTH_DATA   = os.path.join(DATA_DIR,   "health_log.xlsx")
TODO_DATA     = os.path.join(DATA_DIR,   "todos.xlsx")
NOTES_DATA    = os.path.join(DATA_DIR,   "notes.xlsx")
PLANNER_DATA  = os.path.join(DATA_DIR,   "planner.xlsx")

os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ── Sprite sheet layout ────────────────────────────────────────────────────────
SPRITE_SIZE   = 150          # each frame is 150×150 px
SPRITE_SCALE  = 1.0          # scale factor for display (1.0 = 150px)
DISPLAY_SIZE  = int(SPRITE_SIZE * SPRITE_SCALE)

# Row index → animation state
ANIM_ROW = {
    "walk_right": 0,
    "walk_left":  1,
    "idle":       2,
    "play":       3,
    "stopped":    4,
}
ANIM_FRAMES = 4   # columns per row

# ── Animation timing (ms) ──────────────────────────────────────────────────────
FRAME_MS = {
    "walk_right": 120,
    "walk_left":  120,
    "idle":       500,
    "play":       140,
    "stopped":    600,
}

# ── Cat walking behaviour ──────────────────────────────────────────────────────
WALK_SPEED        = 2          # pixels per tick
WALK_TICK_MS      = 16         # ~60 fps movement update
IDLE_CHANCE       = 0.002      # probability per tick of switching to idle
IDLE_DURATION_MS  = 4000       # how long idle lasts before walking again
PLAY_DURATION_MS  = 5000       # how long play animation lasts

# ── Window ─────────────────────────────────────────────────────────────────────
CAT_WIN_BG        = "#000000"  # transparent key colour
CAT_WIN_ALPHA     = 0.0        # fully transparent window bg

# ── Health reminders ───────────────────────────────────────────────────────────
WATER_INTERVAL_MIN  = 45
BREAK_INTERVAL_MIN  = 60
STRETCH_INTERVAL_MIN= 90

# ── Colours (dashboard) ────────────────────────────────────────────────────────
CLR_BG        = "#1e1e2e"
CLR_SURFACE   = "#2a2a3e"
CLR_ACCENT    = "#89b4fa"
CLR_TEXT      = "#cdd6f4"
CLR_SUBTEXT   = "#a6adc8"
CLR_SUCCESS   = "#a6e3a1"
CLR_WARNING   = "#f9e2af"
CLR_ERROR     = "#f38ba8"

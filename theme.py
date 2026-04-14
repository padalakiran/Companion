# ── theme.py ──────────────────────────────────────────────────────────────────
# Central theme system. Character-driven colour palettes.
#
# HOW TO LINK A CHARACTER TO A THEME:
#   Name your spritesheet so it contains the theme key.
#   e.g.  forest_cat_spritesheet.png  →  theme key "forest"
#         sakura_spritesheet.png      →  theme key "sakura"
#         midnight_spritesheet.png    →  theme key "midnight"
#   The default cat spritesheet always uses "default" (Night Blue).

import os

THEMES = {

    # ── 1. Default — Cat — Night Blue ─────────────────────────────────────────
    # Dark blue-purple. Cool and calm. For the original blue cat.
    "default": {
        "name":    "Cat — Night Blue",
        "BG":      "#1A1B2E", "CARD":   "#252640", "BORDER":  "#3A3B5C",
        "ACCENT":  "#89B4FA", "TEXT":   "#CDD6F4", "SUB":     "#A6ADC8",
        "GREEN":   "#A6E3A1", "RED":    "#F38BA8", "YELLOW":  "#F9E2AF",
        "ORANGE":  "#E07B54", "BLUE":   "#74C7EC",
        "DANGER":  "#F38BA8", "SUCCESS":"#A6E3A1",
        "ICON":    "🐱",
    },

    # ── 2. Dragon — Ocean Blue ────────────────────────────────────────────────
    # Deep GitHub-style dark. Clean and sharp. For dragon characters.
    "dragon": {
        "name":    "Dragon — Ocean",
        "BG":      "#0D1117", "CARD":   "#161B22", "BORDER":  "#30363D",
        "ACCENT":  "#58A6FF", "TEXT":   "#E6EDF3", "SUB":     "#8B949E",
        "GREEN":   "#56D364", "RED":    "#F85149", "YELLOW":  "#E3B341",
        "ORANGE":  "#D29922", "BLUE":   "#58A6FF",
        "DANGER":  "#F85149", "SUCCESS":"#56D364",
        "ICON":    "🐉",
    },

    # ── 3. Forest — Deep Green ────────────────────────────────────────────────
    # Rich forest green with warm gold accents. Earthy and natural.
    # Name a spritesheet "forest_spritesheet.png" to use this.
    "forest": {
        "name":    "Forest — Deep Green",
        "BG":      "#0D1F0F", "CARD":   "#152A17", "BORDER":  "#2D5A30",
        "ACCENT":  "#7EC850", "TEXT":   "#D8F0C8", "SUB":     "#8BAF7A",
        "GREEN":   "#A8D878", "RED":    "#F07070", "YELLOW":  "#F0D060",
        "ORANGE":  "#D4813A", "BLUE":   "#60B8D0",
        "DANGER":  "#F07070", "SUCCESS":"#A8D878",
        "ICON":    "🌿",
    },

    # ── 4. Sakura — Soft Pink ─────────────────────────────────────────────────
    # Warm rose-toned dark. Elegant and soft. Great for cute characters.
    # Name a spritesheet "sakura_spritesheet.png" to use this.
    "sakura": {
        "name":    "Sakura — Soft Pink",
        "BG":      "#1E0F18", "CARD":   "#2D1525", "BORDER":  "#5C2E4A",
        "ACCENT":  "#F4A7C3", "TEXT":   "#F5DDE8", "SUB":     "#C48AA0",
        "GREEN":   "#98D8A0", "RED":    "#FF7B8A", "YELLOW":  "#F5D080",
        "ORANGE":  "#F0906A", "BLUE":   "#90C8F0",
        "DANGER":  "#FF7B8A", "SUCCESS":"#98D8A0",
        "ICON":    "🌸",
    },

    # ── 5. Midnight — Pure Dark ───────────────────────────────────────────────
    # Near-black with amber gold accent. Minimal and sleek.
    # Name a spritesheet "midnight_spritesheet.png" to use this.
    "midnight": {
        "name":    "Midnight — Gold",
        "BG":      "#0A0A0A", "CARD":   "#141414", "BORDER":  "#2A2A2A",
        "ACCENT":  "#F0B429", "TEXT":   "#F0F0F0", "SUB":     "#888888",
        "GREEN":   "#5CB85C", "RED":    "#D9534F", "YELLOW":  "#F0AD4E",
        "ORANGE":  "#E8783A", "BLUE":   "#5BC0DE",
        "DANGER":  "#D9534F", "SUCCESS":"#5CB85C",
        "ICON":    "🌙",
    },

}

# ── Active palette — mutable dict updated by apply() ─────────────────────────
_P: dict = dict(THEMES["default"])

def get(key: str, fallback: str = "#000000") -> str:
    return _P.get(key, THEMES["default"].get(key, fallback))

def icon() -> str:
    return _P.get("ICON", "🐱")

def name() -> str:
    return _P.get("name", "")

def apply(theme_key: str):
    """Switch active theme. Updates _P in place so all get() calls refresh."""
    palette = THEMES.get(theme_key, THEMES["default"])
    _P.clear()
    _P.update(palette)
    print(f"[theme] → {palette['name']}")

def theme_for_character(path: str) -> str:
    """Map spritesheet filename to theme key."""
    if not path:
        return "default"
    fname = os.path.splitext(os.path.basename(path))[0]
    fname = fname.replace("_spritesheet","").replace("spritesheet","").strip("_")
    if fname in THEMES:
        return fname
    for key in THEMES:
        if key != "default" and key in fname:
            return key
    return "default"

# Any character whose filename maps to a known theme key uses that theme automatically
def is_predefined(char_path: str) -> bool:
    """True if this character has an explicit theme mapping."""
    import os as _os, config as _cfg
    if char_path == _cfg.SPRITESHEET: return True   # original cat
    key = theme_for_character(char_path)
    if key == "default": return False               # fallback = not predefined
    return True                                      # forest/sakura/midnight/dragon etc.

def load_saved():
    """
    Predefined character  (cat / dragon / forest / sakura / midnight)
        → always apply their mapped theme.
    Custom/unknown character
        → apply saved theme_override if set, else apply "default".
    """
    try:
        import config, openpyxl
        if os.path.exists(config.USER_DATA):
            wb   = openpyxl.load_workbook(config.USER_DATA)
            ws   = wb.active
            data = {r[0]: r[1] for r in ws.iter_rows(values_only=True) if r[0]}
            char_path = str(data.get("active_character",""))
            override  = str(data.get("theme_override",""))
            if is_predefined(char_path):
                apply(theme_for_character(char_path))   # auto-apply mapped theme
            elif override and override in THEMES:
                apply(override)                          # user-chosen theme
            else:
                apply("default")                         # unknown char → default
            return
    except Exception as e:
        print(f"[theme] load_saved: {e}")
    apply("default")

def refresh(module_globals: dict):
    """Inject live colours into a build() function's globals."""
    keys = ["BG","CARD","BORDER","ACCENT","TEXT","SUB",
            "GREEN","RED","YELLOW","ORANGE","BLUE","DANGER","SUCCESS"]
    for k in keys:
        module_globals[k] = _P.get(k, THEMES["default"][k])

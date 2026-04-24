# 🐱 Desktop Cat Companion

A Windows desktop productivity app with an animated character that lives on your screen. Click the character to open a full dashboard — health reminders, to-do lists, rich text notes, daily planner, Pomodoro timer, weather, and Gemini AI chat. All themed around your character. No setup required for end users — just install and run.

---

## For End Users — Installation

### 1. Download the installer
Go to the [Releases page](../../releases) → download **DesktopCatCompanion-Setup.exe** → double-click it → follow the wizard.

### 2. Run
Find **Desktop Cat Companion** in your Start Menu or on your Desktop and open it.

That's it. The character appears on your screen immediately. No API keys, no configuration, no Python required.

> **Windows SmartScreen warning:** Click **More info → Run anyway**. This is normal for self-distributed apps.

---

## Features

| Feature | Description |
|---|---|
| **Animated character** | Walks across your screen, bounces at edges, idles when stopped. Click to open dashboard. |
| **Health reminders** | Configurable water, break, and stretch reminders with themed popup notifications. |
| **To-Do List** | Priority levels (Low / Normal / High), filter tabs (All / Pending / Done). |
| **Rich Text Notes** | Bold, Italic, Underline, bullet lists, font size picker — all saved automatically. |
| **Daily Planner** | Half-hour time slots, multiple events per slot, event completion, notifications. |
| **Pomodoro Timer** | Work / Short Break / Long Break modes with arc progress display. |
| **Weather** | Current conditions + 5-day forecast. City configurable from Settings. |
| **AI Chat (Whiskers)** | Powered by Gemini — knows your tasks and health status. |
| **Character System** | Hot-swap characters instantly. Drop any spritesheet PNG into `characters/`. |
| **Theme System** | 5 built-in themes auto-mapped to predefined characters. Custom characters pick any theme. |
| **Auto-update** | App checks for new versions on every launch and shows a download prompt if one is available. |

---

## Dashboard — Window Controls

| Button | Position | Action |
|---|---|---|
| **←** | Top left | Back to home grid |
| **─** | Top right | Minimise dashboard (app keeps running) |
| **⏻** | Top right (red) | Kill — stops the entire app cleanly |
| **✕** | Top right | Close dashboard (character keeps walking) |

Hover over any button to see a tooltip.

---

## Settings

Open dashboard → Settings tile.

| Setting | Description |
|---|---|
| Your name | Used in AI chat greeting |
| Drink water every | Minutes between water reminders (default 45) |
| Short break every | Minutes between break reminders (default 60) |
| Stretch every | Minutes between stretch reminders (default 90) |
| Notifications | Enable / disable each reminder independently |
| Walking speed | Character movement speed in px per tick (default 2) |
| City | Weather location — saved to your profile, persists across launches |
| Theme | Read-only for predefined characters · Dropdown for custom characters |

---

## Character System

### Built-in themes (auto-applied by filename)

| Filename contains | Theme | Accent | Icon |
|---|---|---|---|
| `cat_spritesheet.png` (default) | Night Blue | `#89B4FA` | 🐱 |
| `dragon` | Ocean Blue | `#58A6FF` | 🐉 |
| `forest` | Deep Green | `#7EC850` | 🌿 |
| `sakura` | Soft Pink | `#F4A7C3` | 🌸 |
| `midnight` | Gold | `#F0B429` | 🌙 |

### Adding a custom character

1. Create a **600 × 750 px** PNG spritesheet — 4 columns × 5 rows × 150 px per cell:

| Row | Animation |
|---|---|
| 0 | Walk right |
| 1 | Walk left |
| 2 | Idle |
| 3 | Play |
| 4 | Stopped / sitting |

2. Drop the PNG into the `characters/` folder inside the install directory.
3. Open Settings → Character → select your character.
4. Choose a theme from the dropdown (Settings → Theme).

No restart needed — character and theme swap instantly.

---

## Keyboard Shortcuts (Notes)

| Shortcut | Action |
|---|---|
| `Ctrl+B` | Bold |
| `Ctrl+I` | Italic |
| `Ctrl+U` | Underline |
| `Enter` on a bullet line | Continue bullet list |
| `Enter` on empty bullet | Exit bullet list |

---

## Data Storage

All user data is stored **locally** on your machine inside the `data/` folder:

| File | Contents |
|---|---|
| `user.xlsx` | Profile, settings, active character, theme, saved city, installed version |
| `health_log.xlsx` | Daily health reminder counts |
| `todos.xlsx` | Tasks with priority, status, due date |
| `notes.xlsx` | Notes with rich text markup and colour |
| `planner.xlsx` | Daily events by date and time |
| `chat_history.xlsx` | AI chat messages (cleared by Clear Chat button) |
| `weather_cache.json` | Last weather fetch — valid for 30 minutes |
| `supabase_cache.json` | Remote config cache — used as offline fallback |

> AI chat messages are sent to Google's Gemini API only during active sessions. No data is stored on Google's servers permanently.

---

## Auto-Update

The app checks for new versions 5 seconds after every launch. If a newer version is available you will see a popup:

- **Download now** → opens the Releases page in your browser
- **Later** → dismisses the popup (you will be reminded next launch)

Your current installed version is tracked in `data/user.xlsx`. The latest version is fetched from the backend. No action required — the check happens silently in the background.

---

## Troubleshooting

**Character not appearing**
- Make sure `assets/cat_spritesheet.png` exists (600×750 px, 4×5 grid)
- If running from source: run `python main.py` from the project root

**Weather not loading**
- Check your city name spelling in Settings → City → Save
- The city is fetched from the remote config — if offline, the last cached city is used

**AI Chat not responding**
- Free tier rate limits apply — wait a moment and try again
- If the chat shows "not available" contact the developer

**Theme not applying after character change**
- Predefined characters (cat / dragon / forest / sakura / midnight) auto-apply their theme
- Custom characters: Settings → Theme → pick a theme → Save

**Update popup not appearing**
- The check runs 5 seconds after launch — wait a few seconds
- If offline, the check is skipped silently and runs on your next launch

**App not closing properly**
- Use the red **⏻** kill button in the dashboard titlebar to stop the app completely
- This cleanly stops all background threads (health reminders, timers)

---

## Project Structure (for developers)

```
cat_companion/
├── main.py                   Entry point — wires App, CatWidget, Dashboard, HealthReminder
├── config.py                 All paths, sprite constants, PyInstaller BASE_DIR fix
├── theme.py                  5 colour palettes, apply(), get(), is_predefined(), load_saved()
├── dashboard.py              Dashboard window, 9-tile grid, titlebar controls, tooltips
├── cat_widget.py             Animated character — walk, bounce, click guard, drag
├── sprite_manager.py         Slices spritesheet PNG into animation frames
├── health_reminder.py        Background timer thread, popup queue, daily log
├── user_data.py              user.xlsx helpers, get/save installed version
├── supabase_config.py        Remote config — get_key("column") fetches from Supabase
├── updater.py                Version check — compares user.xlsx vs Supabase, shows popup
├── autostart.py              Windows registry auto-start helper (future use)
├── requirements.txt          Pillow + openpyxl only
├── build.bat                 One-click PyInstaller build
├── DesktopCatCompanion.spec  PyInstaller recipe — bundles assets/ and characters/
├── version_info.txt          .exe Windows metadata (Properties → Details)
├── installer.iss             Inno Setup script — builds single setup.exe installer
├── .gitignore                Excludes data/ from git
│
├── features/
│   ├── todo.py               To-do list — priority dots, filter tabs, xlsx persistence
│   ├── notes.py              Rich text editor — encode/decode Bold/Italic/Underline/bullets
│   ├── planner.py            Daily planner — half-hour slots, notification guard
│   ├── pomodoro.py           Pomodoro timer — arc canvas, 3 modes, background thread
│   ├── weather.py            OpenWeatherMap — current + 5-day, 30-min cache, city from user.xlsx
│   ├── ai_chat.py            Gemini AI — context injection, daemon thread, winfo_exists guard
│   ├── character.py          Character gallery — hot-swap, theme auto-apply
│   └── settings.py           All settings — saves to user.xlsx, city update triggers tile refresh
│
├── tests/
│   ├── conftest.py           Registers --live flag, skips live DB tests in CI
│   ├── test_theme.py         29 tests — theme mapping, apply/get, is_predefined
│   ├── test_todo.py          9 tests  — save/load, priority, done flag, unicode
│   ├── test_planner.py       12 tests — CRUD, date isolation, notification guard
│   ├── test_health.py        9 tests  — intervals, REMINDERS structure, config defaults
│   ├── test_notes.py         12 tests — encode/decode rich text, save/load
│   └── test_supabase.py      28 tests — DB connection (live), version logic, user.xlsx helpers
│
├── .github/workflows/
│   └── ci.yml                Lint + 99 tests on push · .exe build on version tag
│
├── assets/
│   └── cat_spritesheet.png   Default character — 600×750 px, 4 cols × 5 rows
│
└── characters/               Drop custom spritesheets here
    ├── dragon_spritesheet.png
    ├── forest_spritesheet.png
    ├── sakura_spritesheet.png
    └── midnight_spritesheet.png
```

### Running tests (developers)

```bash
# Install test dependencies
pip install pytest ruff

# Run all offline tests (safe for CI)
pytest tests/ -v

# Run live Supabase DB tests (requires credentials in supabase_config.py)
pytest tests/test_supabase.py -v -m live

# Lint
ruff check . --select=F,E9
```

### Building from source

```bash
# Install build dependencies
pip install pyinstaller pillow openpyxl

# Build portable .exe
pyinstaller DesktopCatCompanion.spec

# Output: dist\DesktopCatCompanion\DesktopCatCompanion.exe
# Then build installer with Inno Setup (press F9 with installer.iss open)
```

### Supabase backend (developers only)

The app fetches API keys and remote config from a Supabase table at launch.

**Table:** `app_config`

| Column | Type | Purpose |
|---|---|---|
| `Gemini_key` | text | Gemini API key — used by all installs |
| `Weather_key` | text | OpenWeatherMap API key |
| `City` | text | Default weather city (user can override in Settings) |
| `Version` | text | Latest app version (e.g. `1.1`) — triggers update popup if higher than installed |
| `Link` | text | Download URL shown in the update popup |
| `Repo` | text | GitHub repo (`username/repo-name`) |

**To release a new version:**
1. Supabase dashboard → `app_config` → update `Version` to `1.1` and `Link` to the new installer URL
2. Build new installer → publish to GitHub Releases
3. All existing users see the update popup on their next launch — automatically

---

## License

Built by Kiran · Python + tkinter · 2026 · Personal use

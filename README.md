# 🐱 Desktop Cat Companion

A Windows desktop productivity app featuring an animated character that lives on your screen. Click the character to open a full dashboard with health reminders, to-do lists, notes, a daily planner, Pomodoro timer, weather, and an AI chat assistant — all themed around your character.

---

## Features

| Feature | Description |
|---|---|
| **Animated character** | Walks across your screen, bounces at edges, sits when idle. Click to open dashboard. |
| **Health reminders** | Configurable water, break, and stretch reminders with popup notifications. |
| **To-Do List** | Priority levels (Low / Normal / High), filter tabs (All / Pending / Done). |
| **Notes** | Rich text editor — Bold, Italic, Underline, bullet lists, font size picker. |
| **Daily Planner** | Half-hour time slots, multiple events per slot, event completion, notifications. |
| **Pomodoro Timer** | Work / Short Break / Long Break modes with arc progress display. |
| **Weather** | Current conditions + 5-day forecast via OpenWeatherMap. |
| **AI Chat** | Powered by Gemini (free tier), knows your tasks and health status. |
| **Character System** | Hot-swap characters by dropping a spritesheet PNG into `characters/`. |
| **Theme System** | 5 built-in themes auto-mapped to predefined characters; custom characters pick any theme. |

---

## Requirements

- **OS:** Windows 10 / 11
- **Python:** 3.11 or later
- **Dependencies:**

```
pip install pillow openpyxl python-dotenv requests
```

---

## Setup

### 1. Clone or download the project

```
Desktop Cat Companion/
├── main.py
├── config.py
├── theme.py
├── dashboard.py
├── cat_widget.py
├── health_reminder.py
├── sprite_manager.py
├── user_data.py
├── assets/
│   └── cat_spritesheet.png     ← default character
├── characters/                 ← drop custom spritesheets here
├── data/                       ← created automatically on first run
└── features/
    ├── todo.py
    ├── notes.py
    ├── planner.py
    ├── pomodoro.py
    ├── weather.py
    ├── ai_chat.py
    ├── character.py
    └── settings.py
```

### 2. Create a `.env` file in the project root

```env
GEMINI_API_KEY=your_gemini_api_key_here
WEATHER_API_KEY=your_openweathermap_api_key_here
WEATHER_CITY=Bengaluru
```

**Getting API keys (both free):**
- Gemini: https://aistudio.google.com/app/apikey
- OpenWeatherMap: https://openweathermap.org/api

### 3. Run

```bash
python main.py
```

The character appears on your desktop. Click it to open the dashboard.

---

## Character System

### Built-in themes (auto-applied by filename)

| Spritesheet filename contains | Theme applied |
|---|---|
| `cat_spritesheet.png` (default) | Cat — Night Blue |
| `dragon` | Dragon — Ocean |
| `forest` | Forest — Deep Green |
| `sakura` | Sakura — Soft Pink |
| `midnight` | Midnight — Gold |

### Adding a custom character

1. Create a **600 × 750 px** spritesheet PNG (4 columns × 5 rows × 150 px per cell):

| Row | Animation |
|---|---|
| 0 | Walk right |
| 1 | Walk left |
| 2 | Idle |
| 3 | Play |
| 4 | Stopped / sitting |

2. Drop the PNG into the `characters/` folder.
3. Open Settings → Character → select your character.
4. Choose a theme from the dropdown in Settings → Theme.

No restart required — character and theme swap instantly.

---

## Themes

| Theme | Key | Accent colour | Icon |
|---|---|---|---|
| Cat — Night Blue | `default` | `#89B4FA` | 🐱 |
| Dragon — Ocean | `dragon` | `#58A6FF` | 🐉 |
| Forest — Deep Green | `forest` | `#7EC850` | 🌿 |
| Sakura — Soft Pink | `sakura` | `#F4A7C3` | 🌸 |
| Midnight — Gold | `midnight` | `#F0B429` | 🌙 |

To auto-apply a theme, include the theme key in your spritesheet filename.  
Example: `forest_dragon_spritesheet.png` → Forest theme applied automatically.

---

## Settings

Open dashboard → Settings tile.

| Setting | Description |
|---|---|
| Your name | Used in AI chat greeting and dashboard |
| Drink water every | Minutes between water reminders (default 45) |
| Short break every | Minutes between break reminders (default 60) |
| Stretch every | Minutes between stretch reminders (default 90) |
| Notifications | Enable/disable each reminder type independently |
| Walking speed | Cat movement speed in px/tick (default 2) |
| City | Weather location (with autocomplete) |
| Theme | Read-only for predefined characters; dropdown for custom characters |

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

All data is stored **locally** in the `data/` folder as Excel files:

| File | Contents |
|---|---|
| `user.xlsx` | Profile, settings, active character, theme override |
| `health_log.xlsx` | Daily health reminder counts |
| `todos.xlsx` | To-do tasks with priority and status |
| `notes.xlsx` | Notes with rich text markup and colour |
| `planner.xlsx` | Daily events by date |

No data is sent to any server. AI chat messages are sent to the Gemini API only during active chat sessions and are not stored server-side.

---

## Project Structure

```
main.py              Entry point — wires App, CatWidget, Dashboard, HealthReminder
config.py            All paths, sprite layout, timing constants, default intervals
theme.py             5 theme palettes, is_predefined(), apply(), load_saved()
dashboard.py         Dashboard window, 9-tile grid, CatNotification popup
cat_widget.py        Animated character — walk, bounce, click detection
sprite_manager.py    Loads and slices spritesheet frames
health_reminder.py   Background timer thread, popup queue, Excel log
user_data.py         user.xlsx read/write helpers

features/
  todo.py            To-do list with priority and filter
  notes.py           Rich text notes with encode/decode markup
  planner.py         Daily planner with time slots and notifications
  pomodoro.py        Pomodoro timer with arc canvas
  weather.py         OpenWeatherMap current + forecast
  ai_chat.py         Gemini AI chat with context injection
  character.py       Character gallery and hot-swap
  settings.py        All user-facing settings with save/restore
```

---

## Troubleshooting

**Character not appearing**
- Check that `assets/cat_spritesheet.png` exists (600×750 px, 4×5 grid)
- Run `python main.py` from the project root directory

**Weather not loading**
- Verify `WEATHER_API_KEY` in `.env` is valid
- Check the city name spelling in Settings

**AI Chat not responding**
- Verify `GEMINI_API_KEY` in `.env` is valid
- Free tier rate limits apply — wait a minute and try again

**Theme not applying after character change**
- Predefined characters (cat/dragon/forest/sakura/midnight) auto-apply their theme
- Custom characters: go to Settings → Theme → pick a theme → Save

**Excel error on first run**
- The `data/` folder and all `.xlsx` files are created automatically on first run

---

## License

Built by Kiran using Python + tkinter. Personal use.

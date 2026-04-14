# ── main.py ───────────────────────────────────────────────────────────────────
# Entry point for the Desktop Cat Companion.

import tkinter as tk
from user_data       import get_or_create_user
from cat_widget      import CatWidget
from dashboard       import Dashboard
from health_reminder import HealthReminder
import config
import theme


class App:
    def __init__(self):
        # ── Hidden root window ────────────────────────────────────────────────
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.title("Cat Companion")

        # ── Load saved theme before building any UI ──────────────────────────
        theme.load_saved()

        # ── User ──────────────────────────────────────────────────────────────
        self._user = get_or_create_user(self._root)
        self._name = self._user.get("name", "Friend")

        # ── Dashboard ─────────────────────────────────────────────────────────
        self._dashboard = Dashboard(
            root     = self._root,
            user     = self._user,
            on_close = self._on_dashboard_closed,
        )

        # ── Health reminder engine (runs always, dashboard-independent) ────────
        self._health = HealthReminder(root=self._root)
        self._health.start()

        # Give dashboard a reference so settings can update intervals
        self._dashboard.set_health_reminder(self._health)

        # Give dashboard reference to cat widget for character hot-swap
        # self._dashboard.set_cat_widget(self._cat)

        # ── Cat widget ────────────────────────────────────────────────────────
        self._cat = CatWidget(
            self._root,
            on_click_callback=self._on_cat_clicked,
        )
        # Give dashboard reference to cat widget for character hot-swap
        self._dashboard.set_cat_widget(self._cat)

        # Wire cat widget to dashboard for character hot-swap + theming
        self._dashboard.set_cat_widget(self._cat)

        self._root.protocol("WM_DELETE_WINDOW", self.quit)
        print(f"[Cat Companion] Hello, {self._name}! Reminders running.")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_cat_clicked(self):
        self._dashboard.open(cat_x=int(self._cat._x))

    def _on_dashboard_closed(self):
        self._cat.resume()

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):
        self._root.mainloop()

    def quit(self):
        self._health.stop()
        self._root.destroy()


if __name__ == "__main__":
    app = App()
    app.run()

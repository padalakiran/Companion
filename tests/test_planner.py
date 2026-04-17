"""
tests/test_planner.py
Unit tests for features/planner.py — CRUD helpers and notification guard.
No tkinter needed.
"""
import sys
import os
import importlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def _import(monkeypatch, tmp_path):
    planner_path = tmp_path / "planner.xlsx"
    monkeypatch.setattr(config, "PLANNER_DATA", str(planner_path))
    import features.planner as mod
    importlib.reload(mod)
    return mod


# ── _load / _save_new / _update / _delete ────────────────────────────────────

def test_save_new_and_load(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev = {"id": 1, "date": "2026-05-01", "time": "09:00",
          "title": "Team standup", "done": False}
    mod._save_new(ev)
    loaded = mod._load("2026-05-01")
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Team standup"
    assert loaded[0]["time"] == "09:00"

def test_load_empty_when_no_events(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    assert mod._load("2026-05-01") == []

def test_load_date_isolation(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev1 = {"id": 1, "date": "2026-05-01", "time": "09:00", "title": "Event A", "done": False}
    ev2 = {"id": 2, "date": "2026-05-02", "time": "10:00", "title": "Event B", "done": False}
    mod._save_new(ev1)
    mod._save_new(ev2)
    day1 = mod._load("2026-05-01")
    day2 = mod._load("2026-05-02")
    assert len(day1) == 1 and day1[0]["title"] == "Event A"
    assert len(day2) == 1 and day2[0]["title"] == "Event B"

def test_multiple_events_same_slot(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    for i in range(4):
        mod._save_new({"id": i+1, "date": "2026-05-01", "time": "09:00",
                       "title": f"Meeting {i+1}", "done": False})
    loaded = mod._load("2026-05-01")
    assert len(loaded) == 4

def test_update_done_flag(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev = {"id": 1, "date": "2026-05-01", "time": "09:00", "title": "Review", "done": False}
    mod._save_new(ev)
    ev["done"] = True
    mod._update(ev)
    loaded = mod._load("2026-05-01")
    assert loaded[0]["done"] is True

def test_delete_removes_event(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev = {"id": 1, "date": "2026-05-01", "time": "09:00", "title": "Lunch", "done": False}
    mod._save_new(ev)
    mod._delete(1)
    assert mod._load("2026-05-01") == []

def test_delete_specific_event_leaves_others(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev1 = {"id": 1, "date": "2026-05-01", "time": "09:00", "title": "First",  "done": False}
    ev2 = {"id": 2, "date": "2026-05-01", "time": "09:00", "title": "Second", "done": False}
    mod._save_new(ev1)
    mod._save_new(ev2)
    mod._delete(1)
    loaded = mod._load("2026-05-01")
    assert len(loaded) == 1
    assert loaded[0]["title"] == "Second"

def test_unicode_title(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    ev = {"id": 1, "date": "2026-05-01", "time": "10:00",
          "title": "கோப்பை 🏆 ミーティング", "done": False}
    mod._save_new(ev)
    loaded = mod._load("2026-05-01")
    assert loaded[0]["title"] == "கோப்பை 🏆 ミーティング"


# ── notification guard (_notified set) ───────────────────────────────────────

def test_notified_guard_blocks_duplicate(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    mod._notified.clear()
    key = "2026-05-01_1_09:00"
    assert key not in mod._notified
    mod._notified.add(key)
    assert key in mod._notified   # second fire blocked

def test_different_events_not_blocked(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    mod._notified.clear()
    k1 = "2026-05-01_1_09:00"
    k2 = "2026-05-01_2_09:00"
    mod._notified.add(k1)
    assert k2 not in mod._notified   # different event still fires

def test_same_event_different_day_not_blocked(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    mod._notified.clear()
    k1 = "2026-05-01_1_09:00"
    k2 = "2026-05-02_1_09:00"
    mod._notified.add(k1)
    assert k2 not in mod._notified   # same event id, different date = new fire

def test_notified_set_clears(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    mod._notified.add("some_key")
    mod._notified.clear()
    assert len(mod._notified) == 0

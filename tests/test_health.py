"""
tests/test_health.py
Unit tests for health_reminder.py — data helpers and interval logic.
No tkinter needed (we avoid instantiating HealthReminder itself).
"""
import sys
import os
import importlib
import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


def _write_user(path, rows):
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["key", "value"])
    for k, v in rows.items():
        ws.append([k, v])
    wb.save(str(path))


# ── _load_interval ────────────────────────────────────────────────────────────

def test_load_interval_reads_from_xlsx(tmp_path, monkeypatch):
    user_xlsx = tmp_path / "user.xlsx"
    _write_user(user_xlsx, {"water_interval": "30"})
    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    import health_reminder as mod
    importlib.reload(mod)
    # Instantiation needs tk — test the static method directly
    result = mod.HealthReminder._load_interval(None, "water_interval", 45)
    assert result == 30

def test_load_interval_uses_default_when_key_missing(tmp_path, monkeypatch):
    user_xlsx = tmp_path / "user.xlsx"
    _write_user(user_xlsx, {})
    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    import health_reminder as mod
    importlib.reload(mod)
    result = mod.HealthReminder._load_interval(None, "water_interval", 45)
    assert result == 45

def test_load_interval_uses_default_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "nonexistent.xlsx"))
    import health_reminder as mod
    importlib.reload(mod)
    result = mod.HealthReminder._load_interval(None, "water_interval", 45)
    assert result == 45

def test_load_interval_ignores_invalid_value(tmp_path, monkeypatch):
    user_xlsx = tmp_path / "user.xlsx"
    _write_user(user_xlsx, {"water_interval": "not_a_number"})
    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    import health_reminder as mod
    importlib.reload(mod)
    result = mod.HealthReminder._load_interval(None, "water_interval", 45)
    assert result == 45


# ── REMINDERS property structure ──────────────────────────────────────────────

def test_reminders_has_three_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import health_reminder as mod
    importlib.reload(mod)
    # Access the property via its underlying function (no tk needed)
    prop_fn = mod.HealthReminder.REMINDERS.fget
    # Build a minimal stub with the _load_interval method
    class Stub:
        _load_interval = staticmethod(mod.HealthReminder._load_interval)
    reminders = prop_fn(Stub())
    assert "water"   in reminders
    assert "break"   in reminders
    assert "stretch" in reminders

def test_reminders_each_has_three_elements(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import health_reminder as mod
    importlib.reload(mod)
    prop_fn = mod.HealthReminder.REMINDERS.fget
    class Stub:
        _load_interval = staticmethod(mod.HealthReminder._load_interval)
    reminders = prop_fn(Stub())
    # REMINDERS returns {key: (title, message, color)} — tuples, not dicts
    for key, val in reminders.items():
        assert isinstance(val, tuple),      f"'{key}' should be a tuple"
        assert len(val) == 3,               f"'{key}' tuple needs 3 elements: (title, message, color)"
        title, message, color = val
        assert len(title)   > 0,            f"'{key}' title is empty"
        assert len(message) > 0,            f"'{key}' message is empty"
        assert color.startswith("#"),       f"'{key}' color is not a hex string"


# ── Config defaults ───────────────────────────────────────────────────────────

def test_config_default_water_interval():
    assert config.WATER_INTERVAL_MIN == 45

def test_config_default_break_interval():
    assert config.BREAK_INTERVAL_MIN == 60

def test_config_default_stretch_interval():
    assert config.STRETCH_INTERVAL_MIN == 90

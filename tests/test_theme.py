"""
tests/test_theme.py
Unit tests for theme.py — pure Python, no tkinter, runs headlessly on CI.
"""
import sys
import os
#import tempfile
import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import theme
import config


# ── theme_for_character ───────────────────────────────────────────────────────

def test_dragon_maps_to_dragon():
    assert theme.theme_for_character("characters/dragon_spritesheet.png") == "dragon"

def test_forest_maps_to_forest():
    assert theme.theme_for_character("characters/forest_spritesheet.png") == "forest"

def test_sakura_maps_to_sakura():
    assert theme.theme_for_character("characters/sakura_spritesheet.png") == "sakura"

def test_midnight_maps_to_midnight():
    assert theme.theme_for_character("characters/midnight_spritesheet.png") == "midnight"

def test_unknown_character_maps_to_default():
    assert theme.theme_for_character("characters/my_hero.png") == "default"

def test_custom_with_no_keyword_maps_to_default():
    assert theme.theme_for_character("characters/robot_spritesheet.png") == "default"

def test_keyword_anywhere_in_name():
    assert theme.theme_for_character("characters/cool_dragon_hero.png") == "dragon"

def test_empty_path_maps_to_default():
    assert theme.theme_for_character("") == "default"


# ── is_predefined ─────────────────────────────────────────────────────────────

def test_default_spritesheet_is_predefined():
    assert theme.is_predefined(config.SPRITESHEET) is True

def test_dragon_is_predefined():
    assert theme.is_predefined("characters/dragon_spritesheet.png") is True

def test_forest_is_predefined():
    assert theme.is_predefined("characters/forest.png") is True

def test_sakura_is_predefined():
    assert theme.is_predefined("characters/sakura_spritesheet.png") is True

def test_midnight_is_predefined():
    assert theme.is_predefined("characters/midnight.png") is True

def test_custom_not_predefined():
    assert theme.is_predefined("characters/my_custom_char.png") is False

def test_robot_not_predefined():
    assert theme.is_predefined("characters/robot_spritesheet.png") is False


# ── apply and get ─────────────────────────────────────────────────────────────

def test_apply_default_accent():
    theme.apply("default")
    assert theme.get("ACCENT") == "#89B4FA"

def test_apply_dragon_accent():
    theme.apply("dragon")
    assert theme.get("ACCENT") == "#58A6FF"
    theme.apply("default")

def test_apply_forest_accent():
    theme.apply("forest")
    assert theme.get("ACCENT") == "#7EC850"
    theme.apply("default")

def test_apply_sakura_accent():
    theme.apply("sakura")
    assert theme.get("ACCENT") == "#F4A7C3"
    theme.apply("default")

def test_apply_midnight_accent():
    theme.apply("midnight")
    assert theme.get("ACCENT") == "#F0B429"
    theme.apply("default")

def test_get_fallback_for_missing_key():
    theme.apply("default")
    assert theme.get("NONEXISTENT_KEY", "#ABCDEF") == "#ABCDEF"

def test_unknown_theme_key_falls_back_to_default():
    theme.apply("nonexistent_theme")
    assert theme.get("ACCENT") == "#89B4FA"   # default accent
    theme.apply("default")


# ── icon ──────────────────────────────────────────────────────────────────────

def test_default_icon():
    theme.apply("default")
    assert theme.icon() == "🐱"

def test_dragon_icon():
    theme.apply("dragon")
    assert theme.icon() == "🐉"
    theme.apply("default")

def test_midnight_icon():
    theme.apply("midnight")
    assert theme.icon() == "🌙"
    theme.apply("default")


# ── all themes have required keys ─────────────────────────────────────────────

def test_all_themes_have_required_keys():
    required = ["BG", "CARD", "BORDER", "ACCENT", "TEXT", "SUB",
                "GREEN", "RED", "YELLOW", "ICON", "DANGER", "SUCCESS"]
    for theme_key, palette in theme.THEMES.items():
        for k in required:
            assert k in palette, f"Theme '{theme_key}' is missing key '{k}'"


# ── load_saved ────────────────────────────────────────────────────────────────

def test_load_saved_applies_predefined_theme(tmp_path, monkeypatch):
    user_xlsx = tmp_path / "user.xlsx"
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["key", "value"])
    ws.append(["active_character", "characters/dragon_spritesheet.png"])
    wb.save(str(user_xlsx))
    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    theme.load_saved()
    assert theme.get("ACCENT") == "#58A6FF"   # dragon
    theme.apply("default")

def test_load_saved_applies_override_for_custom_char(tmp_path, monkeypatch):
    user_xlsx = tmp_path / "user.xlsx"
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["key", "value"])
    ws.append(["active_character", "characters/robot_spritesheet.png"])
    ws.append(["theme_override", "sakura"])
    wb.save(str(user_xlsx))
    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    theme.load_saved()
    assert theme.get("ACCENT") == "#F4A7C3"   # sakura
    theme.apply("default")

def test_load_saved_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "nonexistent.xlsx"))
    theme.load_saved()
    assert theme.get("ACCENT") == "#89B4FA"   # default

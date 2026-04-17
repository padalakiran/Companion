"""
tests/test_notes.py
Unit tests for features/notes.py — encode_rich/decode_rich and save/load.
Requires tkinter (for tk.Text) but NOT a display — uses Tk().withdraw().
"""
import sys
import os
import importlib
import tkinter as tk

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config

# Shared hidden root — created once for all tests
_root = None

def _get_root():
    global _root
    if _root is None:
        _root = tk.Tk()
        _root.withdraw()
    return _root

def _text():
    """Return a fresh tk.Text widget with common tags configured."""
    ta = tk.Text(_get_root())
    ta.tag_config("bold",      font=("Arial", 10, "bold"))
    ta.tag_config("italic",    font=("Arial", 10, "italic"))
    ta.tag_config("underline", underline=True)
    return ta

def _import(monkeypatch, tmp_path):
    notes_path = tmp_path / "notes.xlsx"
    monkeypatch.setattr(config, "NOTES_DATA", str(notes_path))
    import features.notes as mod
    importlib.reload(mod)
    return mod


# ── encode_rich / decode_rich ─────────────────────────────────────────────────

def test_plain_text_roundtrip():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "Hello World")
    markup = encode_rich(ta)
    ta2 = _text()
    decode_rich(ta2, markup)
    assert ta2.get("1.0", "end-1c") == "Hello World"

def test_bold_roundtrip():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "Hello ")
    ta.insert("end", "Bold")
    ta.tag_add("bold", "1.6", "1.10")
    markup = encode_rich(ta)
    assert "**Bold**" in markup
    ta2 = _text()
    decode_rich(ta2, markup)
    assert "bold" in ta2.tag_names("1.6")

def test_italic_roundtrip():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "Hello ")
    ta.insert("end", "Italic")
    ta.tag_add("italic", "1.6", "1.12")
    markup = encode_rich(ta)
    assert "//Italic//" in markup
    ta2 = _text()
    decode_rich(ta2, markup)
    assert "italic" in ta2.tag_names("1.6")

def test_underline_roundtrip():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "Hello ")
    ta.insert("end", "Under")
    ta.tag_add("underline", "1.6", "1.11")
    markup = encode_rich(ta)
    assert "__Under__" in markup
    ta2 = _text()
    decode_rich(ta2, markup)
    assert "underline" in ta2.tag_names("1.6")

def test_bullet_preserved():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "• Item one")
    markup = encode_rich(ta)
    assert "• Item one" in markup
    ta2 = _text()
    decode_rich(ta2, markup)
    assert "• Item one" in ta2.get("1.0", "end-1c")

def test_empty_content_encodes_to_empty():
    from features.notes import encode_rich
    ta = _text()
    assert encode_rich(ta) == ""

def test_multiline_content():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "Line one\nLine two\nLine three")
    markup = encode_rich(ta)
    ta2 = _text()
    decode_rich(ta2, markup)
    content = ta2.get("1.0", "end-1c")
    assert "Line one" in content
    assert "Line two" in content
    assert "Line three" in content

def test_combined_bold_and_italic():
    from features.notes import encode_rich, decode_rich
    ta = _text()
    ta.insert("end", "A")
    ta.tag_add("bold",   "1.0", "1.1")
    ta.tag_add("italic", "1.0", "1.1")
    markup = encode_rich(ta)
    ta2 = _text()
    decode_rich(ta2, markup)
    assert "bold"   in ta2.tag_names("1.0")
    assert "italic" in ta2.tag_names("1.0")


# ── load_notes / _save_all ────────────────────────────────────────────────────

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    notes = [{"id": 1, "title": "My note", "content": "Hello **World**",
              "color": "#89B4FA", "created": "2026-01-01", "updated": "2026-01-01",
              "font_size": 10}]
    mod._save_all(notes)
    loaded = mod.load_notes()
    assert len(loaded) == 1
    assert loaded[0]["title"] == "My note"
    assert loaded[0]["content"] == "Hello **World**"

def test_load_empty_when_no_file(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    assert mod.load_notes() == []

def test_multiple_notes_saved_and_loaded(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    notes = [
        {"id": 1, "title": "Note A", "content": "First",  "color": "#89B4FA",
         "created": "2026-01-01", "updated": "2026-01-01", "font_size": 10},
        {"id": 2, "title": "Note B", "content": "Second", "color": "#A6E3A1",
         "created": "2026-01-02", "updated": "2026-01-02", "font_size": 12},
    ]
    mod._save_all(notes)
    loaded = mod.load_notes()
    assert len(loaded) == 2
    titles = [n["title"] for n in loaded]
    assert "Note A" in titles
    assert "Note B" in titles

def test_empty_list_saves_and_loads(tmp_path, monkeypatch):
    mod = _import(monkeypatch, tmp_path)
    mod._save_all([])
    assert mod.load_notes() == []

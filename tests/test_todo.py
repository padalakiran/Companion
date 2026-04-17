"""
tests/test_todo.py
Unit tests for features/todo.py — save/load helpers only (no tkinter).
"""
import sys
import os
import openpyxl

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ── helpers ───────────────────────────────────────────────────────────────────

def _import(monkeypatch, tmp_path):
    """Patch TODO_DATA path and import fresh."""
    todo_path = tmp_path / "todos.xlsx"
    monkeypatch.setattr(config, "TODO_DATA", str(todo_path))
    # Re-import so module picks up patched path
    import importlib
    import features.todo as todo_mod
    importlib.reload(todo_mod)
    return todo_mod, todo_path


SAMPLE = [
    {"id": 1, "task": "Buy milk",    "priority": "Normal", "due_date": "", "done": False, "created": "2026-01-01"},
    {"id": 2, "task": "Call doctor", "priority": "High",   "due_date": "", "done": True,  "created": "2026-01-02"},
    {"id": 3, "task": "Read book",   "priority": "Low",    "due_date": "", "done": False, "created": "2026-01-03"},
]


# ── save and load ─────────────────────────────────────────────────────────────

def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos(SAMPLE)
    loaded = mod.load_todos()
    assert len(loaded) == 3
    assert loaded[0]["task"] == "Buy milk"
    assert loaded[1]["task"] == "Call doctor"
    assert loaded[2]["task"] == "Read book"

def test_priority_preserved(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos(SAMPLE)
    loaded = mod.load_todos()
    assert loaded[0]["priority"] == "Normal"
    assert loaded[1]["priority"] == "High"
    assert loaded[2]["priority"] == "Low"

def test_done_flag_preserved(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos(SAMPLE)
    loaded = mod.load_todos()
    assert loaded[0]["done"] is False
    assert loaded[1]["done"] is True

def test_empty_list_saves_and_loads(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos([])
    assert mod.load_todos() == []

def test_load_returns_empty_when_no_file(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    # Don't save — file doesn't exist
    assert mod.load_todos() == []

def test_ids_preserved(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos(SAMPLE)
    loaded = mod.load_todos()
    assert loaded[0]["id"] == 1
    assert loaded[1]["id"] == 2
    assert loaded[2]["id"] == 3

def test_overwrite_replaces_previous(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    mod.save_todos(SAMPLE)
    mod.save_todos([SAMPLE[0]])   # overwrite with just 1 item
    loaded = mod.load_todos()
    assert len(loaded) == 1
    assert loaded[0]["task"] == "Buy milk"

def test_unicode_task_name(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    tasks = [{"id": 1, "task": "நன்றி 🐱 テスト", "priority": "Normal",
              "due_date": "", "done": False, "created": "2026-01-01"}]
    mod.save_todos(tasks)
    loaded = mod.load_todos()
    assert loaded[0]["task"] == "நன்றி 🐱 テスト"

def test_due_date_preserved(tmp_path, monkeypatch):
    mod, _ = _import(monkeypatch, tmp_path)
    tasks = [{"id": 1, "task": "Dentist", "priority": "High",
              "due_date": "2026-05-01", "done": False, "created": "2026-01-01"}]
    mod.save_todos(tasks)
    loaded = mod.load_todos()
    assert loaded[0]["due_date"] == "2026-05-01"

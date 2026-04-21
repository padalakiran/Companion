# tests/conftest.py
# Registers the --live flag and the @pytest.mark.live marker.
#
# Usage:
#   pytest tests/ -v              → runs everything EXCEPT live DB tests
#   pytest tests/ -v -m live      → runs ONLY live DB tests (needs real Supabase creds)
#   pytest tests/ -v -m "not live"→ runs everything except live DB tests

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run live tests that require a real Supabase connection",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: marks tests that need a real Supabase connection (skipped in CI)",
    )


def pytest_collection_modifyitems(config, items):
    """Auto-skip @pytest.mark.live tests unless --live flag is passed."""
    if config.getoption("--live"):
        return   # --live passed — run everything
    skip_live = pytest.mark.skip(reason="Live DB test — run with: pytest -m live")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)

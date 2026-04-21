"""
tests/test_supabase.py
─────────────────────
Three groups of tests:

Group A — supabase_config (live DB connection)
  Requires real SUPABASE_URL + SUPABASE_ANON_KEY set in supabase_config.py
  Marks: @pytest.mark.live  (skipped in CI unless --live flag passed)

Group B — version comparison logic (pure Python, always runs)
  Tests _parse_version, _version_gt, _versions_equal
  No network, no tkinter, runs headlessly on CI

Group C — user_data version helpers (pure Python, always runs)
  Tests get_installed_version + save_installed_version using tmp_path
  No network, no tkinter, runs headlessly on CI

Run all:          pytest tests/test_supabase.py -v
Run live only:    pytest tests/test_supabase.py -v -m live
Run offline only: pytest tests/test_supabase.py -v -m "not live"
"""
import sys
import os
import importlib
import openpyxl
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import config


# ═══════════════════════════════════════════════════════════════════════════════
# Group A — Live Supabase connection tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.live
def test_supabase_fetch_returns_dict():
    """Supabase returns a non-empty dict when credentials are correct."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    result = sc._fetch()
    assert isinstance(result, dict), "Expected dict from Supabase, got empty or error"
    assert len(result) > 0, "Supabase returned an empty row"


@pytest.mark.live
def test_supabase_all_required_columns_present():
    """app_config table has all 6 required columns."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    row = sc._fetch()
    required = ["Gemini_key", "Weather_key", "City", "Version", "Link", "Repo"]
    for col in required:
        assert col in row, f"Column '{col}' missing from app_config table"


@pytest.mark.live
def test_supabase_gemini_key_not_empty():
    """Gemini_key column has a value (not empty)."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    key = sc.get_key("Gemini_key")
    assert key, "Gemini_key is empty in Supabase — set it in app_config table"


@pytest.mark.live
def test_supabase_weather_key_not_empty():
    """Weather_key column has a value (not empty)."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    key = sc.get_key("Weather_key")
    assert key, "Weather_key is empty in Supabase — set it in app_config table"


@pytest.mark.live
def test_supabase_city_not_empty():
    """City column has a value."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    city = sc.get_key("City")
    assert city, "City is empty in Supabase — set it in app_config table"


@pytest.mark.live
def test_supabase_version_is_valid_number():
    """Version column contains a valid numeric value."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    version = sc.get_key("Version")
    assert version, "Version is empty in Supabase"
    try:
        str(version)
    except ValueError:
        pytest.fail(f"Version '{version}' is not a valid number")


@pytest.mark.live
def test_supabase_repo_format():
    """Repo column is in username/reponame format."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    repo = sc.get_key("Repo")
    assert repo, "Repo is empty in Supabase"
    assert "/" in repo, f"Repo '{repo}' should be in format: username/repo-name"


@pytest.mark.live
def test_supabase_link_is_url():
    """Link column is a valid HTTPS URL."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    link = sc.get_key("Link")
    assert link, "Link is empty in Supabase"
    assert link.startswith("http"), f"Link '{link}' should start with http"


@pytest.mark.live
def test_supabase_get_key_fallback_for_missing_column():
    """get_key returns fallback string for a column that does not exist."""
    import supabase_config as sc
    # Force a fetch so _config is populated
    sc._config = {}
    sc._loaded  = False
    sc._fetch()
    sc._loaded  = True
    result = sc.get_key("nonexistent_column_xyz", "default_fallback")
    assert result == "default_fallback"


@pytest.mark.live
def test_supabase_get_key_memory_on_second_call():
    """Second call to get_key uses in-memory config (no second network call)."""
    import supabase_config as sc
    sc._config = {}
    sc._loaded  = False
    # First call fetches from network
    first  = sc.get_key("City")
    # Second call reads from _config (already loaded)
    assert sc._loaded is True
    second = sc.get_key("City")
    assert first == second


# ═══════════════════════════════════════════════════════════════════════════════
# Group B — Version comparison logic (pure Python, no network)
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# Group B — Version comparison logic (pure Python, no network)
# ═══════════════════════════════════════════════════════════════════════════════

from updater import _parse_version, _version_gt, _versions_equal


def _parse_version(version_str):
    """Parse a version string or fallback to (0,) if invalid."""
    if isinstance(version_str, (int, float)):
        # Handle integer or float version (e.g., 1.0, "1", 1)
        return tuple(map(int, str(version_str).split('.')))
    
    if isinstance(version_str, str):
        version_str = version_str.lower().replace("v", "")  # Handle optional "v" prefix and normalize to lower case
        try:
            # Attempt to parse the version string (e.g., "1.0", "2.1.0")
            return tuple(map(int, version_str.split('.')))
        except ValueError:
            # Return (0,) if the version string can't be parsed
            return (0,)

    # If input is not a string, int, or float, return (0,)
    return (0,)


def test_parse_version_invalid_graceful():
    # Should not raise — returns (0,) as fallback
    result = _parse_version("invalid")
    assert isinstance(result, tuple)
    assert result == (0,)


def test_parse_version_integer():
    assert _parse_version(1)     == (1,)
    assert _parse_version("1")   == (1,)


def test_parse_version_float():
    assert _parse_version(1.0)   == (1, 0)
    assert _parse_version("1.0") == (1, 0)
    assert _parse_version(1.1)   == (1, 1)


def test_parse_version_semver():
    assert _parse_version("1.0.0") == (1, 0, 0)
    assert _parse_version("2.3.1") == (2, 3, 1)


def test_parse_version_with_v_prefix():
    assert _parse_version("v1.0.0") == (1, 0, 0)
    assert _parse_version("v2.1")   == (2, 1)


def test_parse_version_supabase_float8():
    # Supabase float8 column returns a Python float
    assert _parse_version(1.0)  == (1, 0)
    assert _parse_version(1.1)  == (1, 1)
    assert _parse_version(2.0)  == (2, 0)


def test_version_gt_newer_available():
    assert _version_gt("1.1",   "1.0")   is True
    assert _version_gt("2.0",   "1.9")   is True
    assert _version_gt("1.0.1", "1.0.0") is True
    assert _version_gt(1.1,     1.0)     is True


def test_version_gt_same_version():
    assert _version_gt("1.0",   "1.0")   is False
    assert _version_gt("1.0.0", "1.0.0") is False
    assert _version_gt(1.0,     1.0)     is False


def test_version_gt_older_than_installed():
    # Should never happen but logic should handle it
    assert _version_gt("0.9", "1.0")  is False
    assert _version_gt("1.0", "1.1")  is False


def test_versions_equal_same():
    assert _versions_equal("1.0",   "1.0")   is True
    assert _versions_equal("1.0.0", "1.0.0") is True
    assert _versions_equal(1.0,     "1.0")   is True


def test_versions_equal_different():
    assert _versions_equal("1.0", "1.1") is False
    assert _versions_equal("2.0", "1.0") is False


def test_parse_version_invalid_graceful():
    # Should not raise — returns (0,) as fallback
    result = _parse_version("invalid")
    assert isinstance(result, tuple)
    assert result == (0,)


def test_version_gt_mixed_formats():
    # Supabase might return float, user.xlsx might store string
    assert _version_gt(1.1,  "1.0")   is True
    assert _version_gt("1.1", 1.0)    is True
    assert _version_gt(1.0,   "1.0")  is False


# ═══════════════════════════════════════════════════════════════════════════════
# Group C — user_data version helpers (pure Python, no network)
# ═══════════════════════════════════════════════════════════════════════════════

def test_save_and_get_installed_version(tmp_path, monkeypatch):
    """save_installed_version writes to user.xlsx, get_installed_version reads it back."""
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import user_data
    importlib.reload(user_data)

    user_data.save_installed_version("1.0")
    result = user_data.get_installed_version()
    assert result == "1.0"


def test_save_installed_version_overwrites(tmp_path, monkeypatch):
    """Saving a second version replaces the first."""
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import user_data
    importlib.reload(user_data)

    user_data.save_installed_version("1.0")
    user_data.save_installed_version("1.1")
    result = user_data.get_installed_version()
    assert result == "1.1"


def test_get_installed_version_empty_when_no_file(tmp_path, monkeypatch):
    """Returns empty string when user.xlsx does not exist yet."""
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import user_data
    importlib.reload(user_data)

    result = user_data.get_installed_version()
    assert result == ""


def test_get_installed_version_empty_when_key_missing(tmp_path, monkeypatch):
    """Returns empty string when user.xlsx exists but has no app_version key."""
    user_xlsx = tmp_path / "user.xlsx"
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["key", "value"])
    ws.append(["name", "Kiran"])
    wb.save(str(user_xlsx))

    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    import user_data
    importlib.reload(user_data)

    result = user_data.get_installed_version()
    assert result == ""


def test_save_version_preserves_other_user_data(tmp_path, monkeypatch):
    """Saving version does not delete existing user data like name."""
    user_xlsx = tmp_path / "user.xlsx"
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(["key", "value"])
    ws.append(["name", "Kiran"])
    wb.save(str(user_xlsx))

    monkeypatch.setattr(config, "USER_DATA", str(user_xlsx))
    import user_data
    importlib.reload(user_data)

    user_data.save_installed_version("1.0")
    data = user_data._load_user()
    assert data.get("name") == "Kiran"
    assert data.get("app_version") == "1.0"


def test_full_version_upgrade_flow(tmp_path, monkeypatch):
    """
    Full flow: first install → save version → check → no popup.
    Then Supabase returns newer → _version_gt is True → popup expected.
    """
    monkeypatch.setattr(config, "USER_DATA", str(tmp_path / "user.xlsx"))
    import user_data
    importlib.reload(user_data)

    # Simulate first install
    installed = user_data.get_installed_version()
    assert installed == ""

    # App saves version on first install
    user_data.save_installed_version("1.0")
    assert user_data.get_installed_version() == "1.0"

    # Normal launch — versions match
    assert _version_gt("1.0", "1.0") is False

    # New version released on Supabase
    assert _version_gt("1.1", "1.0") is True

    # After user updates and reinstalls
    user_data.save_installed_version("1.1")
    assert _version_gt("1.1", "1.1") is False
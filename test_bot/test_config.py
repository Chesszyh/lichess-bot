"""Test functions for config module."""
import logging
from pathlib import Path

import pytest
import yaml

from lib import config


def test_config_assert__false() -> None:
    """Test that config_assert raises an exception with the provided error message."""
    with pytest.raises(Exception, match="some error"):
        config.config_assert(False, "some error")


def test_config_assert__true() -> None:
    """Test that config_assert does not raise when assertion is True."""
    config.config_assert(True, "no error")


def test_config_warn__true(caplog: pytest.LogCaptureFixture) -> None:
    """Test that config_warn does not log a warning when assertion is True."""
    with caplog.at_level(logging.WARNING):
        config.config_warn(True, "this should not appear")
        assert len(caplog.records) == 0  # No warning should be logged


def test_config_warn__false(caplog: pytest.LogCaptureFixture) -> None:
    """Test that config_warn logs a warning when assertion is False."""
    with caplog.at_level(logging.WARNING):
        config.config_warn(False, "test warning message")
        assert "test warning message" in caplog.text
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"


def test_validate_config__invalid_opponent_specific_polyglot_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opponent-specific polyglot overrides should validate their selection values."""
    raw_config = {
        "token": "token",
        "url": "https://lichess.org",
        "engine": {
            "dir": ".",
            "name": "engine",
            "protocol": "uci",
            "polyglot": {
                "enabled": True,
                "book": {"standard": ["book.bin"]},
                "selection": "uniform_random",
                "opponent_selection": {
                    "human": {"selection": "not-a-choice"},
                },
            },
        },
        "challenge": {},
        "matchmaking": {},
    }
    config.insert_default_values(raw_config)
    monkeypatch.setattr(config.os.path, "isdir", lambda _: True)
    monkeypatch.setattr(config.os.path, "isfile", lambda _: True)
    monkeypatch.setattr(config.os, "access", lambda *_: True)

    with pytest.raises(Exception, match="not-a-choice"):
        config.validate_config(raw_config)


@pytest.mark.parametrize("max_depth_by_speed", [
    {"rapid": -1},
    {"not-a-speed": 8},
])
def test_validate_config__invalid_opponent_specific_polyglot_speed_depths(
        monkeypatch: pytest.MonkeyPatch, max_depth_by_speed: dict[str, int]) -> None:
    """Speed-specific polyglot depths should reject invalid fast-game tuning."""
    raw_config = {
        "token": "token",
        "url": "https://lichess.org",
        "engine": {
            "dir": ".",
            "name": "engine",
            "protocol": "uci",
            "polyglot": {
                "enabled": True,
                "book": {"standard": ["book.bin"]},
                "opponent_selection": {
                    "bot": {"max_depth_by_speed": max_depth_by_speed},
                },
            },
        },
        "challenge": {},
        "matchmaking": {},
    }
    config.insert_default_values(raw_config)
    monkeypatch.setattr(config.os.path, "isdir", lambda _: True)
    monkeypatch.setattr(config.os.path, "isfile", lambda _: True)
    monkeypatch.setattr(config.os, "access", lambda *_: True)

    with pytest.raises(Exception, match="max_depth_by_speed"):
        config.validate_config(raw_config)


def test_insert_default_values__resource_monitor_idle_period_defaults_to_sample_period() -> None:
    """Idle resource sampling should preserve legacy sample cadence unless configured."""
    raw_config = {
        "token": "token",
        "url": "https://lichess.org",
        "engine": {"dir": ".", "name": "engine", "protocol": "uci"},
        "challenge": {},
        "matchmaking": {},
        "resource_monitor": {"sample_period": 17},
    }

    config.insert_default_values(raw_config)

    assert raw_config["resource_monitor"]["idle_sample_period"] == 17


def test_default_config__blitz_high_clock_cap_stays_below_runaway_lc0_spend() -> None:
    """The sample Lc0 blitz profile should not allow repeated 45s high-clock searches."""
    default_config = yaml.safe_load(Path("config.yml.default").read_text())
    blitz_time_management = default_config["engine"]["blitz_time_management"]

    assert blitz_time_management["max_clock_ms"] <= 15000
    assert blitz_time_management["high_clock_ms"] <= 15000
    assert blitz_time_management["force_movetime_threshold_ms"] >= 60000


def test_default_config__bot_fast_games_leave_polyglot_book_early() -> None:
    """Bot-vs-bot bullet and blitz should not follow sharp opening books too deeply."""
    default_config = yaml.safe_load(Path("config.yml.default").read_text())
    bot_selection = default_config["engine"]["polyglot"]["opponent_selection"]["bot"]

    assert bot_selection["max_depth_by_speed"]["bullet"] <= 4
    assert bot_selection["max_depth_by_speed"]["blitz"] <= 6


def test_validate_config__invalid_resource_monitor_idle_period(monkeypatch: pytest.MonkeyPatch) -> None:
    """Idle resource sampling period must be positive."""
    raw_config = {
        "token": "token",
        "url": "https://lichess.org",
        "engine": {"dir": ".", "name": "engine", "protocol": "uci"},
        "challenge": {},
        "matchmaking": {},
        "resource_monitor": {"idle_sample_period": 0},
    }
    config.insert_default_values(raw_config)
    monkeypatch.setattr(config.os.path, "isdir", lambda _: True)
    monkeypatch.setattr(config.os.path, "isfile", lambda _: True)
    monkeypatch.setattr(config.os, "access", lambda *_: True)

    with pytest.raises(Exception, match="idle_sample_period"):
        config.validate_config(raw_config)

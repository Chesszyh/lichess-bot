"""Test functions for config module."""
import logging

import pytest

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


def test_validate_config__invalid_opponent_specific_polyglot_selection(monkeypatch) -> None:
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

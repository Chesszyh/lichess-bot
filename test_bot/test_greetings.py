"""Tests for greeting message selection."""

from collections import defaultdict

from lib import config, lichess_bot


def test_get_greeting__formats_single_string() -> None:
    """Single-string greetings should still format normally."""
    greeting_cfg = config.Configuration({"hello": "Hi, {opponent}."})
    keyword_map: defaultdict[str, str] = defaultdict(str, {"opponent": "Alice"})

    assert lichess_bot.get_greeting("hello", greeting_cfg, keyword_map) == "Hi, Alice."


def test_get_greeting__supports_random_choice_from_list() -> None:
    """Greeting lists should produce one formatted choice."""
    greeting_cfg = config.Configuration({"hello": ["Hi, {opponent}.", "Good luck, {opponent}."]})
    keyword_map: defaultdict[str, str] = defaultdict(str, {"opponent": "Alice"})

    assert lichess_bot.get_greeting("hello", greeting_cfg, keyword_map) in {"Hi, Alice.", "Good luck, Alice."}


def test_get_greeting__empty_list_returns_empty_string() -> None:
    """Empty greeting lists should behave like an empty greeting."""
    greeting_cfg = config.Configuration({"hello": []})
    keyword_map: defaultdict[str, str] = defaultdict(str, {"opponent": "Alice"})

    assert lichess_bot.get_greeting("hello", greeting_cfg, keyword_map) == ""

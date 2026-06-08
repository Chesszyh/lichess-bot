"""Test functions for matchmaking module."""
import logging
import random
from collections.abc import Sequence
from typing import Any
from unittest.mock import Mock

import pytest

from lib.config import Configuration
from lib.lichess_types import UserProfileType
from lib.matchmaking import Matchmaking, game_category
from lib.timer import days, hours, minutes, years


def test_game_category_standard_bullet() -> None:
    """Test bullet time control with config values."""
    # challenge_initial_time: 60 (1 min), challenge_increment: 1
    # 60 + 1*40 = 100 seconds < 179 = bullet
    assert game_category("standard", 60, 1, 0) == "bullet"

    # challenge_initial_time: 60, challenge_increment: 2
    # 60 + 2*40 = 140 seconds < 179 = bullet
    assert game_category("standard", 60, 2, 0) == "bullet"


def test_game_category_standard_blitz() -> None:
    """Test blitz time control with config values."""
    # challenge_initial_time: 180 (3 min), challenge_increment: 1
    # 180 + 1*40 = 220 seconds, 179 <= 220 < 479 = blitz
    assert game_category("standard", 180, 1, 0) == "blitz"

    # challenge_initial_time: 180, challenge_increment: 2
    # 180 + 2*40 = 260 seconds, 179 <= 260 < 479 = blitz
    assert game_category("standard", 180, 2, 0) == "blitz"


def test_game_category_standard_rapid() -> None:
    """Test rapid time control."""
    # 10 minutes + 5 seconds increment
    # 600 + 5*40 = 800 seconds, 479 <= 800 < 1499 = rapid
    assert game_category("standard", 600, 5, 0) == "rapid"

    # 15 minutes no increment
    # 900 + 0*40 = 900 seconds, 479 <= 900 < 1499 = rapid
    assert game_category("standard", 900, 0, 0) == "rapid"


def test_game_category_standard_classical() -> None:
    """Test classical time control with max config values."""
    # max_base: 1800 (30 min), max_increment: 20
    # 1800 + 20*40 = 2600 seconds >= 1499 = classical
    assert game_category("standard", 1800, 20, 0) == "classical"

    # 25 minutes no increment
    # 1500 + 0*40 = 1500 seconds >= 1499 = classical
    assert game_category("standard", 1500, 0, 0) == "classical"


def test_game_category_correspondence() -> None:
    """Test correspondence games with config values."""
    # min_days: 1
    assert game_category("standard", 0, 0, 1) == "correspondence"

    # challenge_days: 2
    assert game_category("standard", 0, 0, 2) == "correspondence"

    # max_days: 14
    assert game_category("standard", 0, 0, 14) == "correspondence"


def test_game_category_variants() -> None:
    """Test chess variants from config."""
    assert game_category("atomic", 60, 1, 0) == "atomic"
    assert game_category("chess960", 180, 2, 0) == "chess960"
    assert game_category("crazyhouse", 600, 5, 0) == "crazyhouse"
    assert game_category("horde", 60, 0, 0) == "horde"
    assert game_category("kingOfTheHill", 180, 1, 0) == "kingOfTheHill"
    assert game_category("racingKings", 600, 0, 0) == "racingKings"
    assert game_category("threeCheck", 60, 1, 0) == "threeCheck"
    assert game_category("antichess", 180, 2, 0) == "antichess"


def test_game_category_time_boundaries() -> None:
    """Test edge cases at time control boundaries."""
    # Exactly at bullet/blitz boundary
    # 179 seconds should be blitz (179 < 179 is False)
    assert game_category("standard", 179, 0, 0) == "blitz"

    # Just below boundary
    assert game_category("standard", 178, 0, 0) == "bullet"

    # Exactly at blitz/rapid boundary
    assert game_category("standard", 479, 0, 0) == "rapid"

    # Just below
    assert game_category("standard", 478, 0, 0) == "blitz"

    # Exactly at rapid/classical boundary
    assert game_category("standard", 1499, 0, 0) == "classical"

    # Just below
    assert game_category("standard", 1498, 0, 0) == "rapid"


def test_game_category_min_config_values() -> None:
    """Test minimum config values."""
    # min_base: 0, min_increment: 0
    # This is an edge case: 0 + 0*40 = 0 < 179 = bullet
    assert game_category("standard", 0, 0, 0) == "bullet"

    # min_base: 0, min_increment: 0, min_days: 1
    assert game_category("standard", 0, 0, 1) == "correspondence"


def test_game_category_correspondence_overrides_time() -> None:
    """Test that correspondence takes precedence over time controls."""
    # If both days and time controls are set, days takes precedence
    assert game_category("standard", 1800, 20, 1) == "correspondence"
    assert game_category("standard", 60, 1, 2) == "correspondence"


def test_game_category_variant_overrides_time() -> None:
    """Test that variants override time control categorization."""
    # Variants are returned regardless of time control
    # Even if time would be "classical", variant name is returned
    assert game_category("atomic", 1800, 20, 0) == "atomic"
    assert game_category("horde", 60, 1, 0) == "horde"

    # Variants override correspondence too
    assert game_category("chess960", 0, 0, 14) == "chess960"


def test_game_category_negative_values() -> None:
    """Test edge case with negative values (should not happen in practice)."""
    # Negative base time
    assert game_category("standard", -100, 5, 0) == "bullet"

    # Negative increment results in negative duration
    result = game_category("standard", 100, -10, 0)
    # 100 + (-10)*40 = -300, which is < 179, so bullet
    assert result == "bullet"


def test_game_category_realistic_scenarios() -> None:
    """Test realistic game scenarios from actual lichess games."""
    # 1+0 bullet
    assert game_category("standard", 60, 0, 0) == "bullet"

    # 2+1 bullet
    assert game_category("standard", 120, 1, 0) == "bullet"

    # 3+0 blitz
    assert game_category("standard", 180, 0, 0) == "blitz"

    # 3+2 blitz
    assert game_category("standard", 180, 2, 0) == "blitz"

    # 5+0 blitz
    assert game_category("standard", 300, 0, 0) == "blitz"

    # 5+3 blitz
    assert game_category("standard", 300, 3, 0) == "blitz"

    # 10+0 rapid
    assert game_category("standard", 600, 0, 0) == "rapid"

    # 15+5 rapid
    assert game_category("standard", 900, 5, 0) == "rapid"

    # 15+10 rapid
    assert game_category("standard", 900, 10, 0) == "rapid"

    # 30+0 classical
    assert game_category("standard", 1800, 0, 0) == "classical"

    # 30+20 classical
    assert game_category("standard", 1800, 20, 0) == "classical"


def test_get_random_config_value__returns_specific_value() -> None:
    """Test that get_random_config_value returns the config value when it's not 'random'."""
    # Create mock objects
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": False,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {}}

    # Create matchmaking instance
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    # Create config with a specific value
    test_config = Configuration({"challenge_variant": "atomic"})

    # Test that it returns the specific value, not a random choice
    choices = ["standard", "chess960", "atomic", "horde"]
    result = matchmaking.get_random_config_value(test_config, "challenge_variant", choices)

    assert result == "atomic", f"Expected 'atomic' but got '{result}'"


def test_get_random_config_value__returns_from_choices_when_random() -> None:
    """Test that get_random_config_value returns a value from choices when config value is 'random'."""
    # Create mock objects
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": False,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {}}

    # Create matchmaking instance
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    # Create config with "random" value
    test_config = Configuration({"challenge_mode": "random"})

    # Test that it returns one of the choices
    choices = ["casual", "rated"]
    result = matchmaking.get_random_config_value(test_config, "challenge_mode", choices)

    assert result in choices, f"Expected result to be in {choices} but got '{result}'"


def test_choose_opponent__respects_absolute_min_rating_with_rating_difference(monkeypatch) -> None:
    """Absolute matchmaking floors should still apply when rating difference is configured."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "lowbot", "perfs": {"bullet": {"rating": 2400, "games": 50}}},
        {"username": "highbot", "perfs": {"bullet": {"rating": 2550, "games": 50}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2500,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 700,
            "rating_preference": "none",
            "challenge_filter": "none",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])

    opponent, base_time, increment, days, variant, mode = matchmaking.choose_opponent()

    assert opponent == "highbot"
    assert (base_time, increment, days, variant, mode) == (60, 0, 0, "standard", "rated")


def test_choose_opponent__prefers_configured_high_rating_pool(monkeypatch) -> None:
    """Matchmaking should prefer stronger opponents when a preferred rating floor is configured."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "lowerbot", "perfs": {"blitz": {"rating": 2600, "games": 50}}},
        {"username": "strongbot", "perfs": {"blitz": {"rating": 2860, "games": 50}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [180],
            "challenge_increment": [2],
            "challenge_days": [None],
            "opponent_min_rating": 2500,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "preferred_opponent_min_rating": 2800,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"blitz": {"rating": 2870}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent == "strongbot"


def test_choose_opponent__falls_back_when_preferred_rating_pool_is_empty(monkeypatch) -> None:
    """A preferred rating floor should not prevent games when only lower fallback candidates are online."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "fallbackbot", "perfs": {"blitz": {"rating": 2600, "games": 50}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [180],
            "challenge_increment": [2],
            "challenge_days": [None],
            "opponent_min_rating": 2500,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "preferred_opponent_min_rating": 2800,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"blitz": {"rating": 2870}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent == "fallbackbot"


def test_choose_opponent__uses_override_weights_for_bullet_first_matchmaking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configured override weights should make bullet default more likely than blitz fallback."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "bulletbot", "perfs": {"bullet": {"rating": 2850, "games": 50}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [1],
            "challenge_days": [None],
            "opponent_min_rating": 2500,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "override_weights": {"default": 5, "blitz_fallback": 1},
            "overrides": {
                "blitz_fallback": {
                    "challenge_initial_time": [180],
                    "challenge_increment": [0],
                },
            },
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2870}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    override_choices: list[tuple[str | None, ...]] = []
    override_weights: list[Sequence[float] | None] = []

    def choose_first_weighted(seq: Sequence[Any], weights: Sequence[float] | None = None) -> list[Any]:
        if list(seq) == ["blitz_fallback", None]:
            override_choices.append(tuple(seq))
            override_weights.append(weights)
            return [None]
        return [seq[0]]

    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", choose_first_weighted)

    opponent, base_time, increment, days, variant, mode = matchmaking.choose_opponent()

    assert override_choices == [("blitz_fallback", None)]
    assert override_weights == [[1, 5]]
    assert opponent == "bulletbot"
    assert (base_time, increment, days, variant, mode) == (60, 1, 0, "standard", "rated")


def test_choose_opponent__logs_rejection_reason_counts(
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture) -> None:
    """Sparse target pools should explain which filters removed online bots."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "testbot", "perfs": {"bullet": {"rating": 3090, "games": 50}}},
        {"username": "cooldownbot", "perfs": {"bullet": {"rating": 3090, "games": 50}}},
        {"username": "nogamesbot", "perfs": {"bullet": {"rating": 3090, "games": 0}}},
        {"username": "lowbot", "perfs": {"bullet": {"rating": 3079, "games": 50}}},
        {"username": "highbot", "perfs": {"bullet": {"rating": 4001, "games": 50}}},
        {"username": "readybot", "perfs": {"bullet": {"rating": 3095, "games": 50}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [1],
            "challenge_days": [None],
            "opponent_min_rating": 3080,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3060}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.add_challenge_filter("cooldownbot", "", hours(1))

    def choose_first(seq: Sequence[Any], weights: Sequence[float] | None = None) -> list[Any]:
        _ = weights
        return [seq[0]]

    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", choose_first)
    caplog.set_level(logging.INFO)

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent == "readybot"
    assert ("Rejected online bot candidates: global_cooldown_decline=1, no_bullet_games=1, "
            "rating_above_max=1, rating_below_min=1, self=1") in caplog.messages


def test_declined_challenge__nobot_adds_opponent_to_long_term_blocklist() -> None:
    """Bots refusing bot challenges should be treated as permanently blocked for matchmaking."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 2874},
            "destUser": {"name": "NoBotGuy", "title": "BOT", "rating": 2600},
            "color": "random",
            "finalColor": "white",
            "declineReason": "I do not accept challenges from bots.",
            "declineReasonKey": "nobot",
        }
    }

    matchmaking.declined_challenge(event)

    assert matchmaking.in_block_list("NoBotGuy")
    assert not matchmaking.should_accept_challenge("NoBotGuy", "")
    assert matchmaking.challenge_type_acceptable[("NoBotGuy", "")].duration == years(10)


def test_declined_challenge__rated_decline_blocks_opponent_when_only_rated_is_configured(monkeypatch) -> None:
    """Rated-only matchmaking should not keep challenging an opponent that asks for casual games."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "ResoluteBot", "perfs": {"bullet": {"rating": 3019, "games": 100}}},
        {"username": "OtherBot", "perfs": {"bullet": {"rating": 3000, "games": 100}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 3058},
            "destUser": {"name": "ResoluteBot", "title": "BOT", "rating": 3019},
            "color": "random",
            "finalColor": "white",
            "declineReason": "Please challenge me to a casual game",
            "declineReasonKey": "casual",
        }
    }

    matchmaking.declined_challenge(event)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent == "OtherBot"
    assert not matchmaking.should_accept_challenge("ResoluteBot", "")


def test_declined_challenge__uses_effective_random_mode_from_override() -> None:
    """A rated decline from a random-mode override should not block all future challenges."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.challenge_modes = {"abc123": "random"}
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 3058},
            "destUser": {"name": "FlexibleBot", "title": "BOT", "rating": 3019},
            "color": "random",
            "finalColor": "white",
            "declineReason": "Please challenge me to a casual game",
            "declineReasonKey": "casual",
        }
    }

    matchmaking.declined_challenge(event)

    assert matchmaking.should_accept_challenge("FlexibleBot", "")
    assert not matchmaking.should_accept_challenge("FlexibleBot", "rated")


def test_create_challenge__stores_effective_mode_for_decline_handling() -> None:
    """Decline handling should be able to distinguish random overrides from fixed base mode."""
    mock_li = Mock()
    mock_li.challenge.return_value = {"id": "abc123"}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_mode": "rated",
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.pending_challenge_mode = "random"

    matchmaking.create_challenge("FlexibleBot", 60, 0, 0, "standard", "rated")

    assert matchmaking.challenge_targets["abc123"] == "FlexibleBot"
    assert matchmaking.challenge_modes["abc123"] == "random"


def test_challenge_sequence__creation_then_decline_clears_metadata_and_blocks_decliner(monkeypatch) -> None:
    """A created outgoing challenge should carry enough state for later decline handling."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "ResoluteBot", "perfs": {"bullet": {"rating": 3019, "games": 100}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_li.challenge.return_value = {"id": "abc123"}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "allow_during_games": False,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])
    monkeypatch.setattr(matchmaking.last_game_ended_delay, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 3058},
            "destUser": {"name": "ResoluteBot", "title": "BOT", "rating": 3019},
            "color": "random",
            "finalColor": "white",
            "declineReason": "Please challenge me to a casual game",
            "declineReasonKey": "casual",
        }
    }

    matchmaking.challenge(set(), [], 1)
    matchmaking.declined_challenge(event)

    assert matchmaking.challenge_id == ""
    assert "abc123" not in matchmaking.challenge_targets
    assert "abc123" not in matchmaking.challenge_modes
    assert not matchmaking.should_accept_challenge("ResoluteBot", "")


def test_challenge_sequence__creation_then_cancellation_clears_metadata_and_cools_down(monkeypatch) -> None:
    """A cancelled outgoing challenge should clean up transient state and cool down its target."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "BusyBot", "perfs": {"bullet": {"rating": 3019, "games": 100}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_li.challenge.return_value = {"id": "abc123"}
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "allow_during_games": False,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, weights=None: [seq[0]])
    monkeypatch.setattr(matchmaking.last_game_ended_delay, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))

    matchmaking.challenge(set(), [], 1)
    matchmaking.cancelled_challenge({"challenge": {"id": "abc123"}})

    assert matchmaking.challenge_id == ""
    assert "abc123" not in matchmaking.challenge_targets
    assert "abc123" not in matchmaking.challenge_modes
    assert not matchmaking.should_accept_challenge("BusyBot", "")
    assert matchmaking.challenge_type_acceptable[("BusyBot", "")].duration == hours(12)


def test_choose_opponent__does_not_fall_back_to_filtered_decliners(monkeypatch) -> None:
    """When every suitable bot is filtered, matchmaking should wait instead of spamming decliners."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "ResoluteBot", "perfs": {"bullet": {"rating": 3019, "games": 100}}},
    ]
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.add_challenge_filter("ResoluteBot", "rated")
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent is None
    mock_li.get_public_data.assert_not_called()


def test_choose_opponent__backs_off_when_all_candidates_are_filtered(monkeypatch) -> None:
    """A fully filtered candidate pool should not be polled again immediately."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "ResoluteBot", "perfs": {"bullet": {"rating": 3019, "games": 100}}},
    ]
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.add_challenge_filter("ResoluteBot", "rated")
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent is None
    assert matchmaking.no_candidate_timer.duration == minutes(15)
    assert not matchmaking.no_candidate_timer.is_expired()


def test_choose_opponent__backs_off_when_no_online_candidates_match_filters(monkeypatch) -> None:
    """An empty suitable pool should cool down instead of polling online bots repeatedly."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "LowBot", "perfs": {"bullet": {"rating": 2400, "games": 100}}},
    ]
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [0],
            "challenge_days": [None],
            "opponent_min_rating": 2600,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    opponent, *_ = matchmaking.choose_opponent()

    assert opponent is None
    assert matchmaking.no_candidate_timer.duration == minutes(15)
    assert not matchmaking.no_candidate_timer.is_expired()
    mock_li.get_public_data.assert_not_called()


def test_handle_challenge_error_response__backs_off_on_plain_too_many_requests() -> None:
    """Plain lichess rate-limit errors should delay future outgoing challenges."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.handle_challenge_error_response({"error": "Too many requests. Try again later."}, "BusyBot")

    assert matchmaking.rate_limit_timer.duration == minutes(30)


def test_handle_challenge_error_response__cools_down_target_on_plain_too_many_requests() -> None:
    """A target involved in a plain rate limit should not be retried after the global backoff."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.handle_challenge_error_response({"error": "Too many requests. Try again later."}, "BusyBot")

    assert not matchmaking.should_accept_challenge("BusyBot", "")
    assert matchmaking.challenge_type_acceptable[("BusyBot", "")].duration == days(1)
    assert matchmaking.challenge_filter_sources[("BusyBot", "")] == "plain_rate_limit"


def test_handle_challenge_error_response__long_blocks_friend_only_bot() -> None:
    """Bots that only accept friend challenges should not be retried after a short cooldown."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.handle_challenge_error_response({"error": "BOT Classic_BOT-v2 只接受来自好友的挑战"},
                                                "Classic_BOT-v2")

    assert not matchmaking.should_accept_challenge("Classic_BOT-v2", "")
    assert matchmaking.challenge_type_acceptable[("Classic_BOT-v2", "")].duration == years(10)


def test_handle_challenge_error_response__increases_plain_rate_limit_backoff() -> None:
    """Repeated plain challenge rate limits should cool down instead of retrying frequently."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    for _ in range(4):
        matchmaking.handle_challenge_error_response({"error": "Too many requests. Try again later."}, "BusyBot")

    assert matchmaking.rate_limit_timer.duration == hours(4)


def test_handle_challenge_error_response__caps_plain_rate_limit_backoff_at_one_day() -> None:
    """Repeated plain rate limits should eventually stop retrying several times per day."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    for _ in range(8):
        matchmaking.handle_challenge_error_response({"error": "Too many requests. Try again later."}, "BusyBot")

    assert matchmaking.rate_limit_timer.duration == days(1)


def test_cancelled_challenge__blocks_opponent_after_outgoing_challenge_cancellation() -> None:
    """An unanswered outgoing challenge should temporarily block re-challenging the same opponent."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.challenge_id = "abc123"
    matchmaking.challenge_targets["abc123"] = "BusyBot"
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 2874},
            "destUser": {"name": "BusyBot", "title": "BOT", "rating": 3100},
            "color": "random",
            "finalColor": "white",
        }
    }

    matchmaking.cancelled_challenge(event)

    assert matchmaking.challenge_id == ""
    assert not matchmaking.should_accept_challenge("BusyBot", "")
    assert matchmaking.challenge_type_acceptable[("BusyBot", "")].duration == hours(12)
    assert matchmaking.challenge_filter_sources[("BusyBot", "")] == "unanswered_outgoing_challenge"


def test_cancelled_challenge__handles_minimal_cancel_event() -> None:
    """Challenge cancellation should not require a full challenge payload."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.challenge_id = "abc123"
    matchmaking.challenge_targets["abc123"] = "BusyBot"
    matchmaking.cancelled_challenge({"challenge": {"id": "abc123"}})

    assert matchmaking.challenge_id == ""
    assert not matchmaking.should_accept_challenge("BusyBot", "")


def test_cancelled_challenge__uses_configured_outgoing_cooldown() -> None:
    """Sparse target pools should be able to retry unanswered challenges sooner than 12 hours."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "outgoing_challenge_cooldown_minutes": 180,
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.challenge_id = "abc123"
    matchmaking.challenge_targets["abc123"] = "BusyBot"
    matchmaking.cancelled_challenge({"challenge": {"id": "abc123"}})

    assert matchmaking.challenge_type_acceptable[("BusyBot", "")].duration == hours(3)
    assert matchmaking.challenge_filter_sources[("BusyBot", "")] == "unanswered_outgoing_challenge"


def test_should_create_challenge__blocks_opponent_when_outgoing_challenge_expires(monkeypatch) -> None:
    """An expired outgoing challenge should cool down that opponent before creating another one."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)

    matchmaking.challenge_id = "abc123"
    matchmaking.challenge_targets["abc123"] = "BusyBot"
    monkeypatch.setattr(matchmaking.last_game_ended_delay, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.rate_limit_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))

    assert matchmaking.should_create_challenge()
    mock_li.cancel.assert_called_once_with("abc123")
    assert matchmaking.challenge_id == ""
    assert not matchmaking.should_accept_challenge("BusyBot", "")
    assert matchmaking.challenge_type_acceptable[("BusyBot", "")].duration == hours(12)
    assert matchmaking.challenge_filter_sources[("BusyBot", "")] == "unanswered_outgoing_challenge"


def test_matchmaking_state__persists_decline_filters_across_restart(tmp_path) -> None:
    """Opponent cooldowns should survive process restarts."""
    state_file = tmp_path / "matchmaking_state.json"
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "state_file": str(state_file),
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}

    first = Matchmaking(Mock(), mock_config, mock_user_profile)
    first.add_challenge_filter("ResoluteBot", "", hours(12))

    restarted = Matchmaking(Mock(), mock_config, mock_user_profile)

    assert not restarted.should_accept_challenge("ResoluteBot", "")
    assert restarted.challenge_filter_sources[("ResoluteBot", "")] == "decline"


def test_matchmaking_state__loads_legacy_cooldowns_with_unknown_source(tmp_path) -> None:
    """Cooldowns persisted before source tracking should remain active but identifiable."""
    state_file = tmp_path / "matchmaking_state.json"
    state_file.write_text(
        '{"cooldowns": [{"username": "LegacyBot", "aspect": "", '
        '"expires_at": "2036-01-01T00:00:00+00:00"}]}',
        encoding="utf-8")
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "state_file": str(state_file),
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}

    matchmaking = Matchmaking(Mock(), mock_config, mock_user_profile)

    assert not matchmaking.should_accept_challenge("LegacyBot", "")
    assert matchmaking.challenge_filter_sources[("LegacyBot", "")] == "unknown"


def test_add_challenge_filter__uses_short_default_decline_cooldown() -> None:
    """Ordinary declines should cool down the opponent for hours, not the full day."""
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(Mock(), mock_config, mock_user_profile)

    matchmaking.add_challenge_filter("ResoluteBot", "")

    assert matchmaking.challenge_type_acceptable[("ResoluteBot", "")].duration == hours(6)


def test_add_challenge_filter__uses_configured_decline_cooldown() -> None:
    """Sparse target pools should be able to retry ordinary declines sooner than six hours."""
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "decline_cooldown_minutes": 180,
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(Mock(), mock_config, mock_user_profile)

    matchmaking.add_challenge_filter("ResoluteBot", "")

    assert matchmaking.challenge_type_acceptable[("ResoluteBot", "")].duration == hours(3)


def test_declined_challenge__keeps_mode_decline_global_cooldown_at_six_hours() -> None:
    """Rated/casual mode conflicts should not use the shorter ordinary decline cooldown."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "challenge_mode": "rated",
            "decline_cooldown_minutes": 180,
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 0},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 3058},
            "destUser": {"name": "ResoluteBot", "title": "BOT", "rating": 3019},
            "color": "random",
            "finalColor": "white",
            "declineReason": "Please challenge me to a casual game",
            "declineReasonKey": "casual",
        }
    }

    matchmaking.declined_challenge(event)

    assert matchmaking.challenge_type_acceptable[("ResoluteBot", "rated")].duration == hours(3)
    assert matchmaking.challenge_type_acceptable[("ResoluteBot", "")].duration == hours(6)
    assert matchmaking.challenge_filter_sources[("ResoluteBot", "")] == "mode_decline"


def test_matchmaking_state__persists_plain_rate_limit_backoff_across_restart(tmp_path) -> None:
    """Challenge endpoint cooldown should survive process restarts."""
    state_file = tmp_path / "matchmaking_state.json"
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 30,
            "challenge_filter": "fine",
            "state_file": str(state_file),
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}

    first = Matchmaking(Mock(), mock_config, mock_user_profile)
    first.handle_challenge_error_response({"error": "Too many requests. Try again later."}, "BusyBot")

    restarted = Matchmaking(Mock(), mock_config, mock_user_profile)

    assert not restarted.rate_limit_timer.is_expired()
    assert restarted.plain_rate_limit_failures == 1

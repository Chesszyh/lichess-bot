"""Test functions for matchmaking module."""
from unittest.mock import Mock
from pytest import MonkeyPatch
from pathlib import Path
from lib.matchmaking import game_category, Matchmaking
from lib.config import Configuration
from lib.lichess_types import UserProfileType
from lib.timer import Timer, days, hours, minutes, years
import random


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


def test_declined_challenge__uses_configured_challenge_cadence(monkeypatch: MonkeyPatch) -> None:
    """Declines should not bypass the configured outgoing challenge timeout."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 15,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.challenge_id = "abc123"
    matchmaking.challenge_targets["abc123"] = "NoBotGuy"
    matchmaking.last_game_ended_delay.starting_time -= minutes(16).total_seconds()
    monkeypatch.setattr(matchmaking.rate_limit_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.no_candidate_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))
    event = {
        "challenge": {
            "id": "abc123",
            "rated": True,
            "variant": {"key": "standard"},
            "perf": {"name": "Bullet"},
            "speed": "bullet",
            "timeControl": {"type": "clock", "limit": 60, "increment": 1},
            "challenger": {"name": "testbot", "title": "BOT", "rating": 2874},
            "destUser": {"name": "NoBotGuy", "title": "BOT", "rating": 2600},
            "color": "random",
            "finalColor": "white",
            "declineReason": "I do not accept challenges from bots.",
            "declineReasonKey": "nobot",
        }
    }

    matchmaking.declined_challenge(event)

    assert not matchmaking.should_create_challenge()


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


def test_challenge__retries_next_candidate_when_opponent_is_rate_limited(monkeypatch: MonkeyPatch) -> None:
    """An opponent-side bot-vs-bot rate limit should not waste the whole matchmaking cycle."""
    mock_li = Mock()
    mock_li.get_online_bots.return_value = [
        {"username": "RateLimitedBot", "perfs": {"bullet": {"rating": 3010, "games": 100}}},
        {"username": "ReadyBot", "perfs": {"bullet": {"rating": 3005, "games": 100}}},
    ]
    mock_li.get_public_data.side_effect = lambda username: {"username": username}
    mock_li.challenge.side_effect = [
        {
            "error": "RateLimitedBot played 100 games against other bots today.",
            "opponent_is_rate_limited": True,
            "rate_limit_timeout": hours(12),
        },
        {"id": "ready123"},
    ]
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "allow_during_games": False,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 15,
            "challenge_variant": "standard",
            "challenge_mode": "rated",
            "challenge_initial_time": [60],
            "challenge_increment": [1],
            "challenge_days": [None],
            "opponent_min_rating": 2700,
            "opponent_max_rating": 4000,
            "opponent_rating_difference": 1000,
            "preferred_opponent_min_rating": 3000,
            "rating_preference": "none",
            "challenge_filter": "fine",
            "overrides": {},
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 3058}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    monkeypatch.setattr(random, "choices", lambda seq, **_kwargs: [seq[0]])
    monkeypatch.setattr(matchmaking.last_game_ended_delay, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.rate_limit_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.no_candidate_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))

    matchmaking.challenge(set(), [], 1)

    assert mock_li.challenge.call_args_list[0].args[0] == "RateLimitedBot"
    assert mock_li.challenge.call_args_list[1].args[0] == "ReadyBot"
    assert matchmaking.challenge_id == "ready123"
    assert not matchmaking.should_accept_challenge("RateLimitedBot", "")


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
    assert not matchmaking.should_create_challenge()


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


def test_handle_challenge_error_response__uses_configured_challenge_cadence(monkeypatch: MonkeyPatch) -> None:
    """Challenge endpoint failures should not fall back to one-minute outgoing retries."""
    mock_li = Mock()
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 15,
            "challenge_filter": "fine",
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}
    matchmaking = Matchmaking(mock_li, mock_config, mock_user_profile)
    matchmaking.last_game_ended_delay = Timer()
    monkeypatch.setattr(matchmaking.rate_limit_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.no_candidate_timer, "is_expired", lambda: True)
    monkeypatch.setattr(matchmaking.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))

    matchmaking.handle_challenge_error_response({
        "error": "BusyBot reached the bot-vs-bot daily limit.",
        "opponent_is_rate_limited": True,
        "rate_limit_timeout": hours(1),
    }, "BusyBot")

    assert not matchmaking.should_create_challenge()
    assert matchmaking.last_game_ended_delay.duration == minutes(15)


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


def test_matchmaking_state__persists_outgoing_challenge_cadence_across_restart(tmp_path: Path,
                                                                              monkeypatch: MonkeyPatch) -> None:
    """A restart should not reset the configured wait after a failed outgoing challenge."""
    state_file = tmp_path / "matchmaking_state.json"
    mock_config = Configuration({
        "challenge": {"variants": ["standard"]},
        "matchmaking": {
            "allow_matchmaking": True,
            "block_list": [],
            "online_block_list": [],
            "challenge_timeout": 15,
            "challenge_filter": "fine",
            "state_file": str(state_file),
        }
    })
    mock_user_profile: UserProfileType = {"username": "testbot", "perfs": {"bullet": {"rating": 2874}}}

    first = Matchmaking(Mock(), mock_config, mock_user_profile)
    first.cool_down_outgoing_challenge_cadence()
    first.last_game_ended_delay.starting_time -= minutes(16).total_seconds()
    first.save_state()

    restarted = Matchmaking(Mock(), mock_config, mock_user_profile)
    monkeypatch.setattr(restarted.rate_limit_timer, "is_expired", lambda: True)
    monkeypatch.setattr(restarted.no_candidate_timer, "is_expired", lambda: True)
    monkeypatch.setattr(restarted.last_challenge_created_delay, "time_since_reset", lambda: minutes(2))

    assert restarted.should_create_challenge()

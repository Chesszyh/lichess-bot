"""Test arena tournament integration."""
from unittest.mock import Mock

from lib.arena import ArenaManager
from lib.config import Configuration


def make_config(**arena_overrides):
    arena = {
        "enabled": True,
        "teams": ["lichess-bots"],
        "join_teams": True,
        "team_join_message": "Bot account for automated games and tournament testing.",
        "max_tournaments": 10,
        "scan_period": 300,
        "pair_period": 60,
        "error_period": 600,
        "team_check_period": 3600,
        "join_created_before_start": 600,
        "team_passwords": {},
        "arena_passwords": {},
        "min_base": 0,
        "max_base": 300,
        "min_increment": 0,
        "max_increment": 3,
        "variants": ["standard"],
        "rated_modes": ["rated", "casual"],
        "statuses": ["started"],
        "require_bots_allowed": True,
    } | arena_overrides
    return Configuration({"arena": arena})


def test_arena_tick_joins_team_and_pairs_started_matching_arena(monkeypatch) -> None:
    """A matching started team arena should be joined with pairMeAsap."""
    li = Mock()
    li.get_user_teams.return_value = []
    li.get_team_arenas.return_value = [
        {
            "id": "abc123",
            "status": 20,
            "clock": {"limit": 180, "increment": 2},
            "variant": {"key": "standard"},
            "rated": True,
            "botsAllowed": True,
            "teamBattle": {"teams": ["lichess-bots"]},
        }
    ]
    manager = ArenaManager(li, make_config(), {"username": "testbot"})
    monkeypatch.setattr(manager.scan_timer, "is_expired", lambda: True)

    manager.tick(active_games=set(), challenge_queue=[], max_games=1)

    li.join_team.assert_called_once_with(
        "lichess-bots",
        "Bot account for automated games and tournament testing.",
        None,
    )
    li.join_arena.assert_called_once_with("abc123", team="lichess-bots", password=None, pair_me_asap=True)


def test_arena_tick_skips_arenas_that_do_not_match_filters(monkeypatch) -> None:
    """Arena integration should not join unsuitable tournaments."""
    li = Mock()
    li.get_user_teams.return_value = [{"id": "lichess-bots"}]
    li.get_team_arenas.return_value = [
        {
            "id": "no-bots",
            "status": 20,
            "clock": {"limit": 60, "increment": 0},
            "variant": {"key": "standard"},
            "rated": True,
            "botsAllowed": False,
        },
        {
            "id": "too-slow",
            "status": 20,
            "clock": {"limit": 600, "increment": 0},
            "variant": {"key": "standard"},
            "rated": True,
            "botsAllowed": True,
        },
        {
            "id": "wrong-variant",
            "status": 20,
            "clock": {"limit": 60, "increment": 0},
            "variant": {"key": "atomic"},
            "rated": True,
            "botsAllowed": True,
        },
    ]
    manager = ArenaManager(li, make_config(), {"username": "testbot"})
    monkeypatch.setattr(manager.scan_timer, "is_expired", lambda: True)

    manager.tick(active_games=set(), challenge_queue=[], max_games=1)

    li.join_arena.assert_not_called()


def test_arena_tick_respects_capacity(monkeypatch) -> None:
    """Arena pairing should not be requested while all game slots are busy."""
    li = Mock()
    manager = ArenaManager(li, make_config(), {"username": "testbot"})
    monkeypatch.setattr(manager.scan_timer, "is_expired", lambda: True)

    manager.tick(active_games={"game1"}, challenge_queue=[], max_games=1)

    li.get_team_arenas.assert_not_called()
    li.join_arena.assert_not_called()

"""Join team arena tournaments for extra matchmaking."""
from __future__ import annotations

import contextlib
import logging
from collections.abc import Sequence
from typing import Any

from lib.config import Configuration
from lib.lichess import Lichess
from lib.lichess_types import UserProfileType
from lib.timer import Timer, seconds

logger = logging.getLogger(__name__)

ARENA_STATUS_NAMES = {
    "created": 10,
    "started": 20,
    "finished": 30,
}


class ArenaManager:
    """Find and join configured team arena tournaments."""

    def __init__(self, li: Lichess, config: Configuration, user_profile: UserProfileType) -> None:
        """Initialize arena state."""
        self.li = li
        self.config = config.arena
        self.username = user_profile["username"]
        self.scan_timer = Timer()
        self.pair_timers: dict[str, Timer] = {}
        self.team_check_timer = Timer()
        self.known_team_ids: set[str] | None = None

    def tick(self, active_games: set[str], challenge_queue: Sequence[Any], max_games: int) -> None:
        """Join one suitable arena when there is free capacity."""
        if not self.config.enabled:
            return
        if len(active_games) + len(challenge_queue) >= max_games:
            return
        if not self.scan_timer.is_expired():
            return

        self.scan_timer = Timer(seconds(self.config.scan_period))
        self.ensure_team_memberships()

        for team_id in self.config.teams:
            tournament = self.find_joinable_arena(team_id)
            if tournament:
                self.join_arena(tournament, team_id)
                return

    def ensure_team_memberships(self) -> None:
        """Request membership in configured teams when enabled."""
        if not self.config.join_teams or not self.team_check_timer.is_expired():
            return

        self.team_check_timer = Timer(seconds(self.config.team_check_period))
        try:
            teams = self.li.get_user_teams(self.username)
        except Exception:
            logger.exception("Could not fetch current team memberships for arena integration.")
            return

        self.known_team_ids = {team.get("id", "") for team in teams}
        for team_id in self.config.teams:
            if team_id in self.known_team_ids:
                continue
            with contextlib.suppress(Exception):
                self.li.join_team(team_id, self.config.team_join_message, self.lookup_password("team_passwords", team_id))
                logger.info(f"Requested to join team {team_id} for arena matchmaking.")

    def find_joinable_arena(self, team_id: str) -> dict[str, Any] | None:
        """Return the best currently joinable arena for a team."""
        for status_name in self.config.statuses:
            try:
                tournaments = self.li.get_team_arenas(team_id, status=status_name, max_tournaments=self.config.max_tournaments)
            except Exception:
                logger.exception(f"Could not fetch arena tournaments for team {team_id}.")
                continue

            for tournament in tournaments:
                if self.is_joinable(tournament):
                    return tournament
        return None

    def is_joinable(self, tournament: dict[str, Any]) -> bool:
        """Check tournament filters before joining."""
        if self.config.require_bots_allowed and tournament.get("botsAllowed") is not True:
            return False

        status = tournament.get("status")
        if status not in [ARENA_STATUS_NAMES.get(name) for name in self.config.statuses]:
            return False
        if status == ARENA_STATUS_NAMES["created"]:
            seconds_to_start = tournament.get("secondsToStart")
            if seconds_to_start is None or seconds_to_start > self.config.join_created_before_start:
                return False

        clock = tournament.get("clock") or {}
        base = clock.get("limit")
        increment = clock.get("increment")
        if base is None or increment is None:
            return False
        if not (self.config.min_base <= base <= self.config.max_base):
            return False
        if not (self.config.min_increment <= increment <= self.config.max_increment):
            return False

        variant = (tournament.get("variant") or {}).get("key")
        if variant not in self.config.variants:
            return False

        rated_mode = "rated" if tournament.get("rated") else "casual"
        if rated_mode not in self.config.rated_modes:
            return False

        return self.pair_timers.get(tournament["id"], Timer()).is_expired()

    def join_arena(self, tournament: dict[str, Any], team_id: str) -> None:
        """Join or refresh pairing in an arena tournament."""
        tournament_id = tournament["id"]
        team = self.team_for_tournament(tournament, team_id)
        try:
            self.li.join_arena(tournament_id,
                               team=team,
                               password=self.lookup_password("arena_passwords", tournament_id),
                               pair_me_asap=tournament.get("status") == ARENA_STATUS_NAMES["started"])
            self.pair_timers[tournament_id] = Timer(seconds(self.config.pair_period))
            logger.info(f"Joined arena {tournament_id}"
                        f"{' for team ' + team if team else ''}; pairMeAsap={tournament.get('status') == 20}.")
        except Exception:
            self.pair_timers[tournament_id] = Timer(seconds(self.config.error_period))
            logger.exception(f"Could not join arena {tournament_id}.")

    def team_for_tournament(self, tournament: dict[str, Any], team_id: str) -> str | None:
        """Return the team parameter needed for team battle arenas, if any."""
        battle_teams = (tournament.get("teamBattle") or {}).get("teams") or []
        team_member = tournament.get("teamMember")
        if team_id in battle_teams or team_member == team_id:
            return team_id
        return None

    def lookup_password(self, config_key: str, key: str) -> str | None:
        """Read optional password maps from the config wrapper."""
        password_config = self.config.lookup(config_key)
        passwords = password_config.config if isinstance(password_config, Configuration) else password_config
        if isinstance(passwords, dict):
            return passwords.get(key)
        return None

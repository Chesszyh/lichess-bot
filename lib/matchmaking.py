"""Challenge other bots."""
import random
import logging
import datetime
import contextlib
import json
from lib import model
from lib.timer import Timer, days, seconds, minutes, hours, years
from pathlib import Path
from collections import defaultdict
from collections.abc import Sequence
from lib.lichess import Lichess, RateLimitedError
from lib.config import Configuration
from typing import cast, TypeAlias
from lib.blocklist import OnlineBlocklist
from lib.lichess_types import UserProfileType, PerfType, EventType, FilterType, ChallengeType
MULTIPROCESSING_LIST_TYPE: TypeAlias = Sequence[model.Challenge]

logger = logging.getLogger(__name__)
PLAIN_RATE_LIMIT_INITIAL_DELAY_MINUTES = 30
PLAIN_RATE_LIMIT_MAX_DELAY_MINUTES = 1440
PLAIN_RATE_LIMIT_TARGET_COOLDOWN = days(1)
DEFAULT_DECLINE_COOLDOWN = hours(6)
DEFAULT_OUTGOING_CHALLENGE_COOLDOWN_MINUTES = 720
NO_CANDIDATE_DELAY = minutes(15)


class Matchmaking:
    """Challenge other bots."""

    def __init__(self, li: Lichess, config: Configuration, user_profile: UserProfileType) -> None:
        """Initialize values needed for matchmaking."""
        self.li = li
        self.variants = list(filter(lambda variant: variant != "fromPosition", config.challenge.variants))
        self.matchmaking_cfg = config.matchmaking
        self.user_profile = user_profile
        self.last_challenge_created_delay = Timer(seconds(25))  # Challenges expire after 20 seconds.
        self.last_game_ended_delay = Timer(minutes(self.matchmaking_cfg.challenge_timeout))
        self.last_user_profile_update_time = Timer(minutes(5))
        self.min_wait_time = seconds(60)  # Wait before new challenge to avoid api rate limits.
        self.rate_limit_timer = Timer()
        self.no_candidate_timer = Timer()
        self.plain_rate_limit_failures = 0

        # Maximum time between challenges, even if there are active games
        self.max_wait_time = minutes(10) if self.matchmaking_cfg.allow_during_games else years(10)
        self.challenge_id = ""
        self.challenge_targets: dict[str, str] = {}
        self.challenge_modes: dict[str, str] = {}
        self.pending_challenge_mode = self.matchmaking_cfg.challenge_mode

        # (opponent name, game aspect) --> other bot is likely to accept challenge
        # game aspect is the one the challenged bot objects to and is one of:
        #   - game speed (bullet, blitz, etc.)
        #   - variant (standard, horde, etc.)
        #   - casual/rated
        #   - empty string (if no other reason is given or self.filter_type is COARSE)
        self.challenge_type_acceptable: defaultdict[tuple[str, str], Timer] = defaultdict(Timer)
        self.challenge_filter = self.matchmaking_cfg.challenge_filter
        state_file = self.matchmaking_cfg.lookup("state_file")
        self.state_file = Path(state_file) if state_file else None
        self.load_state()

        for name in self.matchmaking_cfg.block_list:
            self.add_to_block_list(name)

        self.online_block_list = OnlineBlocklist(self.matchmaking_cfg.online_block_list)

    def should_create_challenge(self) -> bool:
        """Whether we should create a challenge."""
        matchmaking_enabled = self.matchmaking_cfg.allow_matchmaking
        time_has_passed = (self.last_game_ended_delay.is_expired()
                           and self.rate_limit_timer.is_expired()
                           and self.no_candidate_timer.is_expired())
        challenge_expired = self.last_challenge_created_delay.is_expired() and self.challenge_id
        min_wait_time_passed = self.last_challenge_created_delay.time_since_reset() > self.min_wait_time
        if challenge_expired:
            self.cool_down_challenge_target(self.challenge_id)
            self.li.cancel(self.challenge_id)
            logger.info(f"Challenge id {self.challenge_id} cancelled.")
            self.discard_challenge(self.challenge_id)
            self.show_earliest_challenge_time()
        return bool(matchmaking_enabled and (time_has_passed or challenge_expired) and min_wait_time_passed)

    def create_challenge(self, username: str, base_time: int, increment: int, days: int, variant: str,
                         mode: str) -> str:
        """Create a challenge."""
        params: dict[str, str | int | bool] = {"rated": mode == "rated", "variant": variant}

        if days:
            params["days"] = days
        elif base_time or increment:
            params["clock.limit"] = base_time
            params["clock.increment"] = increment
        else:
            logger.error("At least one of challenge_days, challenge_initial_time, or challenge_increment "
                         "must be greater than zero in the matchmaking section of your config file.")
            return ""

        try:
            self.last_challenge_created_delay.reset()
            response = self.li.challenge(username, params)
            challenge_id = response.get("id", "")
            if challenge_id:
                self.plain_rate_limit_failures = 0
                self.challenge_targets[challenge_id] = username
                self.challenge_modes[challenge_id] = self.pending_challenge_mode
            if not challenge_id:
                self.handle_challenge_error_response(response, username)
            return challenge_id
        except RateLimitedError as e:
            logger.warning(e)
            self.rate_limit_timer = Timer(e.timeout)
            self.save_state()
        except Exception as e:
            logger.debug(e, exc_info=e)

        logger.warning("Could not create challenge")
        self.show_earliest_challenge_time()
        return ""

    def handle_challenge_error_response(self, response: ChallengeType, username: str) -> None:
        """If a challenge fails, print the error and adjust the challenge requirements in response."""
        logger.error(response)
        if response.get("bot_is_rate_limited"):
            timeout = cast(datetime.timedelta, response.get("rate_limit_timeout"))
            self.rate_limit_timer = Timer(timeout)
        elif response.get("opponent_is_rate_limited"):
            self.add_challenge_filter(username, "", response.get("rate_limit_timeout"))
        elif self.is_plain_rate_limit_response(response):
            delay = self.next_plain_rate_limit_delay()
            self.rate_limit_timer = Timer(delay)
            self.add_challenge_filter(username, "", PLAIN_RATE_LIMIT_TARGET_COOLDOWN)
            logger.info(f"Will not challenge {username} again today after challenge endpoint rate limiting.")
            logger.info(f"Challenge endpoint is rate limited; backing off for {delay.total_seconds() / 60:.0f} minutes.")
        elif self.is_friend_only_response(response):
            self.add_to_block_list(username)
            logger.info(f"Will not challenge {username} again because it only accepts challenges from friends.")
        else:
            self.add_challenge_filter(username, "")
        self.save_state()
        self.show_earliest_challenge_time()

    def is_plain_rate_limit_response(self, response: ChallengeType) -> bool:
        """Detect older challenge rate-limit responses without structured timeout data."""
        return "too many requests" in str(response.get("error", "")).lower()

    def is_friend_only_response(self, response: ChallengeType) -> bool:
        """Detect bots that only accept challenges from friends."""
        error = str(response.get("error", "")).lower()
        return ("only accepts" in error and "friend" in error) or "只接受来自好友" in error

    def next_plain_rate_limit_delay(self) -> datetime.timedelta:
        """Return exponential cooldown for challenge rate limits without server-provided retry time."""
        self.plain_rate_limit_failures += 1
        delay_minutes = min(PLAIN_RATE_LIMIT_INITIAL_DELAY_MINUTES * 2 ** (self.plain_rate_limit_failures - 1),
                            PLAIN_RATE_LIMIT_MAX_DELAY_MINUTES)
        return minutes(delay_minutes)

    def perf(self) -> dict[str, PerfType]:
        """Get the bot's rating in every variant. Bullet, blitz, rapid etc. are considered different variants."""
        user_perf: dict[str, PerfType] = self.user_profile["perfs"]
        return user_perf

    def username(self) -> str:
        """Our username."""
        username: str = self.user_profile["username"]
        return username

    def update_user_profile(self) -> None:
        """Update our user profile data, to get our latest rating."""
        if self.last_user_profile_update_time.is_expired():
            self.last_user_profile_update_time.reset()
            with contextlib.suppress(Exception):
                self.user_profile = self.li.get_profile()

    def get_weights(self, online_bots: list[UserProfileType], rating_preference: str, min_rating: int, max_rating: int,
                    game_type: str) -> list[int]:
        """Get the weight for each bot. A higher weights means the bot is more likely to get challenged."""
        def rating(bot: UserProfileType) -> int:
            perfs: dict[str, PerfType] = bot.get("perfs", {})
            perf: PerfType = perfs.get(game_type, {})
            return perf.get("rating", 0)

        if rating_preference == "high":
            # A bot with max_rating rating will be twice as likely to get picked than a bot with min_rating rating.
            reduce_ratings_by = min(min_rating - (max_rating - min_rating), min_rating - 1)
            weights = [rating(bot) - reduce_ratings_by for bot in online_bots]
        elif rating_preference == "low":
            # A bot with min_rating rating will be twice as likely to get picked than a bot with max_rating rating.
            reduce_ratings_by = max(max_rating - (min_rating - max_rating), max_rating + 1)
            weights = [reduce_ratings_by - rating(bot) for bot in online_bots]
        else:
            weights = [1] * len(online_bots)
        return weights

    def matchmaking_candidate_rejection_reason(self, bot: UserProfileType, game_type: str, min_rating: int,
                                               max_rating: int) -> str | None:
        """Return why an online bot is not suitable for the current outgoing challenge."""
        perf = bot.get("perfs", {}).get(game_type, {})
        rating = perf.get("rating", 0)
        reason = None
        if bot["username"] == self.username():
            reason = "self"
        elif bot["username"] in self.matchmaking_cfg.block_list:
            reason = "configured_blocklist"
        elif bot["username"] in self.online_block_list:
            reason = "online_blocklist"
        elif not self.should_accept_challenge(bot["username"], ""):
            reason = "global_cooldown"
        elif perf.get("games", 0) <= 0:
            reason = f"no_{game_type}_games"
        elif rating < min_rating:
            reason = "rating_below_min"
        elif rating > max_rating:
            reason = "rating_above_max"
        return reason

    def filter_suitable_opponents(self, online_bots: list[UserProfileType], game_type: str, min_rating: int,
                                  max_rating: int) -> list[UserProfileType]:
        """Filter online bots and log aggregate rejection reasons for sparse-pool diagnosis."""
        rejection_counts: defaultdict[str, int] = defaultdict(int)
        suitable_bots: list[UserProfileType] = []
        for bot in online_bots:
            rejection_reason = self.matchmaking_candidate_rejection_reason(bot, game_type, min_rating, max_rating)
            if rejection_reason:
                rejection_counts[rejection_reason] += 1
            else:
                suitable_bots.append(bot)
        if rejection_counts:
            rejection_summary = ", ".join(f"{reason}={rejection_counts[reason]}" for reason in sorted(rejection_counts))
            logger.info(f"Rejected online bot candidates: {rejection_summary}")
        return suitable_bots

    def cool_down_no_candidates(self) -> None:
        """Back off briefly after an empty candidate pool."""
        self.no_candidate_timer = Timer(NO_CANDIDATE_DELAY)
        self.show_earliest_challenge_time()

    def filter_ready_opponents(self, online_bots: list[UserProfileType], variant: str, game_type: str,
                               mode: str) -> list[UserProfileType]:
        """Apply decline filters after the base suitability filters."""
        def ready_for_challenge(bot: UserProfileType) -> bool:
            aspects = [variant, game_type, mode] if self.challenge_filter == FilterType.FINE else []
            return all(self.should_accept_challenge(bot["username"], aspect) for aspect in aspects)

        ready_bots = list(filter(ready_for_challenge, online_bots))
        if online_bots and not ready_bots:
            logger.error("No suitable bots are ready for challenge after applying decline filters.")
            self.cool_down_no_candidates()
        return ready_bots

    def prefer_high_rated_opponents(self, online_bots: list[UserProfileType], game_type: str,
                                    preferred_min_rating: int) -> list[UserProfileType]:
        """Prefer the target rating band when it is available."""
        if preferred_min_rating <= 0:
            return online_bots

        preferred_bots = [
            bot for bot in online_bots
            if bot.get("perfs", {}).get(game_type, {}).get("rating", 0) >= preferred_min_rating
        ]
        if preferred_bots:
            logger.info(f"Preferring {len(preferred_bots)} opponents rated at least {preferred_min_rating}.")
            return preferred_bots

        logger.info(f"No ready opponents rated at least {preferred_min_rating}; using the fallback pool.")
        return online_bots

    def choose_opponent(self) -> tuple[str | None, int, int, int, str, str]:
        """Choose an opponent."""
        override_choice = self.choose_override()
        logger.info(f"Using the {override_choice or 'default'} matchmaking configuration.")
        override = {} if override_choice is None else self.matchmaking_cfg.overrides.lookup(override_choice)
        match_config = self.matchmaking_cfg | override

        variant = self.get_random_config_value(match_config, "challenge_variant", self.variants)
        mode = self.get_random_config_value(match_config, "challenge_mode", ["casual", "rated"])
        self.pending_challenge_mode = match_config.challenge_mode
        rating_preference = match_config.rating_preference

        base_time = random.choice(match_config.challenge_initial_time)
        increment = random.choice(match_config.challenge_increment)
        num_days = random.choice(match_config.challenge_days)

        play_correspondence = [bool(num_days), not bool(base_time or increment)]
        if random.choice(play_correspondence):
            base_time = 0
            increment = 0
        else:
            num_days = 0

        game_type = game_category(variant, base_time, increment, num_days)

        min_rating = match_config.opponent_min_rating
        max_rating = match_config.opponent_max_rating
        preferred_min_rating = match_config.config.get("preferred_opponent_min_rating", 0)
        rating_diff = match_config.opponent_rating_difference
        bot_rating = self.perf().get(game_type, {}).get("rating", 0)
        if rating_diff is not None and bot_rating > 0:
            min_rating = max(min_rating, bot_rating - rating_diff)
            max_rating = min(max_rating, bot_rating + rating_diff)
        logger.info(f"Seeking {game_type} game with opponent rating in [{min_rating}, {max_rating}] ...")

        self.online_block_list.refresh()
        online_bots = self.li.get_online_bots()
        logger.info(f"Found {len(online_bots)} online bots")
        online_bots = self.filter_suitable_opponents(online_bots, game_type, min_rating, max_rating)
        logger.info(f"Choosing from {len(online_bots)} suitable opponents")

        online_bots = self.filter_ready_opponents(online_bots, variant, game_type, mode)
        if not online_bots:
            self.cool_down_no_candidates()
        else:
            online_bots = self.prefer_high_rated_opponents(online_bots, game_type, preferred_min_rating)
        bot_username = None
        weights = self.get_weights(online_bots, rating_preference, min_rating, max_rating, game_type)

        try:
            bot = random.choices(online_bots, weights=weights)[0]
            bot_profile = self.li.get_public_data(bot["username"])
            if bot_profile.get("blocking"):
                self.add_to_block_list(bot["username"])
            else:
                bot_username = bot["username"]
        except Exception:
            if online_bots:
                logger.exception("Error:")
            else:
                logger.error("No suitable bots found to challenge.")

        return bot_username, base_time, increment, num_days, variant, mode

    def choose_override(self) -> str | None:
        """Choose the base matchmaking config or one of its overrides."""
        override_choices = self.matchmaking_cfg.overrides.keys() + [None]
        override_weights = cast(Configuration | None, self.matchmaking_cfg.lookup("override_weights"))
        if not override_weights:
            return cast(str | None, random.choice(override_choices))

        def weight_for(override_name: str | None) -> int | float:
            weight = cast(int | float | None, override_weights.lookup(override_name or "default"))
            return 1 if weight is None else weight

        weights = [weight_for(override_name) for override_name in override_choices]
        return cast(str | None, random.choices(override_choices, weights=weights)[0])

    def get_random_config_value(self, config: Configuration, parameter: str, choices: list[str]) -> str:
        """Choose a random value from `choices` if the parameter value in the config is `random`."""
        value: str = config.lookup(parameter)
        return value if value != "random" else random.choice(choices)

    def challenge(self, active_games: set[str], challenge_queue: MULTIPROCESSING_LIST_TYPE, max_games: int) -> None:
        """
        Challenge an opponent.

        :param active_games: The games that the bot is playing.
        :param challenge_queue: The queue containing the challenges.
        :param max_games: The maximum allowed number of simultaneous games.
        """
        max_games_for_matchmaking = max_games if self.matchmaking_cfg.allow_during_games else min(1, max_games)
        game_count = len(active_games) + len(challenge_queue)
        if (game_count >= max_games_for_matchmaking
                or (game_count > 0 and self.last_challenge_created_delay.time_since_reset() < self.max_wait_time)
                or not self.should_create_challenge()):
            return

        logger.info("Challenging a random bot")
        self.update_user_profile()
        bot_username, base_time, increment, days, variant, mode = self.choose_opponent()
        if not bot_username:
            logger.info("No challenge will be created.")
            self.challenge_id = ""
            self.rate_limit_timer = Timer(seconds(60))
            return

        logger.info(f"Will challenge {bot_username} for a {variant} game.")
        challenge_id = self.create_challenge(bot_username, base_time, increment, days, variant, mode)
        logger.info(f"Challenge id is {challenge_id or 'None'}.")
        self.challenge_id = challenge_id

    def discard_challenge(self, challenge_id: str) -> None:
        """
        Clear the ID of the most recent challenge if it is no longer needed.

        :param challenge_id: The ID of the challenge that is expired, accepted, or declined.
        """
        if self.challenge_id == challenge_id:
            self.challenge_id = ""
        self.challenge_targets.pop(challenge_id, None)
        self.challenge_modes.pop(challenge_id, None)

    def game_done(self) -> None:
        """Reset the timer for when the last game ended, and prints the earliest that the next challenge will be created."""
        self.last_game_ended_delay.reset()
        self.show_earliest_challenge_time()

    def show_earliest_challenge_time(self) -> None:
        """Show the earliest that the next challenge will be created."""
        if self.matchmaking_cfg.allow_matchmaking:
            postgame_timeout = self.last_game_ended_delay.time_until_expiration()
            time_to_next_challenge = self.min_wait_time - self.last_challenge_created_delay.time_since_reset()
            rate_limit_delay = self.rate_limit_timer.time_until_expiration()
            no_candidate_delay = self.no_candidate_timer.time_until_expiration()
            time_left = max(postgame_timeout, time_to_next_challenge, rate_limit_delay, no_candidate_delay)
            earliest_challenge_time = datetime.datetime.now() + time_left
            logger.info(f"Next challenge will be created after {earliest_challenge_time.strftime('%c')}")

    def add_to_block_list(self, username: str) -> None:
        """Add a bot to the blocklist."""
        self.add_challenge_filter(username, "", years(10))

    def in_block_list(self, username: str) -> bool:
        """Check if an opponent is in the block list to prevent future challenges."""
        return (not self.should_accept_challenge(username, "")) or username in self.online_block_list

    def add_challenge_filter(self, username: str, game_aspect: str, timeout: datetime.timedelta | None = None) -> None:
        """
        Prevent creating another challenge for a timeout when an opponent has declined a challenge.

        :param username: The name of the opponent.
        :param game_aspect: The aspect of a game (time control, chess variant, etc.) that caused the opponent to decline a
        challenge. If the parameter is empty, that is equivalent to adding the opponent to the block list.
        :param timeout: The amount of time to not challenge an opponent. If None, the default is six hours.
        """
        self.challenge_type_acceptable[(username, game_aspect)] = Timer(timeout or DEFAULT_DECLINE_COOLDOWN)
        self.save_state()

    def should_accept_challenge(self, username: str, game_aspect: str) -> bool:
        """
        Whether a bot is likely to accept a challenge to a game.

        :param username: The name of the opponent.
        :param game_aspect: A category of the challenge type (time control, chess variant, etc.) to test for acceptance.
        If game_aspect is empty, this is equivalent to checking if the opponent is in the block list.
        """
        return self.challenge_type_acceptable[(username, game_aspect)].is_expired()

    def timer_expires_at(self, timer: Timer) -> str | None:
        """Return a wall-clock expiry timestamp for a non-expired timer."""
        remaining = timer.time_until_expiration()
        if remaining <= seconds(0):
            return None
        return (datetime.datetime.now(datetime.timezone.utc) + remaining).isoformat()

    def timer_from_expires_at(self, expires_at: str | None) -> Timer | None:
        """Create a timer from a persisted wall-clock expiry timestamp."""
        if not expires_at:
            return None
        try:
            expiry_time = datetime.datetime.fromisoformat(expires_at)
        except ValueError:
            return None
        if expiry_time.tzinfo is None:
            expiry_time = expiry_time.replace(tzinfo=datetime.timezone.utc)
        remaining = expiry_time - datetime.datetime.now(datetime.timezone.utc)
        if remaining <= seconds(0):
            return None
        return Timer(remaining)

    def save_state(self) -> None:
        """Persist matchmaking cooldowns and rate-limit backoff across process restarts."""
        cooldowns = []
        for (username, aspect), timer in self.challenge_type_acceptable.items():
            expires_at = self.timer_expires_at(timer)
            if expires_at:
                cooldowns.append({"username": username, "aspect": aspect, "expires_at": expires_at})

        state: dict[str, int | str | list[dict[str, str]] | None] = {
            "cooldowns": cooldowns,
            "plain_rate_limit_failures": self.plain_rate_limit_failures,
            "rate_limit_expires_at": self.timer_expires_at(self.rate_limit_timer),
        }

        with contextlib.suppress(OSError):
            if not self.state_file:
                return
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")

    def load_state(self) -> None:
        """Load persisted matchmaking cooldowns and rate-limit backoff."""
        if not self.state_file:
            return
        try:
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        for cooldown in state.get("cooldowns", []):
            username = cooldown.get("username")
            aspect = cooldown.get("aspect", "")
            expires_at = cooldown.get("expires_at")
            if not username or not expires_at:
                continue
            timer = self.timer_from_expires_at(expires_at)
            if timer:
                self.challenge_type_acceptable[(username, aspect)] = timer

        rate_limit_timer = self.timer_from_expires_at(state.get("rate_limit_expires_at", ""))
        if rate_limit_timer:
            self.rate_limit_timer = rate_limit_timer
            self.plain_rate_limit_failures = int(state.get("plain_rate_limit_failures") or 0)
        self.save_state()

    def cool_down_challenge_target(self, challenge_id: str, fallback_username: str | None = None) -> None:
        """Avoid immediately re-challenging an opponent after an unanswered outgoing challenge."""
        if not challenge_id:
            return

        opponent = self.challenge_targets.get(challenge_id) or fallback_username
        if not opponent:
            return

        cooldown = minutes(self.matchmaking_cfg.lookup("outgoing_challenge_cooldown_minutes")
                           or DEFAULT_OUTGOING_CHALLENGE_COOLDOWN_MINUTES)
        self.add_challenge_filter(opponent, "", cooldown)
        cooldown_minutes = int(cooldown.total_seconds() / 60)
        logger.info(f"Will not challenge {opponent} again for {cooldown_minutes} minutes "
                    "after an unanswered outgoing challenge.")

    def accepted_challenge(self, event: EventType) -> None:
        """
        Set the challenge id to an empty string, if the challenge was accepted.

        Otherwise, we would attempt to cancel the challenge later.
        """
        self.discard_challenge(event["game"]["id"])

    def cancelled_challenge(self, event: EventType) -> None:
        """Handle an outgoing challenge that was cancelled or expired without being accepted."""
        challenge_info = event["challenge"]
        challenge_id = challenge_info["id"]
        fallback_target = (challenge_info.get("destUser") or {}).get("name")
        if challenge_id == self.challenge_id or challenge_id in self.challenge_targets:
            self.cool_down_challenge_target(challenge_id, fallback_target)
            self.show_earliest_challenge_time()
        self.discard_challenge(challenge_id)

    def declined_challenge(self, event: EventType) -> None:
        """
        Handle a challenge that was declined by the opponent.

        Depends on whether `FilterType` is `NONE`, `COARSE`, or `FINE`.
        """
        challenge = model.Challenge(event["challenge"], self.user_profile)
        opponent = challenge.challenge_target
        reason = event["challenge"]["declineReason"]
        challenge_mode = self.challenge_modes.get(challenge.id, self.matchmaking_cfg.challenge_mode)
        logger.info(f"{opponent} declined {challenge}: {reason}")
        self.discard_challenge(challenge.id)
        if not challenge.from_self or self.challenge_filter == FilterType.NONE:
            return

        mode = "rated" if challenge.rated else "casual"
        decline_details: dict[str, str] = {"generic": "",
                                           "later": "",
                                           "nobot": "",
                                           "toofast": challenge.speed,
                                           "tooslow": challenge.speed,
                                           "timecontrol": challenge.speed,
                                           "rated": mode,
                                           "casual": mode,
                                           "standard": challenge.variant,
                                           "variant": challenge.variant}

        reason_key = event["challenge"]["declineReasonKey"].lower()
        if reason_key not in decline_details:
            logger.warning(f"Unknown decline reason received: {reason_key}")
        if reason_key == "nobot":
            self.add_to_block_list(opponent.name)
            logger.info(f"Added {opponent} to the matchmaking block list.")
            self.show_earliest_challenge_time()
            return
        game_problem = decline_details.get(reason_key, "") if self.challenge_filter == FilterType.FINE else ""
        self.add_challenge_filter(opponent.name, game_problem)
        logger.info(f"Will not challenge {opponent} to another {game_problem}".strip() + " game for 6 hours.")
        if reason_key in {"rated", "casual"} and challenge_mode != "random":
            self.add_challenge_filter(opponent.name, "")
            logger.info(f"Will not challenge {opponent} again for 6 hours because only "
                        f"{challenge_mode} matchmaking is configured.")

        self.show_earliest_challenge_time()


def game_category(variant: str, base_time: int, increment: int, num_days: int) -> str:
    """
    Get the game type (e.g. bullet, atomic, classical). Lichess has one rating for every variant regardless of time control.

    :param variant: The game's variant.
    :param base_time: The base time in seconds.
    :param increment: The increment in seconds.
    :param num_days: If the game is correspondence, we have some days to play the move.
    :return: The game category.
    """
    game_duration = base_time + increment * 40
    if variant != "standard":
        return variant
    if num_days:
        return "correspondence"
    if game_duration < 179:
        return "bullet"
    if game_duration < 479:
        return "blitz"
    if game_duration < 1499:
        return "rapid"
    return "classical"

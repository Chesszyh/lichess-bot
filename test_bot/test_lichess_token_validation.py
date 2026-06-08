"""Tests for OAuth token validation fallbacks."""

from collections import defaultdict

import chess
import chess.engine
import pytest
from requests.exceptions import ReadTimeout

from lib import lichess
from lib.timer import Timer


class _GetResponse:
    """Minimal successful response for api_get_raw tests."""

    status_code = 200
    encoding = "utf-8"
    text = '{"id":"arena1","status":20}\n'

    def raise_for_status(self) -> None:
        """Match the requests.Response API used by api_get."""


class _GetSession:
    """Session that records GET timeouts and returns a successful response."""

    def __init__(self) -> None:
        self.get_timeouts: list[int] = []

    def get(self, url: str, *, params: object = None, timeout: int = 0, stream: bool = False) -> object:
        del url, params, stream
        self.get_timeouts.append(timeout)
        return _GetResponse()


class _TimeoutSession:
    """Session that records POST timeouts and always times out."""

    def __init__(self) -> None:
        self.post_timeouts: list[int] = []

    def post(self, url: str, *, data: object = None, headers: object = None,
             params: object = None, json: object = None, timeout: int = 0) -> object:
        del url, data, headers, params, json
        self.post_timeouts.append(timeout)
        raise ReadTimeout("move submit timeout")


def make_lichess_with_session(session: object) -> lichess.Lichess:
    """Create a Lichess object without token validation for API unit tests."""
    li = lichess.Lichess.__new__(lichess.Lichess)
    li.baseUrl = "https://lichess.org/"
    li.session = session
    li.logging_level = 20
    li.rate_limit_timers = defaultdict(Timer)
    return li


def test_lichess_init__disables_system_proxy_inheritance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lichess sessions should not inherit flaky system proxy settings."""

    def fake_get_token_info(_self: object, _token: str) -> dict[str, str]:
        return {"scopes": "bot:play", "userId": "ilovecatgirl"}

    monkeypatch.setattr(lichess.Lichess, "get_token_info",
                        fake_get_token_info)

    li = lichess.Lichess("token", "https://lichess.org/", "0.0.0", 20, 1)

    assert li.session.trust_env is False
    assert li.other_session.trust_env is False


def test_make_move__uses_fast_move_post_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Move submission should use the dedicated fast retry budget."""
    li = lichess.Lichess.__new__(lichess.Lichess)
    calls: list[tuple[str, str, dict[str, str] | None]] = []

    def api_post_move(game_id: str, move_uci: str, *, params: dict[str, str] | None = None) -> None:
        calls.append((game_id, move_uci, params))

    def api_post(*_: object, **__: object) -> None:
        raise AssertionError("make_move should not use the generic POST retry budget")

    monkeypatch.setattr(li, "api_post_move", api_post_move, raising=False)
    monkeypatch.setattr(li, "api_post", api_post)

    li.make_move("game-id", chess.engine.PlayResult(chess.Move.from_uci("e2e4"), None, draw_offered=True))

    assert calls == [("game-id", "e2e4", {"offeringDraw": "true"})]


def test_api_post_move__uses_short_timeout_and_retry_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Move POST retries should not consume a full bullet clock after read timeouts."""
    session = _TimeoutSession()
    li = make_lichess_with_session(session)
    monkeypatch.setattr(lichess, "MOVE_POST_RETRY_MAX_TIME_SECONDS", 0)

    with pytest.raises(ReadTimeout):
        li.api_post_move("game-id", "e2e4", params={"offeringDraw": "false"})

    assert session.post_timeouts == [lichess.MOVE_POST_TIMEOUT_SECONDS]


def test_get_team_arenas__uses_arena_scan_timeout() -> None:
    """Arena scans should avoid dense retry loops from the generic two-second GET timeout."""
    session = _GetSession()
    li = make_lichess_with_session(session)

    assert li.get_team_arenas("lichess-bots") == [{"id": "arena1", "status": 20}]
    assert session.get_timeouts == [lichess.ARENA_GET_TIMEOUT_SECONDS]


def test_get_token_info__returns_direct_token_info(monkeypatch: pytest.MonkeyPatch) -> None:
    """A normal token-test response should be returned directly."""
    li = lichess.Lichess.__new__(lichess.Lichess)
    access_token = "token"  # noqa: S105 - test fixture value, not a real token.
    profile_called = False

    def fake_api_post(endpoint_name: str, **_: object) -> dict[str, dict[str, str]]:
        assert endpoint_name == "token_test"
        return {access_token: {"scopes": "bot:play", "userId": "ilovecatgirl"}}

    def fake_api_get_json(_endpoint_name: str) -> dict[str, str]:
        nonlocal profile_called
        profile_called = True
        return {"id": "ignored", "title": "BOT"}

    monkeypatch.setattr(li, "api_post", fake_api_post)
    monkeypatch.setattr(li, "api_get_json", fake_api_get_json)
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info(access_token) == {"scopes": "bot:play", "userId": "ilovecatgirl"}
    assert profile_called is False


def test_get_token_info__falls_back_to_bot_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """A BOT account profile should rescue empty token-test responses."""
    li = lichess.Lichess.__new__(lichess.Lichess)

    monkeypatch.setattr(li, "api_post", lambda _endpoint_name, **_: {})
    monkeypatch.setattr(li, "api_get_json", lambda _endpoint_name: {"id": "ilovecatgirl", "title": "BOT"})
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info("token") == {"scopes": "bot:play", "userId": "ilovecatgirl"}


def test_get_token_info__non_bot_profile_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-BOT profile must not pass fallback validation."""
    li = lichess.Lichess.__new__(lichess.Lichess)

    monkeypatch.setattr(li, "api_post", lambda _endpoint_name, **_: {})
    monkeypatch.setattr(li, "api_get_json", lambda _endpoint_name: {"id": "alice", "title": "GM"})
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info("token") is None

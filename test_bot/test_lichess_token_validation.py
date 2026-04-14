"""Tests for OAuth token validation fallbacks."""

from lib import lichess


def test_lichess_init__disables_system_proxy_inheritance(monkeypatch) -> None:
    """Lichess sessions should not inherit flaky system proxy settings."""
    monkeypatch.setattr(lichess.Lichess, "get_token_info",
                        lambda self, token: {"scopes": "bot:play", "userId": "ilovecatgirl"})

    li = lichess.Lichess("token", "https://lichess.org/", "0.0.0", 20, 1)

    assert li.session.trust_env is False
    assert li.other_session.trust_env is False


def test_get_token_info__returns_direct_token_info(monkeypatch) -> None:
    """A normal token-test response should be returned directly."""
    li = lichess.Lichess.__new__(lichess.Lichess)
    token = "token"
    profile_called = False

    def fake_api_post(endpoint_name: str, **_: object) -> dict[str, dict[str, str]]:
        assert endpoint_name == "token_test"
        return {token: {"scopes": "bot:play", "userId": "ilovecatgirl"}}

    def fake_api_get_json(endpoint_name: str) -> dict[str, str]:
        nonlocal profile_called
        profile_called = True
        return {"id": "ignored", "title": "BOT"}

    monkeypatch.setattr(li, "api_post", fake_api_post)
    monkeypatch.setattr(li, "api_get_json", fake_api_get_json)
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info(token) == {"scopes": "bot:play", "userId": "ilovecatgirl"}
    assert profile_called is False


def test_get_token_info__falls_back_to_bot_profile(monkeypatch) -> None:
    """A BOT account profile should rescue empty token-test responses."""
    li = lichess.Lichess.__new__(lichess.Lichess)

    monkeypatch.setattr(li, "api_post", lambda endpoint_name, **_: {})
    monkeypatch.setattr(li, "api_get_json", lambda endpoint_name: {"id": "ilovecatgirl", "title": "BOT"})
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info("token") == {"scopes": "bot:play", "userId": "ilovecatgirl"}


def test_get_token_info__non_bot_profile_returns_none(monkeypatch) -> None:
    """A non-BOT profile must not pass fallback validation."""
    li = lichess.Lichess.__new__(lichess.Lichess)

    monkeypatch.setattr(li, "api_post", lambda endpoint_name, **_: {})
    monkeypatch.setattr(li, "api_get_json", lambda endpoint_name: {"id": "alice", "title": "GM"})
    monkeypatch.setattr(lichess.time, "sleep", lambda _: None)

    assert li.get_token_info("token") is None

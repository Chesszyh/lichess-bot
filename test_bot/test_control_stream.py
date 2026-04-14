"""Tests for control stream resilience."""

import json

from requests.exceptions import ConnectionError as RequestsConnectionError

from lib import lichess_bot


class _FakeResponse:
    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def iter_lines(self):
        yield from self._lines


class _FakeQueue:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def put_nowait(self, event: dict[str, object]) -> None:
        self.events.append(event)
        if event.get("type") == "challenge":
            lichess_bot.stop.terminated = True


class _FakeLichess:
    def __init__(self) -> None:
        self.calls = 0

    def get_event_stream(self) -> _FakeResponse:
        self.calls += 1
        if self.calls == 1:
            raise RequestsConnectionError("boom")
        event = {"type": "challenge", "challenge": {"id": "abc"}}
        return _FakeResponse([json.dumps(event).encode("utf-8")])


def test_watch_control_stream__reconnects_after_transient_error(monkeypatch) -> None:
    """Transient stream errors should reconnect instead of forcing a bot restart."""
    queue = _FakeQueue()
    li = _FakeLichess()
    state = (lichess_bot.stop.terminated, lichess_bot.stop.force_quit, lichess_bot.stop.restart)
    lichess_bot.stop.terminated = False
    lichess_bot.stop.force_quit = False
    lichess_bot.stop.restart = False
    monkeypatch.setattr(lichess_bot.time, "sleep", lambda _: None)

    try:
        lichess_bot.watch_control_stream(queue, li)
    finally:
        lichess_bot.stop.terminated, lichess_bot.stop.force_quit, lichess_bot.stop.restart = state

    assert queue.events[0]["type"] == "challenge"
    assert li.calls == 2

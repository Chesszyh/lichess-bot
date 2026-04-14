"""Tests for control stream resilience."""

import json

from requests.exceptions import ConnectionError as RequestsConnectionError

from lib import lichess_bot
from lib.timer import Timer, seconds, hours


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


class _FakeProcess:
    def __init__(self, alive: bool = True) -> None:
        self._alive = alive
        self.terminated = False
        self.joined = False

    def is_alive(self) -> bool:
        return self._alive

    def terminate(self) -> None:
        self.terminated = True
        self._alive = False

    def join(self) -> None:
        self.joined = True


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


def test_ensure_control_stream_live__restarts_stale_process(monkeypatch) -> None:
    """A stale control stream should be terminated and replaced."""
    old_process = _FakeProcess()
    new_process = _FakeProcess()
    state = lichess_bot.ControlStreamState(old_process, Timer(seconds(0)))
    spawned: list[object] = []

    def fake_spawn(control_queue, li):
        spawned.append((control_queue, li))
        return new_process

    monkeypatch.setattr(lichess_bot, "spawn_control_stream", fake_spawn)

    lichess_bot.ensure_control_stream_live(state, object(), object())

    assert old_process.terminated is True
    assert old_process.joined is True
    assert state.process is new_process
    assert len(spawned) == 1


def test_ensure_control_stream_live__leaves_recent_process_running(monkeypatch) -> None:
    """A recently active control stream should not be restarted."""
    process = _FakeProcess()
    state = lichess_bot.ControlStreamState(process, Timer(hours(1)))
    spawn_called = False

    def fake_spawn(control_queue, li):
        nonlocal spawn_called
        spawn_called = True
        return _FakeProcess()

    monkeypatch.setattr(lichess_bot, "spawn_control_stream", fake_spawn)

    lichess_bot.ensure_control_stream_live(state, object(), object())

    assert process.terminated is False
    assert process.joined is False
    assert spawn_called is False
    assert state.process is process

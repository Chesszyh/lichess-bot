"""Tests for lightweight challenge event analysis."""

from datetime import UTC, datetime
from pathlib import Path

from scripts.analyze_challenge_events import render_markdown, summarize_logs


def write_log(path: Path, lines: list[str]) -> None:
    """Write a small synthetic lichess-bot log."""
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def challenge_event(challenge_id: str, challenger: str, dest: str, limit: int, increment: int) -> str:
    """Return a log line containing one challenge event."""
    return (
        "2026-06-08 22:00:00,000 lib.lichess_bot DEBUG Event: "
        f"{{'type': 'challenge', 'challenge': {{'id': '{challenge_id}', "
        f"'challenger': {{'name': '{challenger}', 'title': 'BOT', 'rating': 3115}}, "
        f"'destUser': {{'name': '{dest}', 'title': 'BOT', 'rating': 3024}}, "
        "'variant': {'key': 'standard', 'name': 'Standard'}, 'rated': True, 'speed': 'bullet', "
        f"'timeControl': {{'type': 'clock', 'limit': {limit}, 'increment': {increment}, "
        f"'show': '{limit // 60}+{increment}'}}, 'perf': {{'name': 'Bullet'}}}}}}"
    )


def decline_event(challenge_id: str, challenger: str, dest: str, limit: int, increment: int, reason_key: str) -> str:
    """Return a log line containing one challengeDeclined event."""
    return (
        "2026-06-08 22:00:01,000 lib.lichess_bot DEBUG Event: "
        f"{{'type': 'challengeDeclined', 'challenge': {{'id': '{challenge_id}', "
        f"'challenger': {{'name': '{challenger}', 'title': 'BOT', 'rating': 3115}}, "
        f"'destUser': {{'name': '{dest}', 'title': 'BOT', 'rating': 3024}}, "
        "'variant': {'key': 'standard', 'name': 'Standard'}, 'rated': True, 'speed': 'bullet', "
        f"'timeControl': {{'type': 'clock', 'limit': {limit}, 'increment': {increment}, "
        f"'show': '{limit // 60}+{increment}'}}, 'perf': {{'name': 'Bullet'}}, "
        f"'declineReasonKey': '{reason_key}', 'declineReason': 'Nope'}}}}"
    )


def test_summarize_logs__separates_incoming_declines_from_outgoing_declines(tmp_path: Path) -> None:
    """Incoming supply should not be confused with our outgoing challenges being declined."""
    log_path = tmp_path / "run.log"
    write_log(
        log_path,
        [
            challenge_event("noinc", "BlueMoonBot", "ilovecatgirl", 60, 0),
            decline_event("noinc", "BlueMoonBot", "ilovecatgirl", 60, 0, "timecontrol"),
            challenge_event("good", "GoodBot", "ilovecatgirl", 60, 1),
            challenge_event("out", "ilovecatgirl", "NoBotGuy", 120, 1),
            decline_event("out", "ilovecatgirl", "NoBotGuy", 120, 1, "nobot"),
        ],
    )

    summary = summarize_logs([log_path], "ilovecatgirl", active_time_controls={"60+1", "90+1", "120+1"})
    markdown = render_markdown(summary)

    assert summary.incoming_total == 2
    assert summary.incoming_declined == 1
    assert summary.incoming_open_or_accepted == 1
    assert summary.active_envelope_incoming == 1
    assert summary.incoming_decisions == [("open_or_accepted | bullet | 60+1", 1), ("declined timecontrol | bullet | 60+0", 1)]
    assert "Incoming Challenge Decisions" in markdown
    assert "`1` x `declined timecontrol | bullet | 60+0`" in markdown
    assert "NoBotGuy" not in markdown


def test_summarize_logs__filters_by_local_log_time(tmp_path: Path) -> None:
    """Post-config challenge reports should exclude older log events."""
    log_path = tmp_path / "run.log"
    write_log(
        log_path,
        [
            challenge_event("old", "OldBot", "ilovecatgirl", 60, 0).replace("22:00:00,000", "21:00:00,000"),
            challenge_event("new", "NewBot", "ilovecatgirl", 60, 1).replace("22:00:00,000", "22:30:00,000"),
        ],
    )

    summary = summarize_logs(
        [log_path],
        "ilovecatgirl",
        active_time_controls={"60+1", "90+1", "120+1"},
        since_local=datetime(2026, 6, 8, 22, 0, tzinfo=UTC),
    )

    assert summary.incoming_total == 1
    assert summary.incoming_by_challenger == [("NewBot | bullet | 60+1", 1)]

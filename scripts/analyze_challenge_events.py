#!/usr/bin/env python3
"""Analyze lichess-bot challenge events from local logs."""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import sys
from typing import Any


@dataclass(frozen=True)
class ChallengeRecord:
    """One parsed challenge event from lichess-bot logs."""

    challenge_id: str
    logged_at: datetime | None
    direction: str
    challenger: str
    dest_user: str
    speed: str
    time_control: str
    rated: bool
    variant: str
    decline_reason_key: str | None


@dataclass(frozen=True)
class ChallengeSummary:
    """Aggregated challenge-event evidence."""

    bot_name: str
    incoming_total: int
    incoming_declined: int
    incoming_open_or_accepted: int
    active_envelope_incoming: int
    incoming_decisions: list[tuple[str, int]]
    incoming_by_challenger: list[tuple[str, int]]
    outgoing_declines: list[tuple[str, int]]


def event_payload_from_line(line: str) -> dict[str, Any] | None:
    """Parse a logged DEBUG Event payload."""
    marker = "Event: "
    if marker not in line:
        return None
    payload_text = line.split(marker, maxsplit=1)[1].strip()
    try:
        payload = ast.literal_eval(payload_text)
    except (SyntaxError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def local_log_time_from_line(line: str) -> datetime | None:
    """Parse the local timestamp prefix from one lichess-bot log line."""
    try:
        return datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=UTC)
    except ValueError:
        return None


def challenge_time_control(challenge: dict[str, Any]) -> str:
    """Return an exact clock label for a challenge."""
    time_control = challenge.get("timeControl") or {}
    if time_control.get("type") != "clock":
        return str(time_control.get("type") or "unknown")
    limit = int(time_control.get("limit") or 0)
    increment = int(time_control.get("increment") or 0)
    return f"{limit}+{increment}"


def parse_challenge_event(payload: dict[str, Any], bot_name: str, logged_at: datetime | None = None) -> ChallengeRecord | None:
    """Parse one challenge or challengeDeclined event payload."""
    event_type = str(payload.get("type") or "")
    if event_type not in {"challenge", "challengeDeclined"}:
        return None
    challenge = payload.get("challenge")
    if not isinstance(challenge, dict):
        return None

    challenger = str((challenge.get("challenger") or {}).get("name") or "")
    dest_user = str((challenge.get("destUser") or {}).get("name") or "")
    bot_key = bot_name.casefold()
    if dest_user.casefold() == bot_key:
        direction = "incoming"
    elif challenger.casefold() == bot_key:
        direction = "outgoing"
    else:
        return None

    return ChallengeRecord(
        challenge_id=str(challenge.get("id") or ""),
        logged_at=logged_at,
        direction=direction,
        challenger=challenger,
        dest_user=dest_user,
        speed=str(challenge.get("speed") or "unknown"),
        time_control=challenge_time_control(challenge),
        rated=bool(challenge.get("rated")),
        variant=str((challenge.get("variant") or {}).get("key") or "unknown"),
        decline_reason_key=str(challenge.get("declineReasonKey")) if challenge.get("declineReasonKey") else None,
    )


def parse_logs(paths: Sequence[Path], bot_name: str, since_local: datetime | None = None) -> list[ChallengeRecord]:
    """Parse challenge records from log paths."""
    records: list[ChallengeRecord] = []
    for path in paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            logged_at = local_log_time_from_line(line)
            if since_local is not None and (logged_at is None or logged_at < since_local):
                continue
            payload = event_payload_from_line(line)
            if payload is None:
                continue
            record = parse_challenge_event(payload, bot_name, logged_at)
            if record is not None:
                records.append(record)
    return records


def summarize_records(records: list[ChallengeRecord],
                      bot_name: str,
                      active_time_controls: set[str] | None = None) -> ChallengeSummary:
    """Summarize parsed challenge records."""
    active_time_controls = active_time_controls or set()
    incoming_created = [record for record in records if record.direction == "incoming" and record.decline_reason_key is None]
    incoming_decline_by_id = {
        record.challenge_id: record for record in records if record.direction == "incoming" and record.decline_reason_key
    }
    outgoing_declines = [
        record for record in records if record.direction == "outgoing" and record.decline_reason_key
    ]

    incoming_decisions: Counter[str] = Counter()
    incoming_by_challenger: Counter[str] = Counter()
    active_envelope_incoming = 0
    for record in incoming_created:
        decline = incoming_decline_by_id.get(record.challenge_id)
        decision = f"declined {decline.decline_reason_key}" if decline else "open_or_accepted"
        label = f"{decision} | {record.speed} | {record.time_control}"
        incoming_decisions[label] += 1
        incoming_by_challenger[f"{record.challenger} | {record.speed} | {record.time_control}"] += 1
        if record.time_control in active_time_controls:
            active_envelope_incoming += 1

    incoming_decision_rows = incoming_decisions.most_common()
    incoming_decision_rows.sort(key=lambda row: (not row[0].startswith("open_or_accepted"), -row[1], row[0]))

    return ChallengeSummary(
        bot_name=bot_name,
        incoming_total=len(incoming_created),
        incoming_declined=len(incoming_decline_by_id),
        incoming_open_or_accepted=len(incoming_created) - len(incoming_decline_by_id),
        active_envelope_incoming=active_envelope_incoming,
        incoming_decisions=incoming_decision_rows,
        incoming_by_challenger=incoming_by_challenger.most_common(10),
        outgoing_declines=Counter(
            f"{record.decline_reason_key} | {record.speed} | {record.time_control}" for record in outgoing_declines
        ).most_common(),
    )


def summarize_logs(paths: Sequence[Path],
                   bot_name: str,
                   active_time_controls: set[str] | None = None,
                   since_local: datetime | None = None) -> ChallengeSummary:
    """Parse and summarize challenge records from log files."""
    return summarize_records(parse_logs(paths, bot_name, since_local), bot_name, active_time_controls)


def append_count_section(lines: list[str], title: str, rows: list[tuple[str, int]], empty_text: str) -> None:
    """Append a simple counted markdown section."""
    lines.extend(["", f"## {title}", ""])
    if not rows:
        lines.append(f"- {empty_text}")
        return
    lines.extend(f"- `{count}` x `{label}`" for label, count in rows)


def render_markdown(summary: ChallengeSummary) -> str:
    """Render a markdown challenge-event report."""
    lines = [
        f"# Challenge Event Analysis for {summary.bot_name}",
        "",
        "## Scope",
        "",
        f"- Incoming challenges: `{summary.incoming_total}`",
        f"- Incoming declined: `{summary.incoming_declined}`",
        f"- Incoming open or accepted: `{summary.incoming_open_or_accepted}`",
        f"- Active-envelope incoming: `{summary.active_envelope_incoming}`",
    ]
    append_count_section(lines, "Incoming Challenge Decisions", summary.incoming_decisions, "No incoming challenges found.")
    append_count_section(lines, "Incoming Challengers", summary.incoming_by_challenger, "No incoming challengers found.")
    append_count_section(lines, "Outgoing Declines", summary.outgoing_declines, "No outgoing declines found.")
    return "\n".join(lines) + "\n"


def parse_time_controls(value: str | None) -> set[str]:
    """Parse comma-separated exact time controls."""
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


def parse_local_datetime(value: str | None) -> datetime | None:
    """Parse a local datetime used by lichess-bot logs."""
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Analyze local lichess-bot challenge events.")
    parser.add_argument("--bot", default="ilovecatgirl", help="Bot username.")
    parser.add_argument("--logs", nargs="+", default=["lichess_bot_auto_logs/run.log"], help="Log files to parse.")
    parser.add_argument("--active-time-controls", default="60+1,90+1,120+1",
                        help="Comma-separated exact time controls considered active.")
    parser.add_argument("--since-local", help="Only include log events at or after this local ISO datetime.")
    parser.add_argument("--output", help="Optional markdown output path. Defaults to stdout.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the challenge-event analyzer."""
    args = parse_args(argv)
    summary = summarize_logs(
        [Path(path) for path in args.logs],
        args.bot,
        active_time_controls=parse_time_controls(args.active_time_controls),
        since_local=parse_local_datetime(args.since_local),
    )
    markdown = render_markdown(summary)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

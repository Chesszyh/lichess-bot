# Generic Decline Matchmaking Cadence

Date: `2026-06-09 CST`

## Summary

- Generic outgoing challenge declines now skip the full configured matchmaking cadence.
- The bot still waits for the existing one-minute API guard before creating another challenge.
- Non-generic declines, cancelled challenges, expired challenges, and completed games keep the configured cadence.
- No local engine analysis was run.

## Evidence

Recent logs showed immediate generic declines consuming the full `15` minute matchmaking cycle:

- `00:41:52` `styx_reckless` declined a `60+1` rated bullet challenge with `declineReasonKey: generic`.
- Next challenge was delayed until `00:56:52`.
- `00:56:59` `NeuroSoCute` declined a `90+1` rated bullet challenge with `declineReasonKey: generic`.
- Next challenge was delayed until `01:11:59`.

Those declines happened immediately after challenge creation, so waiting for the full post-game cadence reduced bot-vs-bot game acquisition without adding engine strength or safety.

## Verification

- Watched `test_declined_challenge__generic_decline_uses_minimum_retry_cadence` fail before implementation.
- `pytest test_bot/test_matchmaking.py::test_declined_challenge__generic_decline_uses_minimum_retry_cadence test_bot/test_matchmaking.py::test_declined_challenge__uses_configured_challenge_cadence test_bot/test_matchmaking.py::test_declined_challenge__nobot_adds_opponent_to_long_term_blocklist test_bot/test_matchmaking.py::test_declined_challenge__rated_decline_blocks_opponent_when_only_rated_is_configured test_bot/test_matchmaking.py::test_matchmaking_state__persists_outgoing_challenge_cadence_across_restart test_bot/test_matchmaking.py::test_game_done__uses_full_cadence_after_restored_partial_cadence -q` -> `6 passed`.
- `pytest test_bot/test_matchmaking.py -q` -> `45 passed`.
- `mypy --strict lib/matchmaking.py` -> passed.
- `git diff --check` -> passed.
- `ruff check --config test_bot/ruff.toml lib/matchmaking.py test_bot/test_matchmaking.py` still reports existing complexity and test-style findings.

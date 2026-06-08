# Persisted Matchmaking Cadence Cap

Date: `2026-06-09 CST`

## Summary

- Persisted post-game matchmaking cadence now stores the wall-clock start time, not only the expiry time.
- Restored post-game waits are recalculated from the current `matchmaking.challenge_timeout`, so a reduced timeout can cap stale waits after restart.
- Expired post-game waits and old expiry-only state no longer create a fresh full wait during upgrade or repeated restarts.
- No local engine analysis was run.

## Evidence

- After game `tLbp18c5` ended at `2026-06-09 01:18:05 CST`, the bot scheduled the next challenge for `01:33:05 CST`.
- The runtime config was then reduced from `matchmaking.challenge_timeout: 15` to `10`.
- After restart with `challenge_timeout: 10`, the bot still logged `Next challenge will be created after Tue Jun  9 01:33:05 2026`.
- `runtime_state/matchmaking_state.json` contained only `last_game_ended_expires_at`, so the loader had no original start timestamp to apply the shorter current timeout.

## Root Cause

The persisted post-game cadence represented the wait as an absolute expiry timestamp. That preserved the old `15` minute expiry across restarts, but it could not answer the question needed after a config reduction: how much time had already elapsed from the original post-game cadence start.

## Change

- Added `last_game_ended_started_at` to matchmaking state for non-expired post-game waits.
- Rebuild restored post-game waits from `last_game_ended_started_at + current challenge_timeout`.
- Treat old schema expiry-only post-game state as expired during upgrade, avoiding stale waits with no reliable start timestamp.
- Preserve the original start timestamp across repeated load/save cycles so restarts do not reset a partially elapsed wait.

## Verification

- Watched `test_matchmaking_state__keeps_original_start_after_restored_save` fail before the persistence fix.
- Watched `test_matchmaking_state__expired_current_schema_wait_stays_expired_after_save` fail before the persistence fix.
- `pytest test_bot/test_matchmaking.py::test_matchmaking_state__keeps_original_start_after_restored_save test_bot/test_matchmaking.py::test_matchmaking_state__expired_current_schema_wait_stays_expired_after_save -q` -> `2 passed`.
- `pytest test_bot/test_matchmaking.py -q` -> `49 passed`.
- `mypy --strict lib/matchmaking.py` -> passed.
- `pytest test_bot/test_matchmaking.py -q && mypy --strict lib/matchmaking.py && git diff --check` -> passed.
- `ruff check --config test_bot/ruff.toml lib/matchmaking.py test_bot/test_matchmaking.py` still reports existing
  `choose_opponent` complexity and historical test annotation/lambda findings.

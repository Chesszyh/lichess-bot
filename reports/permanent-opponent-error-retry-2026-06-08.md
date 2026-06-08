# Permanent Opponent Error Retry

## Scope

- Date: `2026-06-08`
- Bot: `ilovecatgirl`
- Target behavior: avoid wasting an entire matchmaking cycle on permanent opponent endpoint errors.
- Evidence source: live `lichess_bot_auto_logs/lichess-bot.log`; no local engine experiment was run.

## Evidence

At `2026-06-08 23:32:48`, matchmaking selected `PZChessBot` from the preferred high-rated bullet pool.

The challenge endpoint returned:

- `{'error': '您不能挑战 BOT PZChessBot'}`

Before the fix, this fell through to the generic decline filter path, cooled down outgoing challenge cadence, and scheduled the next challenge for `23:47:48`.

## Change

- Generalized friend-only endpoint handling to permanent opponent endpoint handling.
- Permanent opponent errors now add the opponent to the long block filter and retry the next candidate in the same matchmaking cycle.
- Added a regression test for the Chinese cannot-challenge response.
- Added `PZChessBot` to runtime/private config block lists so it remains ineligible after the temporary persisted cooldown expires.

## Commits

- Public branch: `9c66755 Retry matchmaking after permanent opponent errors`
- Private config history: `e21a204 Block permanent endpoint rejection bot`

## Verification

- RED: `test_challenge__retries_next_candidate_when_opponent_cannot_be_challenged` failed with only one challenge attempt.
- GREEN: targeted permanent-error and friend-only tests passed.
- `pytest test_bot/test_matchmaking.py -q`: `43 passed`.
- `mypy --strict lib/matchmaking.py`: no issues.
- Scoped `ruff` check passed.
- Runtime restarted safely after `/api/account/playing` returned `active_count=0`; new PID `54614`.

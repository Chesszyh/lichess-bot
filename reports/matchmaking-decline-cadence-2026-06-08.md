# Matchmaking Challenge Cadence Review for 2026-06-08

Bot: `ilovecatgirl`

## Trigger

- At 2026-06-08 21:20:48 CST, outgoing matchmaking challenged `maia3-79m_2200` for rated `120+1` bullet.
- The challenge was declined with reason key `nobot`, and the bot added `maia3-79m_2200` to the matchmaking block list.
- The next outgoing challenge was then scheduled for 2026-06-08 21:21:48 CST, only one minute later.

## Problem

The private config intent is to keep outgoing bot challenges paced by `matchmaking.challenge_timeout: 15` so declined
targets do not burn through the bot-vs-bot challenge allowance. The live behavior after a decline was using only the
hard minimum `60` second API wait.

A related challenge endpoint failure had the same one-minute retry path: at 2026-06-08 21:22:54 CST, the attempted
challenge to `Bot1nokk` hit `opponent_is_rate_limited` for the bot-vs-bot daily limit, then scheduled the next outgoing
challenge for 2026-06-08 21:23:54 CST.

## Change

- `Matchmaking.declined_challenge` now resets the outgoing cadence timer for outgoing challenge declines.
- `Matchmaking.cancelled_challenge` uses the same cadence reset for cancelled or expired outgoing challenges.
- `Matchmaking.handle_challenge_error_response` now also resets the outgoing cadence timer, so challenge endpoint
  failures such as `opponent_is_rate_limited`, generic challenge failures, and plain challenge rate-limit responses do
  not fall back to one-minute retries.
- The cadence reset applies before decline-reason filtering, so `nobot`, rated/casual, and generic outgoing declines all
  respect the configured timeout.
- Incoming challenge declines are unchanged.

## Post-Deploy Evidence

- `WOIHrVov` finished before the restart as a rated `120+1` bullet draw against `CupchessBot` with rating diff `0`.
- The bot was safely restarted only after `GET /api/account/playing` returned no active games and the game engine child
  processes had exited.
- The next outgoing challenge was scheduled for 2026-06-08 21:42:28 CST, 15 minutes after the local game-done event.
- A later clean startup with no active game scheduled the next outgoing challenge for 2026-06-08 21:46:08 CST, again
  matching `matchmaking.challenge_timeout: 15`.
- After the endpoint-failure cadence fix was committed, the bot was safely restarted again at 2026-06-08 21:41 CST with
  `GET /api/account/playing` returning no active games. The new process scheduled its next outgoing challenge for
  2026-06-08 21:56:05 CST, preserving the 15-minute cadence under the updated code.

## Permanent Opponent Errors

- At 2026-06-08 23:32:41 CST, outgoing matchmaking triggered on schedule and selected `PZChessBot`.
- Lichess rejected the challenge with `{'error': '您不能挑战 BOT PZChessBot'}`.
- The running process did not retry another candidate in that same cycle, which indicated it had not loaded the later
  permanent-opponent retry fix.
- The current branch head includes `9c66755 Retry matchmaking after permanent opponent errors`, which classifies
  "cannot challenge bot" endpoint responses as permanent opponent errors, blocks that opponent, and retries another
  candidate in the same matchmaking cycle.
- Before restart, `/api/account/playing` returned `ongoing_games 0`.
- The bot was safely restarted at 2026-06-08 23:35 CST to load the current matchmaking code. The new process is PID
  `54614` and scheduled the next outgoing challenge for 2026-06-08 23:47:48 CST, preserving the existing cadence.

Verification for the current code:

- `pytest test_bot/test_matchmaking.py::test_challenge__retries_next_candidate_when_opponent_cannot_be_challenged test_bot/test_matchmaking.py::test_challenge__retries_next_candidate_when_opponent_requires_friendship test_bot/test_matchmaking.py::test_challenge__retries_next_candidate_when_opponent_is_rate_limited -q`: `3 passed`

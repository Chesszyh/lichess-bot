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

## Change

- `Matchmaking.declined_challenge` now resets the outgoing cadence timer for outgoing challenge declines.
- `Matchmaking.cancelled_challenge` uses the same cadence reset for cancelled or expired outgoing challenges.
- The cadence reset applies before decline-reason filtering, so `nobot`, rated/casual, and generic outgoing declines all
  respect the configured timeout.
- Incoming challenge declines are unchanged.

## Post-Deploy Evidence

- The bot was safely restarted only after `GET /api/account/playing` returned no active games.
- After the restart, `WOIHrVov` finished as a rated `120+1` bullet draw against `CupchessBot` with rating diff `0`.
- The next outgoing challenge was scheduled for 2026-06-08 21:42:28 CST, 15 minutes after the local game-done event.
- A later clean startup with no active game scheduled the next outgoing challenge for 2026-06-08 21:46:08 CST, again
  matching `matchmaking.challenge_timeout: 15`.

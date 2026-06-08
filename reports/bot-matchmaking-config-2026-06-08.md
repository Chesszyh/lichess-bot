# Bot Matchmaking Config Update for 2026-06-08

Bot: `ilovecatgirl`

This report records the private `config.yml` strategy change without committing the secret-bearing config file.

## Goal

Increase useful bot-vs-bot bullet/blitz samples while avoiding Lichess outgoing challenge rate limits.

## Private Config Changes

Recorded in local config history:

- `.config-history` commit `a1ca86b`: accept increment bullet bot games.
- `.config-history` commit `6766e56`: throttle outgoing bot challenges safely.

Effective private config intent:

- Incoming challenge queue now prefers bot challengers with `challenge.preference: bot`.
- Incoming challenges accept `bullet`, `blitz`, and `rapid`.
- Bullet challenges must still have increment because `min_increment: 1` and `bullet_requires_increment: true`.
- Incoming base time lower bound is `60` seconds, allowing practical `1+1` and longer bullet.
- Outgoing matchmaking can choose `60`, `90`, `180`, `240`, or `300` second base times with increments from `1`, `2`, or `3`.
- Outgoing challenge cadence is throttled to `challenge_timeout: 15`, so proactive challenges should not burn through the bot-vs-bot daily quota quickly.
- Existing Lichess rate-limit handling remains in place: structured 429 timeout handling, exponential fallback for plain "too many requests", target cooldowns, and persistent matchmaking state.

## Why This Is Safer

The previous live config had `challenge_timeout: 1`, which validates but triggers the repository warning about potentially using the 100 bot-vs-bot games/day allowance quickly. The revised config encourages more games through broader incoming acceptance and better time-control coverage, without increasing outgoing challenge frequency.

The running bot process has not been restarted. These private config changes will take effect only after a later safe restart when no game is active.

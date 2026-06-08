# Bot Matchmaking Config Update for 2026-06-08

Bot: `ilovecatgirl`

This report records the private `config.yml` strategy change without committing the secret-bearing config file.

## Goal

Increase useful bot-vs-bot bullet/blitz samples while avoiding Lichess outgoing challenge rate limits.

## Private Config Changes

Recorded in local config history:

- `.config-history` commit `a1ca86b`: accept increment bullet bot games.
- `.config-history` commit `6766e56`: throttle outgoing bot challenges safely.
- `.config-history` commit `a0ff1a0`: prefer `3000+` outgoing bot opponents when available.
- `.config-history` commit `67e850e`: bias outgoing bot matchmaking toward bullet time controls.
- `.config-history` commit `40bbf63`: disable the fast bot opening book when playing Black.
- `.config-history` commit `7dfb401`: increase outgoing bullet matchmaking sample weight.
- `.config-history` commit `7d5cf39`: avoid weak long blitz bot controls.
- `.config-history` commit `afd8dba`: bias outgoing bullet matchmaking toward short controls.
- `.config-history` commit `a01b8e5`: favor longer bullet controls after short-clock lc0 losses.
- `.config-history` commit `7172e73`: restrict incoming fast-game increments to the active `+1` sample.
- `.config-history` commit `575c002`: restrict fast games to rated mode.
- `.config-history` commit `c626322`: limit arena base time to active controls.
- `.config-history` commit `47a1379`: block `MEGA-NOOB-BOT` active controls.
- `.config-history` commit `287090c`: increase short bullet matchmaking weights.
- `.config-history` commit `f1051ef`: block `abcd_engine` active-control leak.
- `.config-history` commit `6db5b41`: increase the shortest outgoing increment-bullet samples without changing outgoing cadence.

Effective private config intent:

- Incoming challenge queue now prefers bot challengers with `challenge.preference: bot`.
- Incoming challenges and arena entries are restricted to rated games.
- Incoming challenges accept rated `bullet` and short `blitz` only at `+1`; `rapid` is listed but excluded by the
  `120` second base cap and `+1` increment cap.
- Bullet challenges must still have increment because `min_increment: 1` and `bullet_requires_increment: true`.
- Incoming base time is capped to `60` through `120` seconds, allowing practical `1+1`, `1.5+1`, and `2+1` fast games.
- Arena selection now uses the same `120` second base cap and avoids `+2/+3` arenas, keeping arena pairings aligned with
  the active `+1` evidence window.
- Outgoing matchmaking can choose `60`, `90`, or `120` second base times, always with `1` second increment.
- Outgoing matchmaking is still fully increment bullet. The active-control weights are now `60+1` at `5/18`, `90+1` at
  `7/18`, and `120+1` at `6/18`, increasing short active-control sampling without reintroducing abandoned blitz controls
  or changing the Lichess challenge cadence.
- Outgoing challenge cadence is throttled to `challenge_timeout: 15`, so proactive challenges should not burn through the bot-vs-bot daily quota quickly.
- Outgoing matchmaking now prefers opponents rated at least `3000` when the ready pool has them, falling back to the broader pool otherwise. This avoids spending too many samples on sub-3000 draws while keeping the bot from getting stuck when the high pool is empty.
- `MEGA-NOOB-BOT` is blocked for both incoming challenges and outgoing matchmaking after two active-control losses,
  including the 2026-06-08 `90+1` high-clock normal loss.
- `abcd_engine` is blocked for both incoming challenges and outgoing matchmaking after active-control W-D-L `0-3-1`,
  net `-10`, including the 2026-06-08 `60+1` time-forfeit loss while `ilovecatgirl` was the higher-rated bot. This is a
  narrow opponent block, not a global removal of `60+1`, because the active-only `60+1` White pool remains strongly
  rating-positive.
- Fast bot games now leave the local opening book immediately as Black in bullet and blitz, while preserving the bot-specific fast-book cap for White. This targets the observed Black-side Najdorf loss cluster without weakening human-game book behavior.
- Endgame tablebase move sources are enabled for fast games: local 5-piece Syzygy is used directly by lichess-bot, and
  online EGTB is enabled up to `180` base seconds and `8` pieces when the bot has at least `10` seconds left. This targets
  technical bullet/blitz endgames without adding local engine load. This took effect after a safe restart at 2026-06-08
  19:03 CST.
- The private config file now caps incoming bot games and arena selection at `120` base seconds, and outgoing bot
  matchmaking samples `60+1`, `90+1`, and `120+1`.
  The incoming cap took effect after a safe restart at 2026-06-08 18:53 CST, after game `ZiJe1OaC` had ended and all game
  engine processes had exited; later outgoing bullet weighting revisions kept the same safe-restart discipline.
- Existing Lichess rate-limit handling remains in place: structured 429 timeout handling, exponential fallback for plain "too many requests", target cooldowns, and persistent matchmaking state.

## Time Forfeit Evidence

The refreshed bot-game report now tracks loss terminations. Across `2354` fast bot-vs-bot games, `132` losses were by `Time forfeit`, with historical clusters concentrated in no-increment blitz, especially `180+0` (`49` losses split across both colors). The current private config already mitigates that cluster by requiring incoming bot games to have exactly `1` second increment and by issuing outgoing challenges only with `+1` increment.

## Speed Split Evidence

The refreshed bot-game report now splits results by Lichess speed bucket and exact time control. Historical bullet bot games show `242` wins, `269` draws, and `80` losses, while blitz shows `205` wins, `1128` draws, and `386` losses. This supports keeping the outgoing matchmaking bias toward increment bullet while collecting more direct `60+1` and `60+2` evidence for lc0's short-clock behavior.

## Exact Clock Evidence

The exact-clock score table shows `180+0 black` at `24.7%` and `180+0 white` at `31.5%`, the two weakest scored controls with at least ten games. The contextual loss-prefix table also keeps the Najdorf English Attack separated by color, speed, and termination, showing that the largest non-clock opening leak remains Black blitz Najdorf positions. This reinforces the current no-`+0` private matchmaking policy and the Black fast-bot book disable while collecting cleaner increment-only samples.

The earlier outgoing controls included `180` and `240` second bases. Historical score rates for those controls were weak for
Black at `180+1` (`39.9%`), `180+2` (`37.6%`), `240+1` (`44.7%`), and `240+2` (`38.3%`). The current config removes long
blitz bases while keeping proactive matchmaking fully in increment bullet controls.

The latest `60+2` bullet loss to `Cheszter` was not a clock-loss pattern: the bot still had `87` seconds when mated. Local
Syzygy probing showed the 4-piece phase was already lost, while the log showed all late moves came from `Source: Engine`
instead of lichess-bot EGTB. Enabling direct local Syzygy and online EGTB gives exact move sources in future fast technical
endgames before the capped search has to solve them unaided.

The rated-only report still shows active-envelope `+2` losses and rating drag: `120+2 black` is `-17` over `16` rated
games, while focused active controls include `120+2` blitz losses and `60+2`/`90+2` bullet losses. Because outgoing
matchmaking already uses only `+1`, incoming challenges and arena selection were narrowed to `+1` to collect cleaner
`60+1`, `90+1`, and `120+1` evidence before reopening higher increments.

The analyzer now also lists high-clock normal losses separately. These are non-time-forfeit losses where the bot still had
at least `60` seconds after its last recorded move, so they should be reviewed as chess-strength, opening, or conversion
problems rather than time-management failures.

## Why This Is Safer

The previous live config had `challenge_timeout: 1`, which validates but triggers the repository warning about potentially using the 100 bot-vs-bot games/day allowance quickly. The revised config encourages more games through broader incoming acceptance and better time-control coverage, without increasing outgoing challenge frequency.

The `57/60` bullet weighting took effect after safe restarts at 2026-06-08 18:32 CST and 18:53 CST, when no game engine
child process was active. The `60/60` outgoing bullet weighting took effect after a safe restart at 2026-06-08 18:56 CST.
The short-bullet weighting took effect after a safe restart at 2026-06-08 19:11 CST; `/api/account/playing` returned an
empty active-game payload and the next outgoing challenge was scheduled for 2026-06-08 19:26:21 CST.
The longer-bullet weighting was configured at 2026-06-08 after the post-19:11 active-control losses showed short-clock
lc0 risk; it keeps the outgoing challenge cadence at `15` minutes to avoid increasing Lichess active challenge pressure.

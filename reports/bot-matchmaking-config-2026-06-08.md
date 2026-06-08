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

Effective private config intent:

- Incoming challenge queue now prefers bot challengers with `challenge.preference: bot`.
- Incoming challenges accept practical increment `bullet` and short `blitz`; `rapid` is listed but excluded by the `120` second base cap.
- Bullet challenges must still have increment because `min_increment: 1` and `bullet_requires_increment: true`.
- Incoming base time is capped to `60` through `120` seconds, allowing practical `1+1` through `2+2` fast games.
- Outgoing matchmaking can choose `60` or `90` second base times with `1` or `2` second increments.
- Outgoing matchmaking now weights `90` second bases and `1` second increments more heavily. This raises the
  configured bullet share from `57/60` possible base/increment combinations to `60/60`, while keeping increment bullet
  samples such as `60+2` and `90+2` in the pool.
- Outgoing challenge cadence is throttled to `challenge_timeout: 15`, so proactive challenges should not burn through the bot-vs-bot daily quota quickly.
- Outgoing matchmaking now prefers opponents rated at least `3000` when the ready pool has them, falling back to the broader pool otherwise. This avoids spending too many samples on sub-3000 draws while keeping the bot from getting stuck when the high pool is empty.
- Fast bot games now leave the local opening book immediately as Black in bullet and blitz, while preserving the bot-specific fast-book cap for White. This targets the observed Black-side Najdorf loss cluster without weakening human-game book behavior.
- Endgame tablebase move sources are enabled for fast games: local 5-piece Syzygy is used directly by lichess-bot, and
  online EGTB is enabled up to `180` base seconds and `8` pieces when the bot has at least `10` seconds left. This targets
  technical bullet/blitz endgames without adding local engine load. This took effect after a safe restart at 2026-06-08
  19:03 CST.
- The private config file now caps incoming bot games at `120` base seconds and outgoing bot games at `90` base seconds.
  The incoming cap took effect after a safe restart at 2026-06-08 18:53 CST, after game `ZiJe1OaC` had ended and all game
  engine processes had exited; the outgoing `90` second cap took effect after a safe restart at 2026-06-08 18:56 CST.
- Existing Lichess rate-limit handling remains in place: structured 429 timeout handling, exponential fallback for plain "too many requests", target cooldowns, and persistent matchmaking state.

## Time Forfeit Evidence

The refreshed bot-game report now tracks loss terminations. Across `2354` fast bot-vs-bot games, `132` losses were by `Time forfeit`, with historical clusters concentrated in no-increment blitz, especially `180+0` (`49` losses split across both colors). The current private config already mitigates that cluster by requiring incoming bot games to have at least `1` second increment and by issuing outgoing challenges only with `+1` or `+2` increments.

## Speed Split Evidence

The refreshed bot-game report now splits results by Lichess speed bucket and exact time control. Historical bullet bot games show `242` wins, `269` draws, and `79` losses, while blitz shows `205` wins, `1128` draws, and `386` losses. This supports keeping the outgoing matchmaking bias toward increment bullet while treating blitz as the weaker pool to diagnose rather than increasing blitz volume.

## Exact Clock Evidence

The exact-clock score table shows `180+0 black` at `24.7%` and `180+0 white` at `31.5%`, the two weakest scored controls with at least ten games. The contextual loss-prefix table also keeps the Najdorf English Attack separated by color, speed, and termination, showing that the largest non-clock opening leak remains Black blitz Najdorf positions. This reinforces the current no-`+0` private matchmaking policy and the Black fast-bot book disable while collecting cleaner increment-only samples.

The earlier outgoing controls included `180` and `240` second bases. Historical score rates for those controls were weak for
Black at `180+1` (`39.9%`), `180+2` (`37.6%`), `240+1` (`44.7%`), and `240+2` (`38.3%`). The current config removes long
blitz bases and then removes the remaining outgoing `120` second base, keeping proactive matchmaking fully in increment
bullet controls.

The latest `60+2` bullet loss to `Cheszter` was not a clock-loss pattern: the bot still had `87` seconds when mated. Local
Syzygy probing showed the 4-piece phase was already lost, while the log showed all late moves came from `Source: Engine`
instead of lichess-bot EGTB. Enabling direct local Syzygy and online EGTB gives exact move sources in future fast technical
endgames before the capped search has to solve them unaided.

## Why This Is Safer

The previous live config had `challenge_timeout: 1`, which validates but triggers the repository warning about potentially using the 100 bot-vs-bot games/day allowance quickly. The revised config encourages more games through broader incoming acceptance and better time-control coverage, without increasing outgoing challenge frequency.

The `57/60` bullet weighting took effect after safe restarts at 2026-06-08 18:32 CST and 18:53 CST, when no game engine
child process was active. The new `60/60` outgoing bullet weighting took effect after a safe restart at 2026-06-08
18:56 CST.

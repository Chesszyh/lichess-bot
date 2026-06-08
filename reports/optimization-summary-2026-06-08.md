# Lc0 Bullet/Blitz Optimization Summary for 2026-06-08

Bot: `ilovecatgirl`
Target: stabilize both `bullet` and `blitz` around `3080` on local Mac mini `10c/16G`, using Lc0 as the main engine and Stockfish only as helper where useful.

## Current Verified State

- Latest account API check: `bullet 3026` over `2382` games, `prog -29`; `blitz 2946` over `1989` games, `prog -1`.
- The target is not achieved yet. Bullet remains below `3080`, and blitz is materially below target.
- Latest `/api/account/playing` check before this summary returned `0` ongoing games.
- No heavy local engine experiment was run while the live bot was active.
- Latest local active-control PGN remains `game_records/ilovecatgirl vs abdcebot - Zd5yy2Mj.pgn`, a rated `90+1` bullet draw against a `3144` bot for `+2`.

## Evidence Baseline

The main active-control report is `reports/bot-game-analysis-active-controls-2026-06-08.md`.

- Scope: rated `60+1`, `90+1`, and `120+1` bot games only.
- Games analyzed: `262`.
- Results: `109` wins, `122` draws, `21` losses, `10` unknown.
- Rating impact: `+217` over `219` games with rating diffs.
- Exact active controls remain rating-positive:
  - `60+1`: `+99` over `94` rated-diff games.
  - `90+1`: `+27` over `45` rated-diff games.
  - `120+1`: `+91` over `80` rated-diff games.
- Historical risk gate still fails because old leak clusters remain in the local PGN pool.

The focused loss/lower-rated-draw report is `reports/loss-and-low-draw-analysis-2026-06-08.md`.

- It scans all local PGNs for all bot losses and draws against substantially lower-rated opponents.
- The largest all-history lower-rated draw theme is still sharp Sicilian/Najdorf handling.
- In the current active-control envelope, the strongest actionable leaks are opponent-specific rather than a broad time-control failure.

## Optimization Attempts

### Matchmaking Scope

- Restricted bot-vs-bot fast games to rated games.
- Restricted incoming/outgoing active controls to increment bullet: `60+1`, `90+1`, and `120+1`.
- Removed no-increment fast games from the active envelope after historical time-forfeit clusters, especially weak `180+0` blitz results.
- Avoided broad long-blitz arena exposure because historical long-blitz bot games showed both loss and draw-leak rating drag.
- Kept outgoing `challenge_timeout` at `15` minutes to avoid triggering Lichess active challenge pressure.
- Preserved matchmaking cadence across restarts so safe restarts do not accidentally spam immediate outgoing challenges.
- Reset full matchmaking cadence after completed games so the bot can seek another opponent without waiting out stale decline-only state.

### Opponent Selection

- Outgoing matchmaking now prefers ready bots rated at least `3000` when available, with fallback to the broader eligible pool.
- Blocked high-risk active-control leak opponents in both incoming and outgoing paths:
  - `MEGA-NOOB-BOT`
  - `abcd_engine`
  - `Fischer_Bot`
  - `duchessAI`
  - `MDBOT`
  - `ToromBot`
  - `BorkaTower`
  - `Valhalla-Bot`
  - `grail-bot`
  - `abhisun_bot`
  - `RockingSuperstars`
  - `PZChessBot`
- Kept older local matchmaking blocks in place where already configured:
  - `maello_bot`
  - `PatriciaBot`
  - `Xewali`
- Incoming challenge acceptance remains narrow:
  - rated only
  - standard only
  - base `60-120`
  - increment exactly `+1`
  - bullet requires increment
  - challenger rating `2500-4000`
  - concurrency `1`
  - max simultaneous games per user `1`
  - `Chesszyh` always allowed

### Challenge Endpoint Robustness

- Added retry-on-opponent-rate-limit handling for Lichess responses where the selected opponent already reached the bot-vs-bot daily limit.
- Added retry-on-friend-only handling so one unavailable target does not consume the whole matchmaking cycle.
- Generalized permanent opponent endpoint errors, including the Chinese `您不能挑战 BOT ...` response, into same-cycle retry behavior.
- Added persistent cooldown/block behavior for endpoint failures so repeated bad targets do not reappear immediately.
- Documented these in:
  - `reports/opponent-rate-limit-retry-2026-06-08.md`
  - `reports/permanent-opponent-error-retry-2026-06-08.md`
  - `reports/matchmaking-decline-cadence-2026-06-08.md`

### Time Management

- Added exact bullet clock-pressure movetime support.
- Private bullet config enables the rule when:
  - own clock is at least `30000` ms
  - opponent clock is at most `10000` ms
  - game has reached at least ply `20`
  - exact movetime becomes `6000` ms
- This targets the observed pattern where Lc0 moved too casually while clock-rich and then lost despite the opponent having only a few seconds left.
- The latest `abdcebot` draw was not a trigger case because the opponent never became low enough on clock.
- No live `Using exact clock-pressure movetime` log line has been observed yet.

### Opening/Move Source Adjustments

- Fast bot games leave the local opening book immediately as Black in bullet/blitz, while preserving the bot-specific fast-book cap for White.
- This targets the historical Black-side Najdorf/Sicilian loss cluster without changing human-game book behavior.
- Local Syzygy and online EGTB support were enabled for fast technical endgames to reduce avoidable Lc0-only endgame failures under bullet constraints.

### Reporting and Analysis Tooling

- Added/extended PGN analysis filters by:
  - game mode
  - speed bucket
  - exact time control
  - focused active controls
  - lower-rated draw clusters
  - rating-negative draw clusters
  - opponent leak watchlist with recency
  - high-clock normal losses
  - clock-pressure misses
  - abandoned/unknown result contexts
- Added challenge-event analysis for incoming challenge decisions and active-envelope filtering.
- Refresh reports were kept lightweight and PGN/log based; no large engine analysis was run against the live bot's resources.

## Test and Verification Results

Code-level verification performed during this optimization round included:

- `pytest test_bot/test_matchmaking.py -q`: `43 passed` after permanent opponent retry work.
- Targeted matchmaking retry tests passed:
  - opponent cannot be challenged
  - opponent requires friendship
  - opponent is rate limited
- `mypy --strict lib/matchmaking.py`: no issues after endpoint retry work.
- Scoped `ruff` checks passed for the edited matchmaking code.
- Targeted time-management tests for bullet clock-pressure movetime passed when the feature was added.
- The active-control analyzer still exits nonzero for the configured risk gate because historical risk clusters remain; this is expected and the report is still written.

Runtime/deployment verification:

- Safe restarts were performed only after `/api/account/playing` reported no active games.
- The bot reconnected cleanly and resumed awaiting challenges after deployment restarts.
- The permanent opponent retry fix was deployed after the observed `PZChessBot` endpoint failure; the pre-fix runtime showed the old behavior, so the next permanent-error live sample should be watched to confirm same-cycle retry in production.

## Current Conclusions

- The current active increment-bullet envelope is rating-positive, so there is no evidence to remove `60+1`, `90+1`, or `120+1` broadly.
- The strongest confirmed leaks are narrow opponent clusters and specific chess-pattern clusters, not one global bullet time-control failure.
- Short bullet weighting is still delicate. Increasing bullet exposure is useful for sample collection, but too-short search behavior can lose clock-rich positions if the bot does not spend enough time near opponent flag pressure.
- Blitz is still the weaker target area. Historical no-increment and long-blitz controls were poor, so blitz should be reintroduced only through narrow evidence-backed controls, not broad arenas.

## Next Optimization Directions

1. Watch for fresh post-change losses or rating-negative draws against non-blocked opponents in `60+1`, `90+1`, and `120+1`.
2. Confirm live `clock_pressure` behavior with an actual log line before changing thresholds again.
3. If clock-rich normal losses continue, compare the final 10-15 bot moves and decide whether the `6000` ms exact movetime should trigger earlier or use a larger opponent-clock threshold.
4. Build a small offline Stockfish-assisted reviewer for selected PGNs only, scheduled when the bot is idle, to classify whether losses are opening exits, tactical misses, endgame conversion, or time policy failures.
5. Add a post-game lightweight tagger that appends local report metadata for:
   - result and rating diff
   - final clock spread
   - opponent rating bucket
   - whether the clock-pressure rule triggered
   - whether the game was against a blocked/watch opponent
6. For blitz, test only narrow `+1` controls after bullet stabilizes; avoid restoring `180+0`, broad `180+2`, `240+1`, or `240+2` until there is fresh contrary evidence.
7. Keep the block list under review. Historical April-only leaks should not cause permanent avoidance if fresh post-change games show the bot can score well.
8. Continue direct commit/push discipline for code and public reports, and mirror private `config.yml` changes in `.config-history`.

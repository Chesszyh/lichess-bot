# Bot Optimization History And Configuration Notes

This document summarizes the issues found while operating this fork and the improvements requested since the initial Stockfish deployment. Use it as a reference when deploying a second bot, enabling fork-specific features, or tuning a new machine.

## 2026-06-08 Lc0 Bullet/Blitz Optimization Round

Current optimization target: keep the Mac mini 10c/16G bot improving toward stable `3080` bullet and blitz ratings, using Lc0 as the main engine and Stockfish as an optional helper. Changes in this round prioritize public bot-vs-bot evidence. Avoid heavy local engine experiments while the bot is running, and never restart the process during an active game.

Current public ratings at the end of this round:

- Bullet: `3024`
- Blitz: `2946`

### Evidence Used

The main active-control report is `reports/bot-game-analysis-active-controls-2026-06-08.md`. It analyzed `261` rated active-control games across `60+1`, `90+1`, and `120+1`.

Key risk signals:

- `duchessAI | bullet | 60+1`: risk `10`, driven by lower-rated and rating-negative draws.
- `MDBOT | bullet | 60+1`: risk `9`, driven by repeated losses.
- `Fischer_Bot | bullet | 120+1`: risk `6`, with a fresh loss where the bot still had about `80s` while the opponent had about `7s`.
- `ToromBot | bullet | 90+1`: risk `6`, including clock-pressure miss evidence.
- Opening loss clusters include Najdorf English Attack, London systems, Nimzo-Indian Classical structures, Semi-Slav Anti-Moscow, and some Caro-Kann contexts.

Challenge-event evidence is tracked in `reports/challenge-event-analysis-since-2026-06-08-2224.md`. Under the current incoming challenge policy, the only observed incoming challenge in that window was `BlueMoonBot | bullet | 60+0`, declined for `timecontrol`.

### Matchmaking Changes

The bot was encouraged to find more bot-vs-bot games while staying below Lichess challenge rate limits.

Implemented behavior:

- Prefer opponents rated at least `3000` when the pool has suitable candidates.
- Keep rated standard active controls as the main public evaluation set.
- Retry the next candidate when Lichess reports the opponent is at the daily bot-vs-bot rate limit, instead of wasting the whole matchmaking cycle.
- Persist and document opponent rate-limit retry behavior.

Relevant commits:

- `645dc6c Retry matchmaking after opponent rate limits`
- `6501b2f Retry next bot after opponent daily limit`
- `dc954bb Document opponent rate limit retry`

Observed runtime evidence before the retry fix was loaded:

- Matchmaking found `308` online bots.
- `62` matched the configured filters.
- `20` were preferred `3000+` candidates.
- The selected opponent was daily-limited by Lichess (`opponent_is_rate_limited: True`).

After restart, the retry fix was loaded and the next challenge cadence continued normally.

### Current Challenge Policy

Incoming challenge policy is intentionally strict:

- Accept rated games only.
- Accept standard chess only.
- Accept base time from `60` to `120` seconds.
- Require increment exactly `+1`.
- Require increment for bullet; do not accept `1+0`.
- Opponent rating range: `2500-4000`.
- `concurrency: 1`.
- Maximum simultaneous games per user: `1`.
- Always allow `Chesszyh`.

Current challenge block list:

- `MEGA-NOOB-BOT`
- `abcd_engine`
- `Fischer_Bot`

Current matchmaking block list also includes:

- `maello_bot`
- `PatriciaBot`
- `Xewali`
- `MEGA-NOOB-BOT`
- `abcd_engine`
- `Fischer_Bot`

### Opponent Blocking Decisions

Blocking should be conservative and evidence-driven. In this round:

- `MEGA-NOOB-BOT` remained blocked after active-control losses.
- `abcd_engine` was blocked after an active-control leak.
- `Fischer_Bot` was blocked after a fresh `120+1` bullet loss where the bot had a large remaining-clock advantage but still lost normally.

Watch, but do not block without fresher evidence:

- `duchessAI`: repeated lower-rated and rating-negative draws.
- `MDBOT`: repeated historical `60+1` losses.
- `ToromBot`: historical `90+1` losses and clock-pressure misses.
- `Valhalla-Bot`: lower-rated/rating-negative draw risk.
- `grail-bot`, `abhisun_bot`, `RockingSuperstars`: historical rating-negative loss signals.

### Bullet Time-Use Changes

Earlier bullet tuning relaxed overly tight Lc0 caps:

- High/max bullet clock cap increased from `5s` to `12s`.
- Shallow-search guard was made less permissive:
  - `min_depth: 6`
  - `extra_movetime_ms: 1500`
  - `min_clock_ms: 30000`
  - `min_ply: 10`

Fresh evidence then showed a different failure mode: the bot could still move too quickly when the opponent was almost out of time. The clearest example was `Fischer_Bot vs ilovecatgirl - sSos0k3i.pgn`: the bot lost a `120+1` bullet game while keeping a very large clock reserve.

The new `clock_pressure_*` rule forces exact movetime when the bot is clock-rich and the opponent is low:

```yaml
engine:
  bullet_time_management:
    clock_pressure_own_clock_threshold_ms: 30000
    clock_pressure_opponent_clock_threshold_ms: 10000
    clock_pressure_min_ply: 20
    clock_pressure_movetime_ms: 6000
```

Runtime intent:

- If the bot has at least `30s`,
- and the opponent has at most `10s`,
- and at least `20` plies have been played,
- use exact `movetime 6000` for the current search.

This avoids letting Lc0 self-manage into a near-instant move in positions where spending a few seconds can prevent a tactical loss and still leaves enough clock to finish.

Relevant commit:

- `b6249cc Add bullet clock-pressure movetime cap`

Private config mirror:

- `.config-history` commit `aaf098e Enable bullet clock-pressure movetime`

### Verification Results

Commands run during this round:

```bash
pytest test_bot/test_matchmaking.py -q
pytest test_bot/test_engine_time_management.py test_bot/test_config.py -q
pytest test_bot/test_analyze_bot_games.py -q
pytest test_bot/test_analyze_challenge_events.py test_bot/test_analyze_bot_games.py -q
python -m py_compile lib/engine_wrapper.py lib/config.py test_bot/test_engine_time_management.py
git diff --check
```

Observed results:

- `test_bot/test_matchmaking.py`: `39 passed`.
- `test_bot/test_engine_time_management.py test_bot/test_config.py`: `44 passed`.
- Analyzer tests passed.
- `py_compile` passed for the touched time-management/config/test files.
- `git diff --check` passed.

Known verification caveats:

- Full `ruff` on some touched modules still reports pre-existing issues, including a historical long line in `lib/config.py` and complexity warnings.
- Full strict `mypy` on these modules still reports pre-existing type issues in wrappers and tests.
- These existing issues were not fixed in this round to keep the optimization changes scoped.

### Current Runtime State After This Round

The bot was restarted only after `/api/account/playing` returned `ongoing_games 0`.

Healthy restart evidence:

- Launchd state: running.
- New process started successfully.
- Logs showed:
  - `Engine configuration OK`
  - `Welcome ilovecatgirl!`
  - `You're now connected to https://lichess.org/ and awaiting challenges.`

No clock-pressure PGN had landed yet at the time this note was written. The next evidence to inspect is whether logs contain:

```text
Using exact clock-pressure movetime
```

and whether the corresponding PGNs reduce the "bot kept a large time reserve while opponent was nearly flagged, then lost normally" pattern.

### Next Optimization Directions

1. Observe clock-pressure games.
   - If `6000ms` causes self-inflicted time pressure, reduce it to `4000-5000ms`.
   - If tactical misses continue while the bot remains clock-rich, increase it toward `7000-8000ms`.

2. Reduce lower-rated draw leakage.
   - Focus first on `duchessAI` and `Valhalla-Bot`.
   - Consider blocking repeat offenders or changing draw/position-simplification behavior against lower-rated bots.

3. Decide whether to block `MDBOT` or `ToromBot`.
   - Historical risk is high.
   - Prefer fresh active-control evidence before adding permanent blocks.

4. Tune opening policy by bot-vs-bot loss context.
   - Reduce or avoid weak bullet branches in Nimzo-Indian Classical structures, black London systems, Semi-Slav Anti-Moscow, and poor Caro-Kann contexts.
   - Prefer lightweight book-policy changes over local engine-heavy experiments while the bot is running.

5. Split blitz analysis from bullet analysis.
   - Blitz is farther from target than bullet.
   - Collect enough blitz bot-vs-bot games before changing blitz caps again.

6. Improve report automation.
   - Automatically highlight fresh losses, lower-rated rating-negative draws, and clock-pressure misses.
   - Emit concrete block/watch/config suggestions so future tuning turns start from evidence instead of manual scanning.

## Deployment Baseline

The first deployment used a locally compiled Stockfish engine with opening books and Syzygy files. Later experiments switched this Mac mini to Lc0 with the Metal backend and a BT4 network, while the lower-power ThinkPad was identified as a better Stockfish target.

Do not run the same Lichess bot account on two machines. Use a separate bot account, token, runtime directory, config, and logs for each machine.

## Configuration Versioning

The main repository ignores `config.yml` because it may contain tokens and machine-specific paths. Local config changes should still be tracked privately:

```bash
cp config.yml .config-history/config.yml
git -C .config-history add config.yml
git -C .config-history commit -m "Describe the config change"
```

Make a private config commit every time `config.yml` changes. Use specific messages such as `Tighten Lc0 fast-game movetime caps` or `Switch local bot to Lc0 Metal`.

## Challenge And Matchmaking Policy

The bot evolved from accepting only bot challenges to accepting both bots and humans. Current policy goals:

- Always allow the administrator account `Chesszyh`.
- Accept high-rated humans and bots while avoiding low-signal games.
- Support both rated and casual games when game volume is too low.
- Prefer fast games with base time at or below 5 minutes and increment at or below 3 seconds.
- Use cooldowns and rejection tracking to avoid repeated challenges and Lichess `429` rate limits.
- Block or cool down bots that repeatedly reject challenges.

For sparse pools, lower the active opponent floor gradually, for example from `2700+` to `2600+` or `2500+`, instead of sending challenges too aggressively.

## Opening Strategy

Opening handling should depend on opponent type:

- Against bots: use the strongest deterministic book line available. Random weak openings caused several bot-vs-bot losses from early strategic disadvantage.
- Against humans: allow more random book selection to make games interesting and less repetitive. Quality variance is acceptable here.

The specific problem observed was a repeated black repertoire against `1.d4`, often entering the same Nimzo-Indian structure. Human-facing configs should use broader books and random selection; bot-facing configs should use `best_move` or equivalent deterministic selection.

## Time Management

Time management was the most important operational issue.

Observed failures:

- In bullet, the bot sometimes spent too long in obvious positions and flagged.
- In blitz, the bot sometimes moved too quickly in critical positions and lost by shallow tactical oversight.
- In other blitz games, especially with Lc0, the engine spent 10-30 seconds per move despite plenty of game still remaining, then later flagged.
- At very low time, the bot still moved too slowly compared with human premove-like play.

Stockfish responds well to reduced clock values. Lc0 with a large network does not; it needs exact `movetime` caps. This fork adds `force_movetime_caps` under `engine.bullet_time_management`. For Lc0 fast games, enable it and cap every blitz/bullet move with a large `high_clock_threshold_ms`.

Example Lc0-oriented policy:

```yaml
engine:
  bullet_time_management:
    enabled: true
    speeds: [bullet, blitz]
    force_movetime_caps: true
    max_clock_ms: 8000
    high_clock_threshold_ms: 600000
    high_clock_ms: 5000
    low_clock_threshold_ms: 20000
    low_clock_ms: 2200
    critical_clock_threshold_ms: 8000
    critical_clock_ms: 700
    emergency_clock_threshold_ms: 2500
    emergency_clock_ms: 100
```

For Stockfish, use softer caps and allow deeper thinking when the clock is safe. Watch losses where the bot has much more time than the opponent but still misses tactics; that usually means caps are too tight.

## Event Stream And Connectivity

Several failures looked like network issues but were actually control-flow or stream problems:

- Bot online but not reacting to incoming challenges.
- Game event stream stopped receiving moves.
- Bot appeared to leave a game and lost by timeout.
- Startup failed during token validation when proxy/TLS routing was broken.

Healthy startup log lines are:

- `Engine configuration OK`
- `Welcome <bot username>!`
- `You're now connected to https://lichess.org/ and awaiting challenges.`

Before blaming engine strength, inspect `lichess_bot_auto_logs/run.log` for stream disconnects, token validation failures, `429` responses, and long gaps after opponent moves. Restart only after confirming `nowPlaying` is empty.

## Admin And Chat Controls

The administrator account `Chesszyh` should always be allowed to challenge the bot, regardless of rating filters. Admin-only chat commands are useful for controlled testing. The current key command is rating control, for example:

```text
!rating 2500
```

Games where the admin intentionally changes bot strength should be excluded from engine-strength loss analysis.

Opening and ending chat were restored because they make bot games easier to monitor and confirm the chat pipeline is alive.

## Endgame Handling

Suspicious endgame behavior was observed, including poor promotion choices in simple king-and-pawn endings. If tablebase-selected moves look unnatural or reduce practical winning chances, disable lichess-bot tablebase move selection and let the engine search. Stockfish may still use Syzygy internally through UCI options.

Recommended conservative setting:

```yaml
engine:
  online_moves:
    online_egtb:
      enabled: false
  lichess_bot_tbs:
    syzygy:
      enabled: false
```

## Resource And Concurrency Policy

More concurrency is not automatically stronger. Stockfish can usually support higher concurrency by splitting CPU threads and hash. Lc0 with a large network is heavier and should normally run at `concurrency: 1` until proven stable.

Operational goals:

- Record resource usage continuously in `resource_records/`.
- Export resource usage by game, day, or week when comparing configs.
- Avoid setting `Threads * concurrency` above available CPU resources for Stockfish.
- Avoid multiple simultaneous Lc0 games unless network size, backend, and latency are verified.

## Loss Analysis Checklist

Classify each loss before changing code or config:

- Opening: early book choice led to a lasting disadvantage.
- Time management: flagged, moved too slowly at low time, or had excess time while making shallow blunders.
- Event stream: bot stopped receiving events or failed to move after opponent action.
- Network/proxy: token validation, API calls, or move posts failed.
- Engine crash: engine process exited or UCI protocol broke.
- Strength gap: opponent engine was simply stronger in the same conditions.
- Admin test: exclude games affected by `!rating` or manual experiments.

Use PGNs, Lichess links, engine logs, and resource records together. Do not infer cause from the result alone.

## Autoresearch Direction

The long-term goal is agent-driven improvement of bullet and blitz ratings, roughly targeting the 3050 range. A practical two-bot setup uses separate accounts and separate machines. Each bot can be managed by a different agent or model, then tested through public games and controlled head-to-head games.

Avoid overfitting to the local opponent. Keep public high-rated bots in the evaluation set and document every change with:

- Hypothesis
- Config or code diff
- Verification commands
- Result window
- Rollback plan

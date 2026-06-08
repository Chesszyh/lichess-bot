# Bot Optimization History And Configuration Notes

This document summarizes the issues found while operating this fork and the improvements requested since the initial Stockfish deployment. Use it as a reference when deploying a second bot, enabling fork-specific features, or tuning a new machine.

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

## 2026-06-08 ThinkPad Stockfish Bullet/Blitz Tuning

This pass focused on the ThinkPad Stockfish deployment, with the goal of making rated bot-vs-bot bullet and blitz performance more stable near the 3080 range. The analysis prioritized losses and draws against similar or lower-rated bots. All runtime restarts were delayed until logs showed `Process Freed. Count: 0` and no `Stockfish/src/stockfish` process was active.

Current live matchmaking and challenge policy for this deployment:

- Accept only `bullet` and `blitz`; do not accept `rapid`.
- Prefer bullet through default matchmaking weights.
- Default outgoing games use 60 or 90 second base with 1 or 2 second increment.
- Keep ignored `config.yml` mirrored in `.config-history/config.yml` after every private config change.

### Opening Source Control

Evidence game: `scyR4oww`, a bullet loss as black against `CloudNetBot`.

The first move, `1...Nf6`, came from the local opening book. The following sharp sequence, including `...c5`, `...Nd5`, `...Qb6`, and `...Qxb2`, came from Lichess Opening Explorer. By the time Stockfish searched after `6. cxd5`, the bot was already in a bad Accelerated London pawn-grab line and the log showed a poor black winrate.

Changes made:

- Limit online opening explorer use to very shallow positions with `engine.online_moves.max_depth: 2`.
- Disable live online opening moves in the private Stockfish config.
- Keep bot-vs-bot polyglot selection on stronger weighted lines:
  - `selection: weighted_random`
  - `min_weight: 50`
- Fix weighted random book selection so the minimum weight filter is applied before sampling.

Related commits:

- `784d3ab Avoid weak book sidelines in weighted random play`
- `.config-history` `1a43e6b Prefer stronger weighted book lines against bots`
- `.config-history` `454c2fa Stop online books before sharp bot middlegames`

Operational note: for high-rated bot games, online opening explorer stats can prefer risky practical lines that are not good for this local Stockfish setup. Treat online openings as a shallow fallback only, not as a middlegame guide.

### Repetition Guard: Enforce Root Moves

Evidence game: `KvLfR0la`, a bullet draw by threefold repetition against `friendlybot_1700`.

The log showed `Filtering immediate threefold repetition moves`, but the final move still repeated. Root cause: `EngineWrapper.search()` passed filtered `root_moves` to the engine, but did not verify that the returned move was actually in the allowed list.

Change made:

- After search, if `search_root_moves` exists and the engine result is outside that list, replace it with the first allowed move and log a warning.

Regression test:

- `test_search__does_not_play_filtered_repetition_if_engine_returns_it`

Related commit:

- `1d5bd97 Keep repetition guard authoritative after search`

### Repetition Guard: Score-Bounded Avoidance

Evidence games: `o1u2AXZc` and `imlXjLuL`, bullet draws by threefold repetition after the first repetition-guard fix.

`o1u2AXZc` showed that hard-filtering every immediate repetition can be harmful. At move 69 the repeated move was filtered, but the best non-repeating alternative evaluated around `-5.17` from an otherwise equal position. This proved that repetition avoidance should be a preference, not an absolute rule.

Change made:

- Search the normal best move first.
- If the best move immediately creates a threefold repetition, search again with non-repeating root moves.
- Use the non-repeating move only if the score loss is within `repetition_guard.max_score_loss_cp`.
- The live private config sets `max_score_loss_cp: 150`.
- `config.yml.default` documents a conservative default of `200`.

Regression test:

- `test_search__keeps_repetition_when_safe_alternative_loses_too_much`

Related commits:

- `afc7ee1 Limit repetition avoidance to sound alternatives`
- `.config-history` `3958411 Bound repetition avoidance score loss`

Operational note: after this change, a draw by repetition is still acceptable when every non-repeating alternative is materially worse. The desired next improvement is not to force bad endgame moves, but to avoid entering dead-equal structures too early.

### Draw Offers: Avoid Locking In Below-Target Results

Evidence game: `dzsQr4Rh`, a bullet draw by agreement as white against `CupchessBot`.

The bot repeatedly evaluated the simplified endgame as `0.00` and then offered a draw. The opponent was rated above the bot, so the current lower-rated-draw protection did not block the offer. For a deployment trying to stabilize near 3080, this is still a weak practical outcome when the opponent is below that target band: the bot locks in no meaningful rating progress instead of continuing to test the opponent's conversion and clock handling.

Change made:

- Add `draw_or_resign.offer_draw_min_rating`.
- Set the live private Stockfish config to `offer_draw_min_rating: 3080`.
- Apply the floor only to bot-initiated normal engine-equality draw offers.
- Keep elite incoming draw acceptance separate from bot-initiated normal equality draw offers.

Regression tests:

- `test_search__does_not_offer_normal_draw_below_target_rating_floor`
- `test_search__offers_normal_draw_at_target_rating_floor`

Operational note: this should be implemented as a narrow draw-offer policy, not as a blanket refusal to accept every high-rated draw offer. The aim is to stop the bot from voluntarily ending playable equal games below the target rating band.

### Opponent Pool: Avoid Below-Target Draw Sinks

Evidence game: `G5YWiyfP`, a bullet draw by threefold repetition as white against `friendlybot_1700`.

This game was played before the `offer_draw_min_rating` process restart took effect. The bot correctly declined an incoming draw offer, but the final repetition was unavoidable: before `57. Kg1`, python-chess showed exactly one legal move, and that move immediately produced the threefold. The practical problem happened earlier: the outgoing matchmaking floor was still `3000`, so the bot voluntarily entered another rated game against a 3026 opponent where a draw is below the 3080 target band.

Change made in the live private Stockfish config:

- Raise incoming `challenge.min_rating` from `3000` to `3080`.
- Raise outgoing `matchmaking.opponent_min_rating` from `3000` to `3080`.
- Raise outgoing `matchmaking.preferred_opponent_min_rating` and the `blitz_fallback` preferred floor from `3000` to `3080`.

Operational note: this may reduce game volume when few 3080+ bots are online. That is intentional for this phase: the evidence window had too many non-wins against 3000-3079 and even sub-3000 bots, which is poor signal for stabilizing both bullet and blitz near 3080.

### Verification From This Pass

Commands that passed:

```bash
.venv/bin/pytest test_bot/test_engine_time_management.py -q
```

Latest passing result for the time-management and repetition-guard file:

```text
30 passed
```

Configuration loading was also checked for the live private file, confirming:

```text
repetition_guard.enabled=True
repetition_guard.min_rating_gap=-25
repetition_guard.max_score_loss_cp=150
draw_or_resign.offer_draw_min_rating=3080
```

Known verification debt:

- `ruff check --config test_bot/ruff.toml lib/engine_wrapper.py test_bot/test_engine_time_management.py` still fails on existing complexity, docstring, mutable class attribute, and unused fake-engine argument warnings.
- `mypy --strict lib/engine_wrapper.py test_bot/test_engine_time_management.py` still fails on existing timeout typing, homemade engine override signatures, and fake-engine assignment types.
- These failures are not clean-room blockers for the repetition changes, but they raise the maintenance cost of further strategy work.

### Future Optimization Directions

Prioritize these directions before adding heavier local experiments:

- Reduce early drawish openings against lower-rated bots. Berlin Wall, QGD Orthodox, and highly simplified Ruy Lopez structures repeatedly reach stable `0.00` positions.
- Add opponent-aware opening selection: preserve soundness against elite bots, but choose more asymmetric Stockfish-approved lines against lower-rated bots.
- Track low-rated draws by opening family and side. If one family dominates, adjust the local book or bot-specific polyglot weights first.
- Make repetition avoidance time-aware. When the opponent is very low on time, allow slightly more score loss to keep the game alive; when both sides have enough time, keep the current conservative threshold.
- Validate the new draw-offer floor in live games like `dzsQr4Rh`; if too many target-band games become dead flag races, tune the floor or add a clock-aware exception.
- Validate the 3080 opponent-pool floor. If game volume becomes too sparse, prefer a temporary short fallback window over permanently re-opening 3000-3079 draw sinks.
- Consider a "complexity preference" only after engine score is near equal, using cheap signals such as material count, pawn asymmetry, legal move count, and queens present. Do not add heavy local engine experiments while the live bot is playing.
- Clean up `engine_wrapper.py` complexity and test fake-engine typing before larger strategy changes, so future regressions are easier to isolate.

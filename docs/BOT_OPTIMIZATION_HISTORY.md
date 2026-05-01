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

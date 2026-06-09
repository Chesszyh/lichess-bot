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

Follow-up evidence: after the Berlin Wall was filtered on the bot's white side, the latest live target-band game `VT7zOio9` as black against `Cheszter` still reached a repeated Ruy Lopez Closed, Chigorin Defense structure and drew by threefold. The recent game list also showed many black-side bot games entering the same Chigorin/Breyer family, including lower-rated or low-signal draws against `ilovecatgirl`, `duchessAI`, `Koi_Bot`, `coda_bot`, and `Moment-That-Inspires`.

Additional private config change:

- Initially, in the bot-specific Polyglot profile, skip `Na5` after:
  - `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3`
- The real live book was checked at that position. It contains:
  - `Na5` with weight `12`.
  - `Nb8` with weight `6`.
- With live `normalization: max` and `min_weight: 50`, `Nb8` remains above threshold after filtering `Na5`, so the bot can leave the repeated Chigorin line without weakening the book threshold or dropping out of book.

Later evidence showed that leaving `Nb8` active still forced a repeated Ruy Lopez Closed Breyer path. Games `N1AY97NU`, `h1EjQzfE`, `2R78e4KP`, `Yl9L44Tx`, and `dums3X5c` drew from the same `...h3 Nb8 d4 Nbd7 ...` family, and `UJlBX5Z5` lost from the same family after an early negative first search. The live book at the exact `...h3` tabiya contained `Na5`, `Nb8`, `Bb7`, `h6`, `Re8`, `Nd7`, and `Be6`; the private config now filters all of those current book moves so `get_book_move` returns no book move and Stockfish searches the position directly.

Follow-up evidence from live game `yiF82zTL` showed that the full `...h3` avoid list worked in the narrow sense: at the tabiya, no book move was played, and Stockfish searched before choosing `9...Bb7` with about `-0.41`, `45.5%`, depth 24. The game still drew because Polyglot immediately re-entered the adjacent Ruy Lopez Closed/Flohr path for `...Re8` and `...Bf8` after the engine's `...Bb7`. The follow-up code change adds `book_exit_lockout_plies`; the live bot-specific value is `6`, which skips the next two bot book turns after an avoid filter exhausts every current book candidate.

Follow-up evidence: the next live target-band game `IBkQluUF` as white against `Cheszter` reached `Italian Game: Two Knights Defense, Polerio Defense, Bishop Check Line` and drew by threefold. This repeated the same white-side `4. Ng5` Two Knights family seen in `ol8VgVif`, and the final repetition guard allowed the draw only because the best non-repeating move lost `214 cp`, above the live `150 cp` limit.

Additional private config change:

- In the bot-specific Polyglot profile, skip `Ng5` after:
  - `e4 e5 Nf3 Nc6 Bc4 Nf6`
- The real live book was checked at that position. It contains:
  - `Ng5` with weight `31`.
  - `d4` with weight `15`.
  - `O-O` with weight `4`.
  - `Nc3` and `d3` with weight `3`.
- With live `normalization: max` and `min_weight: 50`, `d4` remains above threshold after filtering `Ng5`, so the bot stays in book while leaving the forcing Two Knights repetition channel.
- Do not raise the repetition guard cap from this game alone; the guard behaved as configured, and the cleaner fix is to avoid the opening family that keeps producing equal repetition positions.

Follow-up evidence: after the Two Knights `Ng5` filter, live game `ezGWI9wS` as white against `Cheszter` avoided that line but lost from a different Italian book branch. The game entered `Italian Game: Evans Gambit, Sokolsky Variation`:

```text
e4 e5 Nf3 Nc6 Bc4 Bc5 b4 Bxb4 c3 Ba5 d4 d6 Bg5
```

The log showed the bot's first seven white moves came from the local Polyglot book: `e2e4`, `g1f3`, `f1c4`, `b2b4`, `c2c3`, `d2d4`, and `c1g5`. The first engine move after the book at move 8 evaluated the white position at about `-0.88` with `31.0%` winrate, and the game eventually ended in a white resignation for `-5`. That makes the Evans branch a higher-signal book loss than the surrounding target-band draws.

Additional private config change:

- In the bot-specific Polyglot profile, skip `b4` after:
  - `e4 e5 Nf3 Nc6 Bc4 Bc5`
- The real live book was checked at that position. It contains:
  - `b4` with weight `51`.
  - `c3` with weight `37`.
  - `O-O` with weight `16`.
  - `d3` with weight `5`.
- With live `normalization: max` and `min_weight: 50`, `c3` remains above threshold after filtering `b4`, so the bot stays in book while avoiding the Evans Gambit branch that left it materially worse.
- Do not change the global bot book threshold from this game alone; the evidence points to a specific bad branch, and the narrow avoid rule is easier to validate and revert.

Verification:

```text
bot Nb8 c6b8
after e4 e5 Nf3 Nc6 Bc4 Bc5: b4 51, c3 37, O-O 16, d3 5
after filtering b4 with max/50: c3 remains eligible
```

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

### Post-Floor Live Check

After the 3080 opponent-pool floor was deployed, the live log confirmed the bot searched only inside the target band:

```text
Seeking bullet game with opponent rating in [3080, 4000] ...
```

The first selected opponent was rejected by Lichess because of the daily bot-vs-bot opponent rate limit. Existing matchmaking cooldown handling then removed that opponent from the current pool, and the next search selected the remaining suitable opponent instead of retrying the same blocked bot.

Evidence game: `zlb9HQC5`, a rated 90+1 bullet game as black against `TakticproChess` rated 3099.

The game ended by threefold repetition from an equal Italian Game, Giuoco Pianissimo structure. Because the opponent was above the 3080 target band, this draw was acceptable under the current policy and produced a small positive rating result. The bot declined incoming draw offers, so the `offer_draw_min_rating` change behaved as intended in this sample.

Operational note: repeated target-band draws are not currently a regression. If they become the main bottleneck, analyze opening families and conversion chances before relaxing the 3080 floor.

### Draw Offers: Keep Playing With Large Clock Edge

Evidence game: `J7nJYTTZ`, a rated 90+1 bullet game as white against `TakticproChess` rated 3097.

The bot accepted an incoming draw offer in a stable `0.00` queen endgame while holding a large clock edge. The live log showed the bot had about 97 seconds while the opponent had about 11 seconds. A target-band draw is acceptable when clocks are normal, but accepting here gives up a practical bullet win condition that is especially valuable on this 4-core ThinkPad deployment.

Follow-up evidence game: `xzMGfX4n`, a rated 90+1 bullet game as black against `BlueMoonBot` rated 3115.

The bot correctly declined an incoming draw offer with about 91 seconds versus 11 seconds, but later proactively offered a normal `0.00` draw with about 92 seconds versus 10 seconds. The opponent accepted. Root cause: the clock-edge guard only ran when `draw_offered` was true, so it protected incoming draw acceptance but not proactive normal draw offers.

Change made:

- Add `draw_or_resign.offer_draw_clock_advantage_enabled`.
- Add speed, opponent-clock, and minimum-clock-advantage thresholds for that guard.
- Enable the guard in the live private Stockfish config for `bullet` and `blitz`.
- Set the live thresholds to decline or skip normal draw offers when the opponent has at most 15 seconds and the bot has at least a 60 second clock edge.
- Apply the same clock-edge guard to proactive normal draw offers, not only incoming draw offers.

Regression test:

- `test_search__does_not_accept_normal_draw_when_opponent_is_near_flagging`
- `test_search__does_not_offer_normal_draw_when_opponent_is_near_flagging`

Operational note: this only blocks normal draw-offer acceptance and proactive normal draw offers under a large clock edge. It does not stop the bot from offering or accepting ordinary equal target-band draws when both clocks are healthy or close.

### Repetition Guard: Override Rating Gate With Large Clock Edge

Evidence game: `nSLk3U9v`, a rated 90+1 bullet game as white against `TakticproChess` rated 3097.

The bot declined multiple incoming draw offers and reached a large practical clock edge, about 101 seconds to 31 seconds, but the game still ended by threefold repetition. The log did not show `Filtering immediate threefold repetition moves` for this game. Root cause: `repetition_guard.min_rating_gap` was `-25`, while the opponent outrated the bot by about 65 points, so the repetition guard never ran even with a decisive bullet clock edge.

Follow-up evidence game: `xUcwqJsv`, a rated 60+1 bullet game as white against `Cheszter` rated 3105.

The bot again declined an incoming draw offer, reached about 64 seconds versus 24 seconds, and still drew by threefold repetition. This time the final repetition was created by the opponent's `...Kc5`, not by the bot's move. Local PGN rule analysis of the pre-final position showed the bot's `Nb4` allowed exactly one immediate opponent threefold claim reply, while 12 legal bot moves did not hand over that one-move claim.

Change made:

- Add `repetition_guard.clock_advantage_override_enabled`.
- Add speed, opponent-clock, and minimum-clock-advantage thresholds for the rating-gate override.
- Enable the override in the live private Stockfish config for `bullet` and `blitz`.
- Set the live thresholds to allow repetition avoidance when the opponent has at most 40 seconds and the bot has at least a 30 second clock edge.
- Add opt-in `repetition_guard.avoid_opponent_immediate_claim`.
- Enable it in the live private Stockfish config, so a guarded search can avoid moves that let the opponent claim a threefold repetition on the next move.
- Keep `repetition_guard.max_score_loss_cp: 150`, so this override does not force clearly losing non-repeating moves.

Regression test:

- `test_search__filters_repetition_against_higher_rated_opponent_with_large_clock_edge`
- `test_search__avoids_move_allowing_opponent_immediate_threefold_with_clock_edge`

Operational note: this is a practical bullet/blitz conversion rule, not a general anti-draw setting against stronger bots. Without a large clock edge, the existing rating gate still protects high-rated target-band draws.

### Matchmaking Cooldowns And Pool Diagnostics

After the 3080 floor went live, the next issue was not another completed loss. The bot often found no suitable 3080+ target-band opponents after applying blocklists, cooldowns, game-speed support, and rating filters.

Representative live log after the latest restart:

```text
Seeking blitz game with opponent rating in [3080, 4000] ...
Found 314 online bots
Rejected online bot candidates: configured_blocklist=12, global_cooldown_unknown=40, no_blitz_games=15, rating_below_min=246, self=1
Choosing from 0 suitable opponents
```

Changes made:

- Log online-bot rejection counts by reason so sparse pools can be diagnosed from normal runtime logs.
- Persist cooldown source metadata so new cooldowns are distinguishable as ordinary declines, unanswered outgoing challenges, configured blocklist entries, or other known sources.
- Preserve legacy cooldowns with source `unknown` rather than guessing. The current state contains mixed old causes, so bulk-deleting `unknown` would be unsafe.
- Log the first few target-band bots blocked by global cooldown, including username, rating, cooldown source, and remaining minutes. This makes the next 3080+ pool decision inspectable without dumping the full online bot list.
- Add `matchmaking.outgoing_challenge_cooldown_minutes`.
  - Default: `720` minutes.
  - Live private Stockfish config: `180` minutes.
  - Purpose: scarce 3080+ targets should not disappear for 12 hours merely because they did not answer an outgoing challenge.
- Add `matchmaking.decline_cooldown_minutes`.
  - Default: `360` minutes.
  - Live private Stockfish config: `180` minutes.
  - Explicit rated/casual mode-conflict declines still keep the longer six-hour global cooldown.
- Add `matchmaking.draw_cooldown_minutes`.
  - Default: `0` minutes, so this is opt-in.
  - Live private Stockfish config: `30` minutes.
  - Purpose: after `xzMGfX4n` and `Wp8SbY5A`, avoid immediately spending another bot-vs-bot daily game on the same target-band draw sink.
- Add `engine.polyglot.avoid_moves`.
  - Default: `[]`, so this is opt-in.
  - Live private Stockfish bot profile: after `e4 e5 Nf3 Nc6`, skip `Bb5`.
  - Purpose: repeated white-side Berlin Wall draws showed that the book should stop entering `Bb5 Nf6 O-O Nxe4` against bots.
- Add `matchmaking.try_overrides_on_empty_pool`.
  - Default: `false`, so upstream-style weighted random override selection is unchanged.
  - Live private Stockfish config: `true`.
  - Purpose: after a target-band bullet search returns zero candidates, immediately try the lower-weight `blitz_fallback` instead of waiting another no-candidate interval.
- Add `matchmaking.legacy_unknown_cooldown_max_minutes`.
  - Default: `0`, so historical state is preserved unless explicitly migrated.
  - Live private Stockfish config: `360` minutes.
  - Purpose: cap old source-unknown global cooldowns that were saved before cooldown source tracking and now block scarce target-band candidates for years.
  - Safety boundary: only empty-aspect cooldowns with missing or `unknown` source are capped; configured blocklist entries are re-added after state load and remain 10-year blocks.
- Shorten no-candidate retry waits when a target-band cooldown is about to expire.
  - Evidence: at `2026-06-08 19:49:58 UTC`, bullet and blitz fallback both found `0` suitable opponents, while `Cheszter` was in the 3080+ bullet target band with only `7m` of `drawn_game` cooldown remaining.
  - Previous behavior waited the fixed `15m` no-candidate delay, so the bot would idle for several extra minutes after the best visible target-band candidate became eligible again.
  - New behavior keeps the fixed `15m` wait when there is no near-expiring target-band cooldown, but wakes shortly after the earliest target-band cooldown expiry when that is sooner.
  - This improves game volume without lowering the `3080` rating floor, deleting cooldown state, or repeatedly challenging a still-cooled opponent.
  - Live result after restart: the next search at `19:57:06 UTC` found exactly one suitable bullet opponent and challenged `Cheszter`.
  - Evidence game: `VT7zOio9`, a rated bullet draw as black against `Cheszter` rated 3104, was not a loss and gave NeuroSoCute `+1`.
  - In that game the bot declined incoming draw offers and skipped proactive normal draw offers while holding a large clock edge. The final threefold was allowed only after the guarded alternatives were measured as losing `280` and `468` centipawns, beyond the live `repetition_guard.max_score_loss_cp: 150`.
  - Operational note: this result supports the current score-loss safety cap. Future improvement should target earlier opening asymmetry or complexity, not forcing materially worse non-repeating moves in dead-drawn endings.

Related commits:

- `d1d2d5c Expose sparse matchmaking rejection causes`
- `bae1148 Shorten unanswered challenge cooldowns by config`
- `3d849d5 Track matchmaking cooldown sources`
- `176e5b1 Shorten ordinary decline cooldowns by config`
- This pass: log target-band cooldown blockers.
- This pass: cool down drawn fast-game bot opponents.
- This pass: filter the repeated bot-side Berlin Wall book move.
- This pass: try blitz fallback immediately when the preferred bullet pool is empty.
- This pass: cap legacy source-unknown global cooldowns in live config.
- This pass: retry after near-expiring target-band cooldowns instead of always waiting a full no-candidate interval.

Operational note: this is a pool-health and rating-protection change. It deliberately avoids relaxing the 3080 floor until there is evidence that the shorter, source-aware cooldown policy is still too restrictive.

### Verification From This Pass

Commands that passed:

```bash
.venv/bin/pytest test_bot/test_engine_time_management.py -q
.venv/bin/pytest test_bot/test_engine_time_management.py test_bot/test_config.py -q
.venv/bin/pytest test_bot/test_matchmaking.py test_bot/test_config.py -q
.venv/bin/pytest test_bot/test_matchmaking.py::test_choose_opponent__retries_when_target_band_cooldown_expires_soon test_bot/test_matchmaking.py::test_choose_opponent__backs_off_when_all_candidates_are_filtered test_bot/test_matchmaking.py::test_choose_opponent__backs_off_when_no_online_candidates_match_filters -q
.venv/bin/pytest test_bot/test_matchmaking.py test_bot/test_config.py test_bot/test_external_moves.py -q
.venv/bin/pytest test_bot/test_engine_time_management.py test_bot/test_config.py test_bot/test_matchmaking.py test_bot/test_external_moves.py -q
.venv/bin/pytest test_bot/test_game_stream.py -q
.venv/bin/pytest test_bot/test_external_moves.py -q
.venv/bin/ruff check --config test_bot/ruff.toml lib/matchmaking.py
.venv/bin/ruff check --config test_bot/ruff.toml lib/matchmaking.py lib/config.py test_bot/test_matchmaking.py test_bot/test_config.py --ignore C901,PLR0912,ANN001,ARG005
.venv/bin/ruff check --config test_bot/ruff.toml lib/lichess_bot.py lib/config.py --ignore C901,PLR0912
.venv/bin/ruff check --config test_bot/ruff.toml lib/engine_wrapper.py test_bot/test_external_moves.py --ignore C901,D101,D102,D103,D107,PLR0912,PLR0913,PLR0915,PLR0917,PLW2901,RUF012,RUF100,ARG002
git diff --check
```

Latest passing result for the time-management and repetition-guard file:

```text
33 passed
```

Latest passing result for the matchmaking cooldown and config checks:

```text
64 passed
```

Latest passing result for the current book-filter, config, time-management, and matchmaking regression set:

```text
106 passed, 1 xfailed
```

Latest passing result for the current matchmaking fallback, config, and book-filter regression set:

```text
69 passed
```

Latest passing result for the current repetition-trap and config regression set:

```text
48 passed
```

Latest passing result for the EGTB-zero draw guard, normal clock-edge draw guards, config defaults, and current book-filter regression:

```text
19 passed in 0.46s
git diff --check: exit 0
config.yml offer_draw_clock_advantage_min_ms=30000
.config-history/config.yml offer_draw_clock_advantage_min_ms=30000
```

Latest passing result for the 8K19ZtZc draw-refusal fix and lightweight recent-game report:

```text
6 passed in 0.42s
config.yml offer_draw_clock_advantage_accept_min_score_cp=1
.config-history/config.yml offer_draw_clock_advantage_accept_min_score_cp=1
recent_bot_game_report.py flags i6JbiFiR, 8K19ZtZc, and UJlBX5Z5 as priority losses
live game CFFJyFaz accepted Black's draw offer at exact 0 cp despite clock edge because 0 cp < 1 cp
```

Latest passing result for the dynamic `nobot` cooldown cap:

```text
69 passed in 0.42s
ruff touched files: All checks passed!
git diff --check: exit 0
config.yml dynamic_nobot_cooldown_max_minutes=360
.config-history/config.yml dynamic_nobot_cooldown_max_minutes=360
runtime_state maia3-79m_2600 source=nobot expires_at=2026-06-09T15:04:32.203579+00:00
09:07 matchmaking log shows maia3-79m_2600 source=nobot remaining=357m
```

Latest passing result for the Ruy Lopez `...h3` Breyer book-exit sidestep:

```text
config.yml avoid list=Na5,Nb8,Bb7,h6,Re8,Nd7,Be6
.config-history/config.yml avoid list=Na5,Nb8,Bb7,h6,Re8,Nd7,Be6
real book moves at the tabiya=Na5,Nb8,Nd7,h6,Be6,Bb7,Re8
get_book_move=None after filtering all current book moves
service restarted at 2026-06-09 09:21:07 UTC, PID 2807672
startup logs showed Engine configuration OK, Welcome NeuroSoCute!, and awaiting challenges
```

Latest passing result for the Polyglot avoid-exhausted lockout:

```text
6 passed in 0.34s
28 passed, 1 xfailed in 6.81s
ruff touched files: All checks passed!
git diff --check: exit 0
config.yml book_exit_lockout_plies=6
.config-history/config.yml book_exit_lockout_plies=6
real config/book check: first_get_book_move=None, lockout_until=23, follow_up_get_book_move=None
service restarted at 2026-06-09 09:47:05 UTC, PID 3063380
startup logs showed Engine configuration OK, Welcome NeuroSoCute!, and awaiting challenges
```

Configuration loading was also checked for the live private file, confirming:

```text
repetition_guard.enabled=True
repetition_guard.min_rating_gap=-25
repetition_guard.max_score_loss_cp=150
repetition_guard.avoid_opponent_immediate_claim=True
repetition_guard.clock_advantage_override_enabled=True
repetition_guard.clock_advantage_override_opponent_ms=40000
repetition_guard.clock_advantage_override_min_ms=30000
draw_or_resign.offer_draw_min_rating=3080
draw_or_resign.offer_draw_clock_advantage_enabled=True
draw_or_resign.offer_draw_clock_advantage_opponent_ms=45000
draw_or_resign.offer_draw_clock_advantage_min_ms=30000
draw_or_resign.offer_draw_clock_advantage_accept_min_score_cp=1
challenge.min_rating=3080
matchmaking.opponent_min_rating=3080
matchmaking.preferred_opponent_min_rating=3080
matchmaking.blitz_fallback.preferred_opponent_min_rating=3080
matchmaking.decline_cooldown_minutes=180
matchmaking.outgoing_challenge_cooldown_minutes=180
matchmaking.draw_cooldown_minutes=30
matchmaking.try_overrides_on_empty_pool=True
matchmaking.legacy_unknown_cooldown_max_minutes=360
matchmaking.dynamic_nobot_cooldown_max_minutes=360
engine.polyglot.opponent_selection.bot.avoid_moves[0].after=e4 e5 Nf3 Nc6
engine.polyglot.opponent_selection.bot.avoid_moves[0].moves=Bb5
engine.polyglot.opponent_selection.bot.book_exit_lockout_plies=6
engine.polyglot.opponent_selection.bot.avoid_moves includes after=e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3 moves=Na5,Nb8,Bb7,h6,Re8,Nd7,Be6
engine.polyglot.opponent_selection.bot.avoid_moves includes after=e4 e5 Nf3 Nc6 Bc4 Bc5 moves=b4
```

The live private book profile was checked against the real Polyglot book after `e4 e5 Nf3 Nc6`; it returned:

```text
f1c4
```

At the Ruy Lopez `...h3` tabiya, the same live private book profile now returns no book move:

```text
get_book_move=None
```

With the new live six-ply lockout, the follow-up position after engine-chosen `...Bb7` and White's `d4` also returns no Polyglot move:

```text
follow_up_get_book_move=None
```

Known verification debt:

- `ruff check --config test_bot/ruff.toml lib/engine_wrapper.py test_bot/test_engine_time_management.py` still fails on existing complexity, docstring, mutable class attribute, and unused fake-engine argument warnings.
- `ruff check --config test_bot/ruff.toml lib/lichess_bot.py lib/config.py` still fails on existing `lichess_bot_main`, `play_game`, and `validate_config` complexity.
- `mypy --strict lib/engine_wrapper.py test_bot/test_engine_time_management.py` still fails on existing timeout typing, homemade engine override signatures, and fake-engine assignment types.
- `mypy --strict lib/matchmaking.py` is still blocked by existing `lib/lichess.py` timeout type errors.
- Full `ruff check --config test_bot/ruff.toml lib/config.py` is still blocked by existing `validate_config` complexity.
- These failures are not clean-room blockers for the repetition changes, but they raise the maintenance cost of further strategy work.

### Pause-State Summary

At the point the optimization goal was paused, the live bot was running with the latest private Stockfish config. The service had restarted cleanly after the Polyglot lockout update at `2026-06-09 09:47:05 UTC`, logged `Engine configuration OK`, `Welcome NeuroSoCute!`, and was awaiting challenges. A `2026-06-09 09:48 UTC` snapshot showed service PID `3063380`, no `Stockfish/src/stockfish` child process, and the next challenge scheduled after `2026-06-09 09:50:07 UTC`. The live matchmaking log confirmed the current policy was searching only target-band bullet games:

```text
Seeking bullet game with opponent rating in [3080, 4000] ...
```

No new completed rated bullet or blitz games had been observed after the latest restart. The first post-restart searches found `309` online bots but `0` suitable target-band opponents after current blocklist and cooldown filters. That makes opponent-pool sparsity the next operational bottleneck, not a confirmed engine-strength regression.

Optimization attempts and outcomes from this ThinkPad Stockfish pass:

| Area | Evidence | Change | Test or live result | Status |
| --- | --- | --- | --- | --- |
| Challenge types | User request to stop rapid after current game | Accept only `bullet` and `blitz`; prefer bullet | Live log seeks bullet target-band games | Active |
| Opening explorer depth | `scyR4oww` loss vs `CloudNetBot` | Stop deep online opening explorer guidance; cap online depth at 2; prefer stronger weighted book lines | Weighted book regression covered by commit `784d3ab`; config mirrored privately | Active |
| Repetition filter authority | `KvLfR0la` repeated despite filtered root moves | Force search result back into allowed root moves when engine returns a filtered move | `test_search__does_not_play_filtered_repetition_if_engine_returns_it` | Active |
| Sound repetition avoidance | `o1u2AXZc` showed hard avoidance can choose a losing move | Compare normal best move with non-repeating alternative and cap accepted score loss | `test_search__keeps_repetition_when_safe_alternative_loses_too_much` | Active |
| Below-target draw offers | `dzsQr4Rh` draw by agreement vs below-target opponent | Add `draw_or_resign.offer_draw_min_rating`; live floor `3080` | `test_search__does_not_offer_normal_draw_below_target_rating_floor`; `test_search__offers_normal_draw_at_target_rating_floor` | Active |
| Below-target opponent pool | `G5YWiyfP` and other low-signal draws | Raise incoming and outgoing opponent floors to `3080` | Live log confirms `[3080, 4000]` search range | Active, watch volume |
| Target-band clock-edge draw offers | `J7nJYTTZ` accepted draw with about 97s vs 11s; `xzMGfX4n` proactively offered draw with about 92s vs 10s | Decline or skip normal draw offers in bullet/blitz when opponent is near flagging and bot has a large clock edge | `test_search__does_not_accept_normal_draw_when_opponent_is_near_flagging`; `test_search__does_not_offer_normal_draw_when_opponent_is_near_flagging` | Active |
| Target-band mid-clock draw offers | `ol8VgVif` vs `Cheszter` (3102) was drawn by agreement after the bot declined Black's draw offer around 105s vs 46.7s, then proactively offered draw around 108.7s vs 42.5s | Raise live `offer_draw_clock_advantage_opponent_ms` from `15000` to `45000`; later lower live `offer_draw_clock_advantage_min_ms` from `60000` to `30000` after another practical bullet clock-edge draw | Live config load check; normal draw-offer clock regressions cover the engine-search path | Active, watch whether target-band equal endings convert more often |
| EGTB-zero draw offers | `iCfhUIsj` vs `Cheszter` drew by agreement after Lichess EGTB returned `wdl: 0`; the bot offered the draw around 52s vs 16s, bypassing the normal draw clock guard | Require `normal_draw_clock_allows_offer()` before offering a draw from both online EGTB and local lichess-bot tablebase zero-WDL moves; live minimum clock-edge threshold is now 30s | `test_get_online_move__egtb_zero_respects_clock_edge`; config load check confirms `offer_draw_clock_advantage_min_ms=30000` | Active, needs live validation in the next target-band equal EGTB ending |
| Clock-edge draw refusal too aggressive | `8K19ZtZc` vs `Cheszter` declined a draw offer around 65s vs 33s with exact `0.0` evaluations, then drifted into a losing endgame and resigned after EGTB `wdl: -2` | Keep clock-edge suppression for proactive draw offers, but accept opponent draw offers when the latest bot cp score is below `offer_draw_clock_advantage_accept_min_score_cp`; live value `1` accepts exact `0.0` after the safe restart at `2026-06-09 08:49:03 UTC` | `test_search__accepts_zero_score_draw_offer_despite_clock_edge_when_configured`; config load check; `CFFJyFaz` live log accepted Black's draw offer at `0 cp < 1 cp` despite clock edge | Active, validated once live |
| Incoming draw endpoint semantics | `b5HgegKb` logged intent to accept normal draw offers, but Lichess chat recorded `Black declines draw`; `pxVN1kAf` repeated the pattern from a zero-WDL Lichess EGTB position after Black offered draw; `TU3CmM4p` showed the first endpoint patch was still incomplete because the final submit path re-read draw state after search | Add explicit `/api/bot/game/{gameId}/draw/{yes|no}` support and route accepted incoming normal/EGTB draw offers through it. Keep proactive draw offers on the move endpoint. Capture the incoming draw-offer flag before search and carry that snapshot through EGTB/online move selection and final submission. For zero-WDL EGTB, accept an already offered draw even when proactive tablebase draw offers are suppressed by clock edge | `test_submit_move_or_accept_draw__accepts_incoming_draw_without_moving`; `test_submit_move_or_accept_draw__keeps_proactive_draw_offer_on_move`; `test_submit_move_or_accept_draw__uses_captured_incoming_draw_offer`; `test_accept_draw__posts_draw_answer`; `test_get_online_move__egtb_zero_accepts_incoming_draw_offer_with_clock_edge`; `test_get_egtb_move__egtb_zero_accepts_incoming_draw_offer_with_clock_edge` | Active, needs live `/draw/yes` validation after deployment |
| Lightweight recent-game triage | Repeated manual curls made it easy to miss the next priority loss while a live game was active | Add `scripts/recent_bot_game_report.py` to flag losses, below-floor draws, and repeated draw/loss opening families without running local engine experiments | `test_recent_bot_game_report.py`; live `--max 16` report flagged `8K19ZtZc` and `UJlBX5Z5` | Active |
| Cheszter English losses | `8K19ZtZc` and `i6JbiFiR` were consecutive black-side losses against `Cheszter` from English Opening: Agincourt Defense after `1.c4 e6 2.g3 d5` | No opening change yet; the immediate code fix targets the clear draw-refusal failure, while Cheszter/English remains a watch item | PGN/log review only | Watch for one more repeated early-negative or losing endgame before filtering this branch |
| Breyer-family target-band draw/loss path | `N1AY97NU`, `h1EjQzfE`, `2R78e4KP`, `Yl9L44Tx`, and `dums3X5c` drew from the same Ruy Lopez Closed Breyer path after `...h3 Nb8 d4 Nbd7 ...`; `UJlBX5Z5` lost from the same family after an early negative first search | Bot-specific Polyglot profile now skips all current book moves after `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3`, forcing Stockfish search at that exact tabiya instead of falling through to low-weight book alternatives | Live book check showed current book moves `Na5`, `Nb8`, `Bb7`, `h6`, `Re8`, `Nd7`, and `Be6`; after filtering them, `get_book_move` returns no book move | Active, first exit validated in `yiF82zTL` |
| Polyglot re-entry after Breyer book exit | `yiF82zTL` showed the first no-book exit worked, but after Stockfish chose `...Bb7`, Polyglot re-entered for `...Re8` and `...Bf8`, reaching another drawish Ruy Lopez Closed/Flohr path | Add `book_exit_lockout_plies`; live bot value `6` skips Polyglot for the next two bot turns after `avoid_moves` exhausts every current book candidate | New regression verifies tabiya no-book, follow-up no-book during lockout, and book resumes after the lockout; real config/book check reports `first_get_book_move=None`, `lockout_until=23`, `follow_up_get_book_move=None` | Active, needs next live Ruy Lopez `...h3` validation |
| Target-band clock-edge repetition | `nSLk3U9v` repeated with about 101s vs 31s because rating gate blocked repetition guard; `xUcwqJsv` repeated with about 64s vs 24s because the bot allowed the opponent an immediate threefold claim | Add clock-edge override for repetition guard rating gate; lower live clock-edge threshold to 30s; add opt-in one-ply opponent-claim filtering while preserving score-loss cap | `test_search__filters_repetition_against_higher_rated_opponent_with_large_clock_edge`; `test_search__avoids_move_allowing_opponent_immediate_threefold_with_clock_edge` | Active |
| Opponent-pool sparsity | Latest searches found no suitable 3080+ opponent after filters | Add rejection-reason logs, cooldown source metadata, and target-band cooldown blocker details | Runtime logs now split configured blocklist, legacy unknown cooldowns, game-speed gaps, rating floors, self-filtering, and the first few cooldown-blocked target-band bots | Active, watch volume |
| Unanswered outgoing challenges | Scarce 3080+ candidates could be removed for 12 hours after no answer | Add `outgoing_challenge_cooldown_minutes`; live value `180` | `test_matchmaking.py` cooldown coverage; config check confirms live value | Active |
| Ordinary declines | Normal declines used a long global cooldown, reducing sparse target-band volume | Add `decline_cooldown_minutes`; live value `180`; keep mode-conflict declines at six hours | `test_add_challenge_filter__uses_short_default_decline_cooldown`; `test_add_challenge_filter__uses_configured_decline_cooldown`; mode-conflict regression | Active |
| Repeated target-band draw sink | `xzMGfX4n` and `Wp8SbY5A` were consecutive draws against `BlueMoonBot` | Add opt-in `draw_cooldown_minutes`; live value `30` for drawn bullet/blitz games against bots | `test_game_done__cools_down_bot_after_fast_draw`; `test_game_done__does_not_cool_down_bot_after_win`; config default test | Active |
| Repeated Berlin Wall book draws | Recent white-side bot draws repeatedly entered `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 ... Qxd8+ Kxd8`, including `Q1poOSgG`, `Wp8SbY5A`, and `nSLk3U9v` | Add opt-in Polyglot `avoid_moves`; live bot profile skips `Bb5` after `e4 e5 Nf3 Nc6` | `test_get_book_move__avoid_moves_filters_configured_san_line`; config default test; live config mirrored privately | Active, watch if Italian/other alternatives improve conversion |
| Evans Gambit book loss | `ezGWI9wS` as white against `Cheszter` entered `e4 e5 Nf3 Nc6 Bc4 Bc5 b4 ...`; first engine search after book was about `-0.88` and the game ended `-5` | Bot-specific Polyglot profile skips `b4` after `e4 e5 Nf3 Nc6 Bc4 Bc5` | Live book check shows `c3` remains eligible after filtering `b4`; config load check | Active, watch whether the `c3` replacement avoids early negative engine evaluations |
| Bullet pool empty while blitz is allowed | Post-deploy logs at `18:27:48` showed default bullet searched `[3080, 4000]`, found `0` suitable opponents, and waited until `18:42:48`; no same-cycle blitz attempt happened | Add opt-in `try_overrides_on_empty_pool`; live value `true`, with default bullet weight `5` before blitz fallback weight `1` | `test_choose_opponent__tries_blitz_fallback_when_bullet_pool_empty`; config default test | Active |
| Legacy source-unknown cooldowns | Runtime logs showed target-band candidates such as `maia3-79m_2600` blocked by `global_cooldown_unknown` for about 10 years from old state | Add opt-in `legacy_unknown_cooldown_max_minutes`; live value `360`, capped only for source-unknown global cooldowns loaded from state | `test_matchmaking_state__caps_legacy_unknown_global_cooldowns_when_configured`; configured blocklist regression keeps 10-year blocks | Active, watch pool volume |
| Dynamic no-bot cooldowns | At `2026-06-09 08:57 UTC`, bullet fallback had no target-band candidates and blitz fallback showed `maia3-79m_2600` rated 3101 blocked by source `nobot` for about 10 years | Add opt-in `dynamic_nobot_cooldown_max_minutes`; live value `360`, capped only for dynamic source `nobot` global cooldowns, while configured blocklists remain 10 years | `test_declined_challenge__nobot_uses_configured_dynamic_cooldown_cap`; `test_matchmaking_state__caps_dynamic_nobot_global_cooldowns_when_configured`; configured blocklist regression | Active, improves sparse blitz target pool without lowering the 3080 floor |
| No-candidate retry cadence | At `19:49:58 UTC`, Cheszter was a 3106 bullet target blocked by only `7m` of draw cooldown, but the bot scheduled the next search `15m` later | When the target-band pool is empty because of a soon-expiring cooldown, retry shortly after that cooldown expires instead of always waiting the full no-candidate interval | `test_choose_opponent__retries_when_target_band_cooldown_expires_soon`; existing no-candidate backoff tests still pass | Active, improves volume without lowering rating floor |

Current private live thresholds worth preserving unless new games disprove them:

- `challenge.min_rating: 3080`
- `matchmaking.opponent_min_rating: 3080`
- `matchmaking.preferred_opponent_min_rating: 3080`
- `matchmaking.blitz_fallback.preferred_opponent_min_rating: 3080`
- `matchmaking.try_overrides_on_empty_pool: true`
- `matchmaking.legacy_unknown_cooldown_max_minutes: 360`
- `matchmaking.dynamic_nobot_cooldown_max_minutes: 360`
- `draw_or_resign.offer_draw_min_rating: 3080`
- `draw_or_resign.offer_draw_clock_advantage_opponent_ms: 45000`
- `draw_or_resign.offer_draw_clock_advantage_min_ms: 30000`
- `draw_or_resign.offer_draw_clock_advantage_accept_min_score_cp: 1`
- `repetition_guard.max_score_loss_cp: 150`
- `repetition_guard.avoid_opponent_immediate_claim: true`
- `repetition_guard.clock_advantage_override_opponent_ms: 40000`
- `repetition_guard.clock_advantage_override_min_ms: 30000`
- `engine.polyglot.opponent_selection.bot.book_exit_lockout_plies: 6`
- bot-specific Polyglot `avoid_moves` for `Bb5` after `e4 e5 Nf3 Nc6`, all current book moves in the Ruy Lopez `...h3` tabiya, `Ng5` after `e4 e5 Nf3 Nc6 Bc4 Nf6`, and `b4` after `e4 e5 Nf3 Nc6 Bc4 Bc5`

### Future Optimization Directions

Prioritize these directions before adding heavier local experiments:

- Use the new source-specific rejection logs and target-band blocker details to watch whether `global_cooldown_unknown` and `global_cooldown_nobot` shrink after their 360-minute caps and whether new cooldowns are mainly declines, unanswered challenges, or daily rate-limit blocks.
- If the blocker log is still too terse, add an explicit one-off diagnostic command that dumps the full target-band blocked candidate set with source and remaining cooldown time.
- If further migrating legacy `unknown` cooldowns, classify only entries with strong historical-log evidence. Do not bulk-delete or relabel unknown state.
- If volume remains too sparse, add a temporary and explicitly logged fallback window before permanently re-opening 3000-3079. Prefer a short-lived `3060-3079` fallback over undoing the target-band policy.
- Reduce early drawish openings against lower-rated bots. Berlin Wall, QGD Orthodox, and highly simplified Ruy Lopez structures repeatedly reach stable `0.00` positions.
- Add opponent-aware opening selection: preserve soundness against elite bots, but choose more asymmetric Stockfish-approved lines against lower-rated bots.
- Watch the Italian `e4 e5 Nf3 Nc6 Bc4 Bc5 c3` replacement after the Evans filter. If it also produces early negative engine evaluations, move the bot-specific book choice toward `O-O` or reduce the bot book depth in this branch instead of adding broad book randomization.
- Track low-rated draws by opening family and side. If one family dominates, adjust the local book or bot-specific polyglot weights first.
- Continue validating the new one-ply repetition trap filter in target-band games. If it avoids too many sound repetitions, keep the live 30 second clock-edge gate but raise `max_score_loss_cp` only after concrete PGN evidence.
- Validate the new draw-offer floor in live games like `dzsQr4Rh`; if too many target-band games become dead flag races, tune the floor or add a clock-aware exception.
- Validate the EGTB-zero draw guard in live games like `iCfhUIsj` and `pxVN1kAf`; equal tablebase positions should not be proactively offered as draws when the opponent is below 45s and the bot has a 30s or larger clock edge.
- Validate the new `/draw/yes` path in live games after `b5HgegKb` and `pxVN1kAf`; when policy accepts an incoming draw offer, Lichess chat should show an accepted draw rather than a decline caused by making a move.
- Keep watching the 8K19ZtZc draw-refusal fix after the `CFFJyFaz` live validation. In exact `0.0` repeated endings, opponent draw offers should be accepted through the draw endpoint unless the latest bot score is at least the live `1` cp threshold.
- Watch Cheszter English Opening: Agincourt Defense losses (`8K19ZtZc`, `i6JbiFiR`) before changing the `1.c4 e6 2.g3 d5` branch.
- Validate the Ruy Lopez `...h3` Breyer sidestep plus six-ply lockout. The bot should have no book move at that exact position and no Polyglot move for the next two bot turns; if the first Stockfish search is still materially negative, prefer a narrower searched alternative over lowering global book thresholds.
- Validate the 3080 opponent-pool floor. If game volume becomes too sparse, prefer a temporary short fallback window over permanently re-opening 3000-3079 draw sinks.
- Consider a "complexity preference" only after engine score is near equal, using cheap signals such as material count, pawn asymmetry, legal move count, and queens present. Do not add heavy local engine experiments while the live bot is playing.
- Clean up `engine_wrapper.py` complexity and test fake-engine typing before larger strategy changes, so future regressions are easier to isolate.

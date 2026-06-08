# HefYDfeq coda_bot Loss Review

## Scope

- Fresh game: `HefYDfeq`
- Record: `game_records/coda_bot vs ilovecatgirl - HefYDfeq.pgn`
- Control: rated bullet `120+1`
- Bot color: black
- Opponent: `BOT coda_bot` (`3035`)
- Result: loss, `-5`
- Aggregate report updated: `reports/bot-game-analysis-recent-fast-2026-06-09.md`

## Evidence

- The game began from the default matchmaking profile, not the `blitz_probe` override.
- The bot lost a `120+1` Semi-Slav Defense: Accelerated Meran Variation.
- No stale move, illegal move, or post-finish HTTP `400` was observed.
- A transient `ChunkedEncodingError` occurred, but the game stream reconnected and move submission continued.
- The bot kept significant clock for much of the game, then used exact `2000 ms` caps after dropping below the low-clock threshold.
- Final event: mate with bot rating diff `-5`.

## Spot-Check Findings

Bounded one-thread Stockfish checks were run only after `/api/account/playing` returned `active_count=0`.

- The final king-and-queen phase was already losing:
  - `47...Kxf6` differed from `Kf5`, but both were already heavily losing.
  - From `48...Ke6` onward, Stockfish saw forced mate sequences for white.
- The queen/rook transition was also already bad:
  - `38...g3` differed from the 2s Stockfish preference `R8e5`, but the preferred line was still around `-6.45` from black's perspective.
  - Subsequent checked moves were mostly identical to the bounded Stockfish choices but remained losing.

## Decision

- No code change from this single black-side `120+1` loss.
- No config change from this game alone.
- The stronger current action remains the white bullet opening leak:
  - three `60+1` white losses from `1.d4` Nimzo structures
  - zero recent `60+1` white losses from `1.e4`

## Follow-Up

- Keep this game in the aggregate report as another black-side bullet loss sample.
- Do not generalize a black Semi-Slav fix from one game; wait for a repeated prefix/control cluster.
- If approved, prioritize the config-only white book-selection mitigation documented in `reports/white-bullet-opening-leak-2026-06-09.md`.

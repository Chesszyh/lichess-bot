# Post-Threshold Live Watch

## Scope

- Baseline change: lowered local `bullet_time_management.clock_pressure_own_clock_threshold_ms` from `30000` to `15000`.
- Runtime restart baseline: `2026-06-08T19:05:19Z`.
- New completed rated active-control game: `oi6DonOy`.
- Current branch: `lc0+stockfish`.

## Latest Game

- `Cheszter vs ilovecatgirl - oi6DonOy.pgn`
- Rated bullet `90+1`
- Bot color: black
- Opponent rating: `3105`
- Result: draw
- Rating impact: `+2`
- Termination: Normal
- Final bot clock from game finish event: `12s`

## Evidence

- `reports/bot-game-analysis-post-clock-pressure-threshold-2026-06-09.md` analyzes only post-threshold games and currently shows:
  - `1` game analyzed
  - `1` rated bullet draw
  - `+2` rating
  - no actionable opponent leak watchlist entries
  - no losses
  - no saved bot eval drops
- The broader refreshed active-control report still identifies `CupchessBot | bullet | 90+1`, `abdcebot | bullet | 60+1`, and `friendlybot_1700 | bullet | 60+1`, but those samples are from before the relevant recent mitigations:
  - `CupchessBot` loss predates the clock-pressure threshold change.
  - `abdcebot` loss predates the higher-rated bot shallow-search guard.
  - `friendlybot_1700` rating-negative draw predates the lower-rated repetition draw guard.

## Decision

No new runtime/config/code change is justified from the current post-threshold sample. The only fresh game after the restart was a favorable draw against a higher-rated bot.

The next aligned action is to keep collecting post-threshold active-control games and only tune again if a new loss, costly lower-rated draw, or repeated time-management pattern appears after the current mitigations.

## Watch Items

- Confirm whether a rematch with `CupchessBot` at `90+1` still reaches the same low-clock tactical collapse after the new `15000 ms` pressure threshold.
- Confirm whether future `60+1` games against `abdcebot` still show high-clock tactical drops after the depth guard.
- Continue monitoring rating-negative draws against lower-rated bots; current lower-rated draw evidence is pre-repetition-guard.

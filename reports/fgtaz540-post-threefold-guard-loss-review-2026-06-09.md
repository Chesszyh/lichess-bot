# Fgtaz540 Post-Threefold Guard Loss Review

## Scope

- Fresh game: `Fgtaz540`
- Record: `game_records/Cheszter vs ilovecatgirl - Fgtaz540.pgn`
- Control: rated bullet `60+1`
- Bot color: black
- Result: loss, `-5`
- Aggregate report: `reports/bot-game-analysis-post-threefold-guard-2026-06-09.md`
- No local engine experiments were run while a game was active.

## Evidence

- `/api/account/playing` returned `active_count=0` before post-game inspection.
- The game ended by mate at `2026-06-09 03:40:15 +08:00`; Lichess exported the PGN immediately afterward.
- No post-finish stale move submission or HTTP `400` was observed for this game.
- The late endgame repeatedly used exact bullet caps of `700 ms` while bot clock stayed around `8.7-9.0s` and opponent clock stayed around `1.4-7.1s`.
- The online Lichess EGTB began returning moves only after the position was already lost; logs showed `wdl: -2` from `118...Ke8` onward.
- A direct tablebase API probe on the earlier nine-piece king-and-pawn positions returned no WDL/DTZ/DTM data, so raising `online_egtb.max_pieces` would not have supplied reliable guidance.

## Endgame Findings

- Local configured Stockfish checks found the king-and-pawn ending after `110...Kxg8` was already losing for black.
- The rook-trade sequence `108...Rc8 109.Rg8 Rxg8 110.hxg8=R Kxg8` was not the first clear root cause; Stockfish already evaluated black as losing several moves earlier.
- In the critical rook phase, configured Stockfish did not show a stable save from longer search:
  - `104...Rd6` matched configured Stockfish at `700 ms`; longer searches preferred `Rh1`, but with worse/lost scores.
  - `106...Rc6` and `107...Kf7` differed from one-off Stockfish suggestions, but all tested lines remained losing.
- The clock cap likely reduced practical defensive depth, but this single game does not establish a safe code/config change.

## Opponent Context

- Broader local PGN data vs `Cheszter`: `47` games.
- Bullet total: W-D-L `0-10-5`, rating impact `0` with one unknown diff.
- Blitz total: W-D-L `0-26-6`, rating impact `+3` with six unknown diffs.
- Rated bullet `60+1` vs `Cheszter`: W-D-L `0-3-1`, rating impact `+4`.
- This does not justify adding `Cheszter` to the block list from the current evidence.

## Decision

- No runtime code change.
- No config change.
- No restart.
- Keep watching fast bullet losses where the bot preserves significant clock while the opponent is below `10s`; more samples are needed before changing the critical-clock/clock-pressure ordering.

## Verification

- Generated `reports/bot-game-analysis-post-threefold-guard-2026-06-09.md`.
- Confirmed the game was no longer active before analysis.
- Confirmed no active game again before the bounded local Stockfish spot checks.
- Used bounded one-thread and configured Stockfish checks only after active games were clear.

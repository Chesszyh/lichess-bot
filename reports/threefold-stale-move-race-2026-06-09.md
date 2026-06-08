# Threefold Stale Move Race

## Scope

- Fresh game: `DTw5MeIe`
- Record: `game_records/ilovecatgirl vs Cheszter - DTw5MeIe.pgn`
- Control: rated bullet `60+1`
- Result: draw, `+1`
- Runtime symptom: after `gameFinish`, the worker still posted `g1h1` and received HTTP `400`.

## Evidence

- The final game stream update still had `status: started` after `18...Qg3+`.
- Local board reconstruction showed the current position was already a threefold repetition:
  - `board.is_repetition(3) == True`
  - `board.is_game_over(claim_draw=True) == True`
- The account stream emitted `gameFinish` at `03:23:58.368`.
- The worker submitted `POST /api/bot/game/DTw5MeIe/move/g1h1` at `03:23:58.692`, after the game was already finished.

## Root Cause

Existing stale-move guards only checked:

- `game.state["status"] != "started`
- whether the account-level control stream had already marked the game ID as finished

In this race, the per-game stream still reported `started`, and the worker reached `submit_move` before the shared finished-game state suppressed the move. The local board already contained the draw evidence, but `submit_move` did not check it.

## Change

Added a local guard in `EngineWrapper.submit_move`:

- skip move submission when `board.is_repetition(3)` is true
- log that the game is already a threefold repetition

This targets the observed Lichess threefold-draw race without adding an API call before every move.

## Validation

- Added regression coverage:
  - `test_submit_move__does_not_send_move_after_local_threefold_draw`
- Verified red before the fix:
  - failed with `lichess.moves_made == ['g1h1']`
- Verified green after the fix:
  - targeted test passed
  - full `test_bot/test_engine_time_management.py` passed: `40 passed`

## Runtime Note

The running LaunchAgent must be restarted while idle before the code change affects live games.

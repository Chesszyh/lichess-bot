# IfUsKs6H Blitz Black Ruy Loss

## Result

- Game: `friendlybot_1700 vs ilovecatgirl - IfUsKs6H.pgn`
- Control: rated blitz `300+2`
- Bot side: black
- Opponent: `friendlybot_1700` (`3010`)
- Result: normal loss by mate
- Rating impact: `-4`

## Evidence

- `IfUsKs6H` was the second accepted sample after narrowing `blitz_probe` to `300+2`/`300+3`.
- The opening again entered the black Ruy Lopez Open structure:
  - `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`
- Refreshed aggregate now covers `75` rated fast games.
- Overall scored rating impact is `-75` over `57` games.
- Bullet remains the larger leak at `-66` over `32` games.
- Blitz worsened from `-5` to `-9` over `25` scored games after `IfUsKs6H`.
- `Ruy Lopez: Open, Classical Defense | black | blitz` is now `-13` over `3` games.
- `300+2` fell from rating-positive to `-1` over `4` scored games; score is now W-D-L `0-5-1`.
- The loss was clock-rich rather than clock-pressure: the bot still had `169s` on the clock in the analyzer's loss record.

## Root Cause

- The repeated failure is not a generic `300+2` or low-clock issue.
- It is a black-side Ruy Lopez Open exposure that appears across bullet and blitz controls.
- The live local bot configuration had bot-vs-bot black bullet/blitz polyglot depth disabled at `0`, so the engine was allowed to choose and repeat `5...Nxe4`.
- Local book inspection showed `rodent.bin` would prefer `5...Be7` after `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O`:
  - `Be7`: weight `65520`
  - `Nxe4`: weight `32760`
  - `b5`: weight `32760`
- Re-enabling the full black bot book would be broader than the evidence justifies.

## Change

- Added a one-entry polyglot book that is small enough to track directly:
  - `engines/books/avoid-open-ruy-black.bin`
- The only entry maps the Ruy Lopez position after `5. O-O` to:
  - `5...Be7`
- Updated ignored runtime config mirrors:
  - `config.yml`
  - `.config-history/config.yml`
- Bot-vs-bot black bullet/blitz now uses the one-entry book with depth `5`; other black positions still fall through to the engine because the custom book has no entries there.

## Validation

- Parsed both ignored runtime config mirrors with PyYAML.
- Confirmed both mirrors resolve black bot polyglot to `engines/books/avoid-open-ruy-black.bin`.
- Confirmed both mirrors set black bot `bullet` and `blitz` book depth to `5`.
- Confirmed the custom book is exactly one polyglot entry and returns `f8e7`.
- Confirmed the custom book checksum is `354b70780e0bea67bb12e127d72aa7da7601bab4b546889cf156e57942239db9`.
- Confirmed `get_book_move()` returns `f8e7` from the actual config at the target Ruy position.
- Confirmed `get_book_move()` returns no move from the starting position, so the custom book does not broadly drive black openings.
- Pre-restart `/api/account/playing` returned `active_count=0`.
- LaunchAgent `org.chesszyh987.lichess-bot` was safely restarted from PID `33763` to PID `33621`.
- Post-restart log confirmed engine configuration OK, login, Lichess connection, and next challenge scheduling.
- Post-restart `/api/account/playing` returned `post_restart_active_count=0`.

## Follow-Up

- Post-mitigation local evidence has no accepted/completed game after `IfUsKs6H` yet; the next outgoing `300+3` blitz probe was declined by `Void_Bot`.
- Watch the next black-side Ruy Lopez bot game.
- Success signal: after `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O`, logs should show an opening-book move `f8e7` instead of an engine move `f6e4`.
- If the bot still reaches `...Nxe4 d4 b5`, verify whether the custom book was bypassed by a different move order before changing anything else.

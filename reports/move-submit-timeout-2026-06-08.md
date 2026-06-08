# Move Submit Timeout Leak for 2026-06-08

Bot: `ilovecatgirl`

## Evidence

- `game_records/ilovecatgirl vs abcd_engine - 2QVD5cp2.pgn` was a rated `60+1` bullet bot game.
- The bot lost as White by `Time forfeit` after move `21... Re6`.
- `lichess_bot_auto_logs/run.log` shows repeated `ReadTimeout` failures submitting `h1h5` to `/api/bot/game/2QVD5cp2/move/h1h5`.
- The generic POST backoff retried move submission until giving up after `28` tries, consuming about one minute of bullet clock.

## Change

- Move submission now uses a move-specific POST retry path.
- Non-move POST endpoints keep the generic retry behavior.
- Move POST attempts use a short retry budget so the game stream can reconnect and recover instead of blocking until flag fall.

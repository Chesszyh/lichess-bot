# White Bullet Opening Leak

## Scope

- Dataset: rated bullet/blitz PGNs since `2026-06-08T00:00:00Z`
- Aggregate report: `reports/bot-game-analysis-recent-fast-2026-06-09.md`
- No local engine analysis was run.
- No runtime behavior was changed in this report.

## Evidence

- Recent rated fast sample: `37` games, `26` draws, `10` losses, `1` win.
- Bullet is the current rating leak: `-32` rating over `20` games.
- Blitz is roughly stable in this sample: `-1` rating over `12` games.
- Focused `60+1` is the largest control leak: `-23` rating over `8` scored games.
- White `60+1` is the largest color/control leak: `-18` rating over `7` scored games.

## Repeated Opening Leak

Recent white `60+1` bullet games since `2026-06-08T00:00:00Z`:

- `1.d4`: `0-1-3` score as W-D-L by result bucket used here (`3` losses, `1` draw).
- `1.e4`: `0-4-0` (`4` draws, `0` losses).
- `Nimzo-Indian Defense: Normal Variation, Classical Defense`: `3` losses from `3` games.

The three Nimzo losses:

- `game_records/ilovecatgirl vs abcd_engine - 2QVD5cp2.pgn`: `-10`
- `game_records/ilovecatgirl vs MEGA-NOOB-BOT - wUt40hrP.pgn`: `-6`
- `game_records/ilovecatgirl vs abdcebot - MznBGMQZ.pgn`: `-5`

All three shared this first-eight-ply prefix:

```text
d4 Nf6 c4 e6 Nc3 Bb4 e3 O-O
```

## Book Trace

- Current bot-vs-bot white bullet book profile uses `engines/books/rodent.bin`.
- `rodent.bin` gives `e4` and `d4` equal top first-move weight (`65520` each).
- Current selection is `uniform_random`, so `1.d4` is selected with meaningful frequency.
- In the loss traces, only the first four white moves were book moves; the engine then continued into similarly losing structures.
- `reader.find()` on the current books returns `e4` as the deterministic best first move.

## Candidate Design

Recommended tactical mitigation:

- For bot opponents when the bot is white, switch local book selection from `uniform_random` to `best_move`.
- Keep existing bot black book disabled for bullet/blitz.
- Keep existing max book depth unchanged initially; this isolates the variable to deterministic top-book selection.
- Mirror the local ignored `config.yml` change into `.config-history/config.yml`.

Trade-off:

- This reduces opening diversity, but the current diversity is producing a repeated high-cost `1.d4` Nimzo loss cluster.
- If later `1.e4` becomes predictable or starts leaking, revisit with a purpose-built filtered book rather than restoring random `1.d4`.

## Current Decision

- Report only.
- No behavior change yet.
- The next behavior change should be a config-only opening-policy adjustment after approval.

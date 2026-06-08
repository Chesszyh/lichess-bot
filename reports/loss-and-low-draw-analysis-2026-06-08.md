# Loss and Lower-Rated Draw Analysis for 2026-06-08

Bot: `ilovecatgirl`

Scope:

- All local `game_records/*.pgn` available at analysis time.
- Focus requested by user: all losses, plus draws against lower-rated bots.
- Lower-rated draw definition used here: bot rating minus opponent rating is at least `100`.
- This was a lightweight PGN/header/opening scan only. No local engine analysis was run.

## Summary

- Bot games scanned: `2394`
- Bot losses: `469`
- Draws against opponents rated at least `100` lower: `109`

Top openings in all losses:

| Losses | Opening |
| --- | --- |
| `66` | Sicilian Defense: Najdorf Variation, English Attack |
| `24` | Caro-Kann Defense: Advance Variation, Short Variation |
| `10` | Ruy Lopez: Berlin Defense, Berlin Wall |
| `9` | French Defense: Steinitz Variation, Boleslavsky Variation |
| `8` | Caro-Kann Defense: Advance Variation |
| `8` | Semi-Slav Defense |
| `8` | Sicilian Defense: Moscow Variation, Main Line |

Top openings in lower-rated draws:

| Draws | Opening |
| --- | --- |
| `17` | Sicilian Defense: Najdorf Variation, English Attack |
| `10` | Sicilian Defense: Najdorf Variation |
| `5` | Semi-Slav Defense |
| `4` | Semi-Slav Defense: Meran Variation, Wade Variation |
| `3` | Sicilian Defense: Lasker-Pelikan Variation, Sveshnikov Variation, Chelyabinsk Variation |
| `3` | Sicilian Defense: Moscow Variation, Main Line |
| `3` | French Defense: Steinitz Variation |

## Largest Rating-Gap Draws

| Rating Gap | TC | Game | Opening | Termination |
| --- | --- | --- | --- | --- |
| `576` | `240+1` | `ilovecatgirl vs GNUPassant - Cdt4VUHk.pgn` | Caro-Kann Advance Short | Normal |
| `561` | `240+0` | `ilovecatgirl vs PeachFruit - aD2Tfss0.pgn` | Sicilian Taimanov Bastrikov | Time forfeit |
| `528` | `180+1` | `PeachFruit vs ilovecatgirl - nWc2j90j.pgn` | Catalan Open Modern Sharp | Normal |
| `483` | `90+0` | `SoloBot vs ilovecatgirl - ke35DrrS.pgn` | Sicilian Moscow Main Line | Normal |
| `478` | `90+2` | `simbelmyne-bot vs ilovecatgirl - 0kLqYVhg.pgn` | Sicilian Moscow Main Line | Normal |
| `472` | `240+2` | `Eichkatzerl vs ilovecatgirl - 42ytSeFu.pgn` | Sicilian Sozin Attack | Normal |
| `450` | `90+0` | `prokopakop vs ilovecatgirl - TQr2RUE6.pgn` | Najdorf English Attack | Normal |
| `429` | `120+0` | `ilovecatgirl vs prokopakop - FfzXRpyW.pgn` | Ruy Lopez Closed Smyslov | Normal |
| `427` | `60+0` | `prokopakop vs ilovecatgirl - SO2bW34b.pgn` | Najdorf | Normal |
| `419` | `60+0` | `prokopakop vs ilovecatgirl - ZnbOQOsf.pgn` | Najdorf | Normal |

## Takeaways

1. The dominant chess-pattern leak remains sharp Sicilian/Najdorf handling. It is both the largest loss cluster and the largest lower-rated draw cluster.
2. Lower-rated draws are not all harmless book draws: several are large rating-gap fast games where a win should be expected if the bot is targeting stable `3080` bullet/blitz.
3. Runtime cleanup still matters. Recent live logs show a finished blitz game (`BQes6qMc`) where the worker posted a move after a `gameFinish`, received HTTP `400`, and then reconnected as if the board stream failed. This wastes time and can compound the timeout/stall issues seen in older loss reports.

## Actions From This Turn

- Fix the inactive-game move POST path so a failed move submit after game finish does not force a reconnect.
- Keep tracking Najdorf and lower-rated draw clusters after the speed-specific book-depth changes are actually loaded by the running bot process.

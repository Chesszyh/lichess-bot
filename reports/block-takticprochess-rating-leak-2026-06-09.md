# Block TakticproChess Rating Leak

## Scope

- Date: `2026-06-09`
- Bot: `ilovecatgirl`
- Target modes: rated bullet/blitz, with active-control focus on `60+1`, `90+1`, `120+1`
- Method: PGN/report evidence only; no local engine experiment was run.

## Evidence

`reports/bot-game-analysis-active-controls-2026-06-08.md` identifies a current active-control leak:

- `TakticproChess | bullet | 120+1`: rating `-4` over `1` rated game.
- High-clock normal loss: `109s` left in `ilovecatgirl vs TakticproChess - yxoZcdPT.pgn`.
- Focused score by opponent includes `TakticproChess | bullet | 120+1`: W-D-L `0-0-1`, score `0.0%`.

A broader PGN pass over local records shows this is not isolated to one time control:

- `TakticproChess 240+2`: W-D-L-U `0-3-5-0`, rating `-16` over `8` rated games.
- `TakticproChess 300+2`: W-D-L-U `0-0-2-0`, rating `-8` over `2` rated games.
- `TakticproChess 30+0`: W-D-L-U `0-1-1-0`, rating `-4` over `2` rated games.
- `TakticproChess 120+1`: W-D-L-U `0-0-1-0`, rating `-4` over `1` rated game.

Other unblocked candidates were not added in this pass because the active-control evidence is weaker or mixed. For example, `DarkOnBot 60+1` is rating-positive in the local sample, and `bot1e 60+1` only has one active-control loss.

## Change

Added `TakticproChess` to both runtime `config.yml` and `.config-history/config.yml` in:

- `challenge.block_list`
- `matchmaking.block_list`

Private config history commit:

- `27ad418 Block TakticproChess rating leak`

## Deployment

- `/api/account/playing` returned `active_count=0` before config edit.
- Restarted/recovered bot runtime to PID `97874`; startup log confirms `Welcome ilovecatgirl!`.
- Preserved matchmaking cadence: next challenge after `Tue Jun 9 00:20:54 2026`.

## Verification

- YAML parsed for both config files.
- `TakticproChess` is present in both `challenge.block_list` and `matchmaking.block_list` for both config files.

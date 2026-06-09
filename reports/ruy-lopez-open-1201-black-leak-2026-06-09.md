# Ruy Lopez Open 120+1 Black Leak

## Scope

- Objective: document the newest bullet leak after the coda/codabot blocklist restart.
- Evidence source: local PGNs and refreshed aggregate report only.
- No local engine analysis was run.
- No runtime code was changed.

## New Sample

- Game: `CCI-6 vs ilovecatgirl - PxsslsQe.pgn`
- Start: `2026-06-09T08:11:15Z`
- Result: black loss, rating `-5`
- Control: `120+1`
- Opening: `Ruy Lopez: Open, Classical Defense`
- Prefix: `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`

## Aggregate Impact

- Aggregate now covers `70` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored impact is `-68` over `53` games.
- Bullet impact is `-66` over `32` games.
- Blitz impact is `-2` over `21` games.
- `120+1` focused score is now W-D-L `1-5-7`, score `26.9%`.
- `120+1 black` rating impact is now `-29` over `7` games.
- `Ruy Lopez: Open, Classical Defense | black | bullet | 120+1` is now W-D-L `0-0-3`.

## Interpretation

The latest loss is not another coda/codabot sample, but it repeats the same black-side Ruy Lopez Open family that already appeared in the loss cluster. That makes the current strongest hypothesis:

- The remaining bullet leak is structural exposure to the Open Ruy Lopez branch in `120+1` as black.
- The coda/codabot blocklist removes the top repeated opponents, but it does not by itself remove the opening/control exposure.
- A tactical engine tweak is not justified from this evidence alone, because the saved PGN evaluations show the position already deteriorating inside a recurring opening family and no fresh controlled engine comparison was run.

## Next Candidate Actions

- Prefer low-risk exposure reduction before deeper engine experiments while the bot is active.
- Candidate A: stop outgoing `120+1` matchmaking while keeping `60+1`, `90+1`, and the blitz probe.
- Candidate B: keep outgoing `120+1`, but narrow incoming challenge acceptance away from `120+1` by reducing `challenge.max_base` to `90`.
- Candidate C: keep time controls unchanged and prepare an opening-specific mitigation for black Ruy Lopez Open only after collecting a non-live engine/book comparison.

The current evidence favors Candidate A or B over changing blitz, because blitz is only slightly negative while bullet carries nearly all rating loss.

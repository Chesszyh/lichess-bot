# Bullet 90+1 Black Exposure Triage

## Scope

- Continuation point: after `738ad23 Document non-waiting closeout`.
- Evidence source: local rated fast PGNs, current aggregate report, ignored local config, and runtime log tail.
- No local engine search was run.
- No tracked runtime code was changed.
- A later ignored runtime config change narrowed `blitz_probe` after game `M8ZpgJQe` finished.

## Current Live Config

- Incoming challenge bounds are `challenge.min_base == 90` and `challenge.max_base == 90`.
- Default outgoing bullet matchmaking is `90+1` only.
- `blitz_probe` is now narrowed to `300` base with `+2/+3`.
- `coda_bot` and `codabot` remain in the local ignored incoming and outgoing blocklists.
- Bot-vs-bot white book selection remains `best_move`.
- Bot black bullet/blitz book depth remains disabled at `0`, matching the prior white-book isolation decision.

## Aggregate Evidence

- Refreshed aggregate now covers `73` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact is `-72` over `55` scored games.
- Bullet remains the clear leak at `-66` over `32` scored games.
- Blitz is now negative at `-6` over `23` scored games after the `M8ZpgJQe` loss.
- Focused `90+1` score is W-D-L `0-5-3`, score `31.2%`, rating `-9` over `8` scored games.
- `90+1 black` is worse than the aggregate `90+1` slice: rating `-12` over `6` scored games.

## Reachable 90+1 Samples

Recent rated `90+1` games in the current analysis window:

- `MEGA-NOOB-BOT vs ilovecatgirl - 87C7maRn.pgn`: black loss, Ruy Lopez Open Bernstein, opponent now blocklisted.
- `CloudNetBot vs ilovecatgirl - X4YQN6x8.pgn`: black draw, Queen's Pawn London, opponent now blocklisted.
- `ilovecatgirl vs abdcebot - Zd5yy2Mj.pgn`: white draw, Ruy Lopez Berlin Rio Gambit Accepted.
- `ilovecatgirl vs CupchessBot - C0SjBNos.pgn`: white draw, Semi-Slav Main Line.
- `CupchessBot vs ilovecatgirl - 21mY5MXC.pgn`: black loss, Italian Giuoco Pianissimo Four Knights.
- `Cheszter vs ilovecatgirl - oi6DonOy.pgn`: black draw, English Four Knights Nimzowitsch.
- `codabot vs ilovecatgirl - Ts2zIe97.pgn`: black draw, Slav Exchange, opponent now blocklisted.
- `friendlybot_1700 vs ilovecatgirl - i97cDXbZ.pgn`: black loss, Ruy Lopez Open Classical.

## Interpretation

- The current default bullet pool no longer exposes `60+1` or `120+1`, so the next reachable bullet leak is `90+1`.
- The harmful `90+1` samples are concentrated on black, not white.
- The two still-reachable black losses are against `CupchessBot` and `friendlybot_1700`; both are single-loss samples, so immediate global blocklisting would be weaker than the prior coda/codabot evidence.
- `friendlybot_1700` also produced useful blitz-probe draw evidence, so a global opponent block would remove useful blitz data as well as risky bullet data.
- Current code does not expose a `matchmaking.challenge_color` setting; outgoing challenges are created without a color parameter and therefore remain random-color.
- Adding color-aware matchmaking could reduce outgoing default bullet black exposure while keeping blitz controls separately configurable, but that is a runtime behavior feature and should be designed/tested separately rather than patched during an active game.

## Active Game Note

- `M8ZpgJQe` was a rated `180+3` blitz game from `blitz_probe`, with the bot black against `friendlybot_1700`.
- It ended as a normal black loss by mate, rating `-5`.
- Its opening again used an Open Ruy Lopez structure from the prefix `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- This confirms the black Open Ruy issue is not confined to default bullet `90+1`.

## Decision

- `M8ZpgJQe` is now finished and documented separately in `reports/m8zpgjqe-blitz-black-ruy-loss-2026-06-09.md`.
- Do not block `CupchessBot` or `friendlybot_1700` from the current evidence alone.
- Do not re-enable black bullet/blitz books in this pass, because prior evidence intentionally kept black book disabled while isolating the white-book fix.
- The immediate low-risk behavior change was to narrow `blitz_probe` to `300+2`/`300+3`, where the current aggregate has the strongest blitz evidence.
- If the black Open Ruy pattern recurs at longer blitz, the next behavior candidate is opening-specific design rather than another broad time-control filter.

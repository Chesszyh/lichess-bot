# Bullet 90+1 Black Exposure Triage

## Scope

- Continuation point: after `738ad23 Document non-waiting closeout`.
- Evidence source: local rated fast PGNs, current aggregate report, ignored local config, and runtime log tail.
- No local engine search was run.
- No runtime code or ignored runtime config was changed.
- No LaunchAgent restart was attempted because game `M8ZpgJQe` remained active in local log evidence.

## Current Live Config

- Incoming challenge bounds are `challenge.min_base == 90` and `challenge.max_base == 90`.
- Default outgoing bullet matchmaking is `90+1` only.
- `blitz_probe` remains unchanged at `180/240/300` base with `+2/+3`.
- `coda_bot` and `codabot` remain in the local ignored incoming and outgoing blocklists.
- Bot-vs-bot white book selection remains `best_move`.
- Bot black bullet/blitz book depth remains disabled at `0`, matching the prior white-book isolation decision.

## Aggregate Evidence

- Refreshed aggregate still covers `72` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact remains `-67` over `54` scored games.
- Bullet remains the clear leak at `-66` over `32` scored games.
- Blitz remains near neutral at `-1` over `22` scored games.
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
- Adding color-aware matchmaking could reduce outgoing default bullet black exposure while keeping `blitz_probe` random, but that is a runtime behavior feature and should be designed/tested separately rather than patched during an active game.

## Active Game Note

- `M8ZpgJQe` is a rated `180+3` blitz game from `blitz_probe`, with the bot black against `friendlybot_1700`.
- Latest local log evidence in this pass still had `status: started`.
- Its opening is again an Open Ruy Lopez structure from the prefix `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- It is intentionally excluded from aggregate and result conclusions until a finished PGN/result is available.

## Decision

- Do not restart while `M8ZpgJQe` is active.
- Do not block `CupchessBot` or `friendlybot_1700` from the current evidence alone.
- Do not re-enable black bullet/blitz books in this pass, because prior evidence intentionally kept black book disabled while isolating the white-book fix.
- Next evidence target: when `M8ZpgJQe` finishes, refresh the aggregate and check whether black Open Ruy exposure now extends from bullet into blitz.
- Next behavior candidate, if the active-game evidence confirms the pattern: design and test a `matchmaking.challenge_color` option so the default bullet path can request white while `blitz_probe` remains random.

# Goal Stop Summary

## Scope

- Covers tracked work from `9124fdd` through `9a5e7b5`, plus the final aggregate refresh in this stop pass.
- Goal state is not complete: bullet/blitz are not stable at `3080`.
- No heavy local engine experiments were run during an active game in this stop pass.
- Game `KZlP9dMr` was active during this stop pass and was deliberately not waited on or analyzed, per stop request.

## Tracked Changes

- Added `reports/white-bullet-opening-leak-2026-06-09.md` and initial `reports/bot-game-analysis-recent-fast-2026-06-09.md` in `9124fdd`.
- Added `reports/hefydfeq-coda-bot-loss-review-2026-06-09.md` and refreshed the aggregate in `a97f0f5`.
- Added `reports/bot-white-book-best-move-config-2026-06-09.md` in `07a5067`.
- Added restart verification and post-restart aborted-game follow-up in `ed8c1b5` and `2ccf4b0`.
- Refreshed the aggregate after the `Void_Bot` abort in `b52e8fe`.
- Documented the first `180+2` blitz probe draw against `CupchessBot` in `9a5e7b5`.
- Final stop-pass refresh extends the aggregate to `63` rated fast games and documents the second `180+2` draw against `Cheszter`.

## Local Runtime Config

- Ignored `config.yml` and `.config-history/config.yml` remain aligned.
- Bot-vs-bot polyglot selection is `best_move`; human selection remains `uniform_random`.
- Bot black bullet/blitz book depth remains disabled at `0`.
- Matchmaking default pool still probes `60+1`, `90+1`, and `120+1` bullet-style controls.
- `blitz_probe` override remains active for `180/240/300` base with `+2/+3` increments.

## Runtime Actions

- Performed one safe idle LaunchAgent restart after `/api/account/playing` returned `active_count=0`.
- Runtime PID changed from `91127` to `39567`.
- Post-restart checks confirmed reconnect and idle state.
- No later restart was performed.

## Evidence State

- Latest aggregate: `63` rated bullet/blitz games since `2026-06-08T00:00:00Z`.
- Overall scored rating impact: `-61` over `48` scored games.
- Bullet is the clear leak: `-61` over `30` scored games.
- Blitz is neutral: `+0` over `18` scored games.
- Worst current opponent/control watchlist starts with `coda_bot | bullet | 120+1`: risk `9`, `3` losses, rating `-15`.
- New repeated opening leak: Ruy Lopez Open structures as black, especially `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Nxe4 d4 b5`.
- Previous white bullet `1.d4` Nimzo leak was mitigated by deterministic bot book selection, but fresh post-change bullet evidence still needs review.

## Stop Decision

- Do not mark the optimization goal complete.
- Before any future restart, re-check active games; `KZlP9dMr` was not included in this stop summary.
- Next useful work should analyze the finished post-change bullet losses, especially black-side Ruy Lopez Open and `coda_bot` `120+1`, before making another config change.
- If a low-risk config change is needed next, prefer reducing exposure to leaking bullet controls/opponents over changing blitz, because blitz probe evidence is currently neutral-to-positive.

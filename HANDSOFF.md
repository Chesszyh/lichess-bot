# HANDSOFF

This is the handoff state for the ThinkPad Stockfish `lichess-bot` tuning goal as of 2026-06-09 UTC.

## Current Runtime State

- Main repo branch: `only-stockfish`.
- Main repo latest pushed handoff before this EGTB update: `0acc100 Preserve the stopped Stockfish tuning handoff`.
- Private config mirror latest committed handoff before this EGTB update: `.config-history` `116aec9 Mirror the Evans book sidestep privately`.
- `.config-history` has no remote configured; private mirror commits are local only.
- Last checked service state after applying the EGTB update: `lichess-bot.service` active under PID `2307937`, started at `2026-06-09 08:22:16 UTC`.
- Last checked startup logs showed `Engine configuration OK`, `Welcome NeuroSoCute!`, and connected to Lichess.
- Restart safety check before that restart showed no active `Stockfish/src/stockfish` game child. The previous game `h1EjQzfE` had ended in a draw, then matchmaking was idle and waiting for the next target-band retry.
- After committing this handoff, the main worktree should be clean except expected untracked local assets such as `Stockfish/`.

Do not restart while a game is active or while a Stockfish child process exists. Check first:

```bash
ps -eo pid,ppid,lstart,cmd | rg 'lichess-bot.py|Stockfish/src/stockfish|stockfish|tail -n 0 -F lichess_bot_auto_logs/run.log|timeout .*tail'
tail -n 160 lichess_bot_auto_logs/run.log
systemctl --user status lichess-bot.service --no-pager -l
```

## Current Live Policy

- Accept only `bullet` and `blitz`; rapid is no longer accepted.
- Prefer bullet first, then try the configured blitz fallback when the bullet pool is empty.
- Keep rated target-band games at `3080+`:
  - `challenge.min_rating: 3080`
  - `matchmaking.opponent_min_rating: 3080`
  - `matchmaking.preferred_opponent_min_rating: 3080`
  - `matchmaking.blitz_fallback.preferred_opponent_min_rating: 3080`
- Keep `config.yml` ignored/private. Mirror every private runtime config change in `.config-history/config.yml` and commit inside `.config-history`.

## Changes Made During This Tuning Pass

### Matchmaking And Pool Control

- Stopped accepting rapid after the active game completed; live policy is bullet/blitz only.
- Raised incoming and outgoing opponent floors to the 3080 target band.
- Preferred bullet for outgoing challenges while allowing blitz fallback when no bullet candidate is available.
- Added `try_overrides_on_empty_pool` so a failed bullet pool can try the blitz fallback in the same cycle.
- Shortened ordinary decline and unanswered outgoing challenge cooldowns to reduce sparse-pool dead time.
- Added source-aware matchmaking cooldown metadata and target-band blocker logs.
- Added `legacy_unknown_cooldown_max_minutes: 360` to cap stale source-unknown cooldowns without deleting configured long blocks.
- Added `draw_cooldown_minutes: 30` for repeated drawn fast bot pairings.
- Added retry timing that waits until soon-expiring target-band cooldowns clear instead of always sleeping the full no-candidate interval.

### Draw And Repetition Handling

- Added `draw_or_resign.offer_draw_min_rating` and set the live floor to `3080`, so normal draw offers do not lock in below-target results.
- Added clock-edge draw-offer guards for bullet/blitz:
  - Current live `offer_draw_clock_advantage_opponent_ms: 45000`
  - Current live `offer_draw_clock_advantage_min_ms: 30000`
- Extended the same clock-edge guard to zero-WDL Lichess EGTB draw offers. This closes the path where tablebase equality could still offer a draw while the opponent was under practical bullet clock pressure.
- Added repetition guard clock-edge override so the bot can avoid repetition even against higher-rated opponents when the opponent is low on clock:
  - `repetition_guard.clock_advantage_override_opponent_ms: 40000`
  - `repetition_guard.clock_advantage_override_min_ms: 30000`
- Added `repetition_guard.avoid_opponent_immediate_claim: true` to filter moves that let the opponent immediately claim threefold, while preserving the score-loss cap.
- Enforced repetition root-move filters after engine search, so a returned move outside the allowed root set is replaced before play.
- Kept repetition avoidance score-bounded with `repetition_guard.max_score_loss_cp: 150`.

### Opening And Book Control

- Stopped relying on deep online opening explorer guidance for bot games. The live private config keeps online opening guidance disabled and uses the local Polyglot book.
- Fixed weighted-random book selection so `min_weight` filtering happens before sampling.
- Bot-vs-bot Polyglot profile currently uses `weighted_random`, `min_weight: 50`, `normalization: max`, `max_depth: 12`.
- Added bot-specific `avoid_moves` for repeated or losing book branches:
  - Skip `Bb5` after `e4 e5 Nf3 Nc6` to avoid repeated Berlin Wall draw channels.
  - Skip `Na5` after `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 Bb3 d6 c3 O-O h3` to sidestep the repeated Chigorin tabiya.
  - Skip `Ng5` after `e4 e5 Nf3 Nc6 Bc4 Nf6` to leave the Two Knights repetition channel.
  - Skip `b4` after `e4 e5 Nf3 Nc6 Bc4 Bc5` after `ezGWI9wS`; the live book then selects `c3`.

## Key Evidence From Recent Games

- `ezGWI9wS`: high-signal loss. White stayed in book through `e4 e5 Nf3 Nc6 Bc4 Bc5 b4 ... Bg5`; first engine search after book was about `-0.88` and `31.0%` winrate, and the bot lost `-5`. This led to the `b4` bot-book filter.
- `IBkQluUF` and `ol8VgVif`: repeated Two Knights `Ng5` family draws; led to the bot-book `Ng5` filter.
- `VT7zOio9` and related Ruy Lopez Chigorin draws: led to the Chigorin `Na5` sidestep.
- `Q1poOSgG`, `Wp8SbY5A`, `nSLk3U9v`: repeated Berlin Wall draw channels; led to the `Bb5` filter.
- `J7nJYTTZ` and `xzMGfX4n`: draw agreements/offers despite large clock edge; led to clock-aware draw-offer guards.
- `iCfhUIsj`: target-band bullet draw against `Cheszter` after Lichess EGTB returned `wdl: 0`; the bot offered a draw with about 52s vs 16s, showing EGTB-zero draw offers bypassed the normal draw clock guard. This led to the EGTB guard and the live 30s minimum clock-edge threshold.
- `UJlBX5Z5`: target-band bullet loss against `TakticproChess`. The book left the bot around `-0.51` / 43.6% after a Breyer line and later stayed around `-0.3` to `-0.5`; no narrow config fix has been applied because the signal is not yet specific enough.
- `nSLk3U9v` and `xUcwqJsv`: repetition with large clock edge; led to repetition clock override and opponent immediate-claim filtering.
- `o1u2AXZc`: showed hard repetition avoidance can choose losing alternatives; keep the score-loss cap.
- `KvLfR0la`: showed root-move filtering had to be enforced after search.

## Verification Already Run

Fresh verification from the EGTB-zero draw guard and 30s live draw-clock threshold:

```text
git diff --check: exit 0
19 passed in 0.46s
config.yml offer_draw_clock_advantage_opponent_ms=45000
config.yml offer_draw_clock_advantage_min_ms=30000
.config-history/config.yml offer_draw_clock_advantage_opponent_ms=45000
.config-history/config.yml offer_draw_clock_advantage_min_ms=30000
```

Targeted test command:

```bash
.venv/bin/python -m pytest \
  test_bot/test_external_moves.py::test_get_online_move__egtb_zero_respects_clock_edge \
  test_bot/test_engine_time_management.py::test_search__does_not_accept_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_engine_time_management.py::test_search__does_not_offer_normal_draw_when_opponent_is_near_flagging \
  test_bot/test_config.py \
  test_bot/test_external_moves.py::test_get_book_move__avoid_moves_filters_configured_san_line -q
```

Fresh verification from the final Evans branch change:

```text
config.yml avoided=b2b4 book_move=c2c3
.config-history/config.yml avoided=b2b4 book_move=c2c3
17 passed in 0.34s
git diff --check: exit 0
```

Targeted test command:

```bash
.venv/bin/python -m pytest test_bot/test_config.py \
  test_bot/test_external_moves.py::test_get_book_move__avoid_moves_filters_configured_san_line \
  test_bot/test_external_moves.py::test_get_book_move__weighted_random_respects_min_weight -q
```

Known verification debt is unchanged:

- Full `ruff` and `mypy` are still blocked by pre-existing complexity and typing failures documented in `docs/BOT_OPTIMIZATION_HISTORY.md`.
- No completed live game has yet validated the latest `b4 -> c3` replacement after the service restart.
- No completed live game has yet validated the EGTB-zero draw-offer guard or the new 30s draw-clock edge threshold.
- Avoid heavy local Stockfish experiments while the live bot is running.

## Next Best Work

- Watch the next `e4 e5 Nf3 Nc6 Bc4 Bc5 c3` bot game. If the first engine search is still materially negative, prefer a narrower branch change such as moving toward `O-O` or lowering bot book depth in that branch before changing global book randomness.
- Watch the next target-band equal EGTB ending. The bot should not offer a draw if the opponent is below 45s and the bot has at least a 30s clock edge.
- Keep `UJlBX5Z5` as evidence for possible Breyer/opening-depth tuning, but do not overfit it without another loss or repeated early negative first-search positions from the same family.
- Track whether the 3080 floor makes volume too sparse. If it does, prefer a temporary, explicitly logged `3060-3079` fallback window over permanently reopening 3000-3079.
- Keep using the target-band blocker logs to separate real pool scarcity from stale cooldowns, rate limits, and mode declines.
- Keep prioritizing losses and low-signal draws against bots over broad engine tuning.
- Clean up `engine_wrapper.py` complexity and fake-engine test typing before larger strategy changes.

## Useful Commands

Recent rated bullet/blitz games:

```bash
curl -fsSL -H 'Accept: application/x-ndjson' \
  'https://lichess.org/api/games/user/NeuroSoCute?max=30&rated=true&perfType=bullet,blitz&moves=true&pgnInJson=false&tags=true&clocks=true&evals=false&opening=true&sort=dateDesc' \
  | jq -r '[.id,.createdAt,.lastMoveAt,.speed,.status,(if .players.white.user.name=="NeuroSoCute" then "white" else "black" end),(.players.white.user.name),(.players.white.rating|tostring),(.players.white.ratingDiff|tostring),(.players.black.user.name),(.players.black.rating|tostring),(.players.black.ratingDiff|tostring),(.opening.name // ""),(.moves|split(" ")[0:60]|join(" "))] | @tsv'
```

Book check for the latest Evans sidestep:

```bash
.venv/bin/python - <<'PY'
import chess, chess.polyglot
from lib.config import load_config

cfg = load_config('config.yml')
book = cfg.engine.polyglot.book.standard[0]
board = chess.Board()
for san in 'e4 e5 Nf3 Nc6 Bc4 Bc5'.split():
    board.push_san(san)

with chess.polyglot.open_reader(book) as reader:
    print(sorted([(board.san(e.move), e.move.uci(), e.weight) for e in reader.find_all(board)], key=lambda x: x[2], reverse=True))
PY
```

Before restart:

```bash
ps -eo pid,ppid,lstart,cmd | rg 'lichess-bot.py|Stockfish/src/stockfish|stockfish'
tail -n 160 lichess_bot_auto_logs/run.log
```

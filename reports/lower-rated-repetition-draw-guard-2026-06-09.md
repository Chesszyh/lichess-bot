# 低分对手重复局面和棋保护

生成时间: 2026-06-09T02:02:43+08:00

## Problem Description

- 最新已完成对局 `YDxZJH1Q` 中，bot 执白对 `friendlybot_1700` 下成三次重复和棋。
- 对手赛前等级分 `3026`，本 bot 赛前等级分 `3030`，这是低分/近低分对手，和棋导致 `-1`。
- 对 3080 目标而言，此类可避免的低分和棋会拖低 bullet/blitz 稳定分。

## Environment and Scope

- 仓库：`/Users/chesszyh987/Develop/lichess-bot`
- 分支：`lc0+stockfish`
- 证据 PGN：`game_records/ilovecatgirl vs friendlybot_1700 - YDxZJH1Q.pgn`
- 运行日志：`lichess_bot_auto_logs/lichess-bot.log`
- 范围：只处理 rated bullet/blitz 中对不高于自身等级分 bot 的直接重复和棋风险。

## Symptoms and Reproduction

- PGN 解析显示 `YDxZJH1Q` 在 `60+1` rated bullet 中以 `1/2-1/2` 结束。
- 三次重复相关 ply：`65, 69, 71, 72`。
- 在 ply `69` 前，局面已有重复历史，走 `Kd2-e1` 会让对手立刻具备重复和棋路径。
- 同一局面仍有非重复合法着法，例如 `Ne2-f4`。

复现命令：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py::test_search__filters_repetition_draw_roots_against_lower_rated_bot -q'
```

## Investigation Timeline

- 检查最新 PGN，确认最近一局 `YDxZJH1Q` 是低分对手三次重复和棋。
- 用 `python-chess` 重放 PGN，确认关键局面不是唯一合法着法导致的强制和棋。
- 追踪 `EngineWrapper.search()`，确认当前搜索没有根据 rating/重复历史过滤 root moves。
- 确认已有 `last_search_score_cp` 可作为“不明显输棋时才拒绝重复和棋”的保守门槛。

## Root Cause

搜索入口只把 `root_moves` 原样传给引擎。引擎把重复和棋评估为接近 `0.00` 时，会自然选择重复着法；但在 rated bullet/blitz 中，对低分或同分对手主动进入可索和重复并不符合冲分目标。

根因不是 Lichess 提交逻辑，也不是 draw offer 配置；问题发生在引擎搜索候选着法集合没有排除会让低分对手立刻索和或强制三次重复的 root move。

## Changes Made

- 新增 `move_allows_threefold_claim()`，检测某个候选着法后是否会让下一方立即索和或强制三次重复。
- 新增 `EngineWrapper.should_avoid_repetition_draw()`：
  - 仅 rated `bullet`/`blitz`
  - 仅对手等级分不高于本 bot
  - 仅上一手搜索分数不低于 `-50cp`
- 新增 `EngineWrapper.root_moves_avoiding_repetition_draw()`，在满足条件时过滤重复和棋 root moves。
- 增加回归测试覆盖：
  - 低分对手时过滤 `Kd2-e1`
  - 高分对手时保留重复和棋可能
  - 上一手分数已经明显落后时保留重复和棋可能

## Verification

- RED：新增 `test_search__filters_repetition_draw_roots_against_lower_rated_bot` 后，测试失败于 `root_moves is None`。
- GREEN：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py::test_search__filters_repetition_draw_roots_against_lower_rated_bot test_bot/test_engine_time_management.py::test_search__allows_repetition_draw_roots_against_higher_rated_bot test_bot/test_engine_time_management.py::test_search__allows_repetition_draw_roots_when_score_is_losing -q && pytest test_bot/test_engine_time_management.py -q'
```

结果：

```text
3 passed, 4 warnings
37 passed, 4 warnings
```

## Problems Encountered During Debugging

- FEN 本身不包含重复历史，因此测试必须重放 `YDxZJH1Q` 的 move stack，而不能只用最终 FEN。
- `Board.can_claim_threefold_repetition()` 会检查下一方是否可通过合法着法索和；这里故意使用该行为，因为目标是阻断对手下一手立刻进入重复索和。

## Reuse Notes and Lessons

- 后续遇到低分和棋，应先区分“强制和棋”和“候选着法未过滤导致的可避免重复”。
- 如果出现输棋局面，不应盲目拒绝重复和棋；当前 `-50cp` 门槛就是为避免把可守和局面变成败局。
- 若未来要调参，优先从 `REPETITION_AVOID_MIN_SCORE_CP` 和 rating 条件入手，而不是扩大到所有对手。

## Appendix: Reusable Commands

查看最近 PGN：

```bash
rtk ls -lt game_records | sed -n '1,20p'
```

重放 PGN 检查重复：

```bash
rtk sh -c '. .venv/bin/activate && python - <<'"'"'PY'"'"'
import chess.pgn
from pathlib import Path
path = Path("game_records/ilovecatgirl vs friendlybot_1700 - YDxZJH1Q.pgn")
with path.open(encoding="utf-8") as handle:
    game = chess.pgn.read_game(handle)
board = game.board()
for ply, node in enumerate(game.mainline(), start=1):
    board.push(node.move)
    if board.can_claim_threefold_repetition() or board.is_repetition(3):
        print(ply, board.fen())
PY'
```

运行 focused gate：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py -q && git diff --check'
```

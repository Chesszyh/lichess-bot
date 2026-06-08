# 高分对手时钟压力和棋接受

生成时间: 2026-06-09T02:16:06+08:00

## Problem Description

- 最新已完成对局 `54fzm4bM` 中，bot 执白对 `RaspFish` 下成和棋，结果为 `+1`。
- 对手赛前等级分 `3075`，本 bot 赛前等级分 `3029`；这是高分 bot 对手，但低于本地配置的 `high_rated_accept_draw_min_rating: 3100`。
- 对手在稳定接近均势的残局中先提出和棋；本 bot 当时时钟已低于 `10s`，但因为对手未达到绝对 `3100` 门槛而继续拒绝，直到后续 EGTB `wdl: 0` 主动提和才结束。

## Environment and Scope

- 仓库：`/Users/chesszyh987/Develop/lichess-bot`
- 分支：`lc0+stockfish`
- 证据 PGN：`/Users/chesszyh987/Develop/lichess-bot/game_records/ilovecatgirl vs RaspFish - 54fzm4bM.pgn`
- 运行日志：`/Users/chesszyh987/Develop/lichess-bot/lichess_bot_auto_logs/lichess-bot.log`
- 范围：只调整 incoming draw offer 的接受条件；不改变普通主动提和规则，也不放宽低分对手和棋出口。

## Symptoms and Reproduction

- PGN 头部显示：
  - `Event: rated bullet game`
  - `WhiteElo: 3029`
  - `BlackElo: 3075`
  - `TimeControl: 60+1`
  - `Result: 1/2-1/2`
- 日志关键窗口：
  - `02:05:39`：`Black offers draw`
  - `02:05:39`：搜索显示 `wtime 9459 btime 21850`
  - `02:05:40`：`White declines draw`
  - `02:05:52`：Lichess EGTB 返回 `f3f4`，`wdl: 0`
  - `02:05:52`：本 bot `offeringDraw=true`，随后 `Draw offer accepted`

复现回归测试：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py::test_search__accepts_higher_rated_draw_offer_when_bot_is_in_clock_pressure -q'
```

## Investigation Timeline

- 检查 `54fzm4bM` PGN，确认这是 rated bullet `60+1`，对手 `RaspFish` 为高分 bot。
- 检查运行日志，确认对手先提和时本 bot 只有约 `9.5s`，对手约 `21.9s`。
- 追踪 `EngineWrapper.offer_draw_or_resign()`，发现 incoming high-rated draw 规则只允许 `opponent_rating >= high_rated_accept_draw_min_rating`。
- 对照本地配置，`high_rated_accept_draw_min_rating` 为 `3100`，因此 `3075` 的高分 bot 不符合接受条件。
- 新增 RED 测试后，确认当前行为失败于 `result.draw_offered == False`。

## Root Cause

根因是 high-rated incoming draw 规则只有“绝对高分门槛”，没有“相对高分 + 本 bot 时钟压力”的保守路径。`RaspFish` 相对本 bot 高 `46` 分，局面稳定接近均势，本 bot 时钟已进入关键区间，但 `3075 < 3100` 导致 draw offer 被拒绝。

这不是 EGTB 或提交移动逻辑问题；同一局后续 EGTB 已确认 `wdl: 0` 并能成功提和，说明问题发生在 engine search 后处理的 incoming draw acceptance predicate。

## Changes Made

- `lib/engine_wrapper.py`
  - 拆出时钟压力辅助函数，统一读取本方/对方剩余时间和阈值。
  - 保留原有“对手低时钟、本方安全时拒绝高分提和”的保护。
  - 新增相对高分 bot 时钟压力接受路径：
    - 仅 incoming draw offer
    - 仅 rated `bullet`/`blitz`
    - 仅 bot 对手
    - 仅对手等级分严格高于本 bot
    - 仅本方时钟低于等于 own threshold，且对方时钟高于 opponent threshold
    - 仍要求最近评分稳定接近均势、棋子数满足阈值
- `lib/config.py`
  - 为旧配置补齐 `high_rated_accept_draw_clock_pressure_*` 的运行时默认值。
  - 顺手包装一个已存在的超长 `set_config_default()` 行，避免 touched file lint 失败。
- `config.yml.default`
  - 更新 clock-pressure 注释，避免只描述“拒绝对手低时钟提和”的旧语义。
- `test_bot/test_engine_time_management.py`
  - 增加 `54fzm4bM` 对应的 RED/GREEN 回归测试。
- `test_bot/test_config.py`
  - 增加旧配置补齐 clock-pressure 默认值的测试。

## Verification

RED：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py::test_search__accepts_higher_rated_draw_offer_when_bot_is_in_clock_pressure -q'
```

结果：`1 failed`，失败于 `assert result.draw_offered`。

配置 RED：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_config.py::test_insert_default_values__adds_high_rated_draw_clock_pressure_defaults -q'
```

结果：`1 failed`，失败于缺少 `high_rated_accept_draw_clock_pressure_enabled`。

GREEN / focused gate：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py test_bot/test_config.py -q && git diff --check && ruff check --config test_bot/ruff.toml lib/engine_wrapper.py lib/config.py test_bot/test_engine_time_management.py test_bot/test_config.py --select E,F && mypy --strict lib/config.py'
```

结果：

```text
54 passed, 4 warnings
All checks passed!
Success: no issues found in 1 source file
```

## Problems Encountered During Debugging

- `rtk date --iso-8601=seconds` 在 macOS 上不可用，改用 `rtk date -Iseconds`。
- 广泛搜索 `Black offers draw` 会命中其他对局，最终改为截取 `54fzm4bM` 附近日志窗口。
- 对 changed-paths 运行 `mypy --strict` 会暴露仓库已有测试 fake/override 类型债务；本次只对新增 config 默认值路径运行了干净的 `mypy --strict lib/config.py`，并用 focused tests 覆盖 engine 行为。

## Reuse Notes and Lessons

- 高分对手和棋策略需要区分“绝对高分”和“相对高分”：冲分目标下，相对高分 bot 在稳定均势且本方低时钟时接受和棋是正期望防守。
- 不应把该规则扩展到低分对手；低分/同分 bot 的 draw exit 仍应保持严格。
- 复盘 draw-offer 问题时同时看三类证据：PGN rating/time control、日志中的 `draw_offered` 状态、提交移动时的 `offeringDraw` 参数。

## Appendix: Reusable Commands

检查当前是否有活跃对局：

```bash
rtk sh -c '. .venv/bin/activate && python - <<'"'"'PY'"'"'
import json, urllib.request, yaml
with open("config.yml", "r", encoding="utf-8") as config_file:
    token = yaml.safe_load(config_file)["token"]
request = urllib.request.Request(
    "https://lichess.org/api/account/playing",
    headers={"Authorization": "Bearer " + token},
)
with urllib.request.urlopen(request, timeout=15) as response:
    games = json.load(response).get("nowPlaying", [])
print(f"active_count={len(games)}")
for game in games:
    print("game_id=%s speed=%s rated=%s" % (
        game.get("gameId") or game.get("fullId") or game.get("id"),
        game.get("speed"),
        game.get("rated"),
    ))
PY'
```

查看 `54fzm4bM` draw-offer 日志窗口：

```bash
rtk sed -n '29145,29230p' lichess_bot_auto_logs/lichess-bot.log
rtk sed -n '29430,29452p' lichess_bot_auto_logs/lichess-bot.log
```

运行 focused gate：

```bash
rtk sh -c '. .venv/bin/activate && pytest test_bot/test_engine_time_management.py test_bot/test_config.py -q && git diff --check'
```

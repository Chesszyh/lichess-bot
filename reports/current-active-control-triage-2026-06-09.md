# 当前 active-control 证据复盘

生成时间: 2026-06-09T02:44:58+08:00

## 1. Problem Description

目标是继续把 `ilovecatgirl` 的 bullet/blitz bot-vs-bot 表现推向稳定 3080。本轮复盘关注最新本地 PGN 和运行日志，判断上一轮部署后是否出现新的可行动弱点，避免在没有证据时继续叠加配置或代码风险。

## 2. Environment and Scope

- 仓库：`/Users/chesszyh987/Develop/lichess-bot`
- 分支：`lc0+stockfish`
- 最新提交：`02a97c0 Extend tactical guard against stronger bots`
- 运行进程：LaunchAgent `org.chesszyh987.lichess-bot`，PID `4463`
- 分析范围：本地 `game_records/*.pgn`、`lichess_bot_auto_logs/run.log`，不做本地引擎大规模搜索。

## 3. Symptoms and Reproduction

没有发现上一轮 `02a97c0` 部署后的新 PGN。最新一盘仍是部署前的：

- `game_records/ilovecatgirl vs Cheszter - HY97jjD2.pgn`
- UTC：`2026.06.08 18:28:21`
- rated bullet `120+1`
- 对手 `Cheszter` 约 `3106`
- 结果 `1/2-1/2`，我方评分 `+1`

02:43 本地时间触发下一次 matchmaking，但 `abdcebot` 未应答：

- `2026-06-09 02:43:38` 创建 challenge `pIOlPpav`
- `2026-06-09 02:44:06` 记录 `Will not challenge abdcebot again for 12 hours after an unanswered outgoing challenge.`
- `2026-06-09 02:44:07` 取消 challenge，下一次 challenge 计划在 `02:54:06`

## 4. Investigation Timeline

1. 检查 git 状态：工作区只有已知未跟踪路径，没有未提交代码改动。
2. 检查 LaunchAgent 和日志：bot 正常运行，处于 watchdog/matchmaking 空闲状态。
3. 生成 `reports/bot-game-analysis-active-controls-since-2026-06-08-1500.md`：最近 10 盘 active-control rated bullet/blitz 中，总评分 `+9`，唯一负面项是已处理的 `MznBGMQZ` 和 `YDxZJH1Q`。
4. 扩大到 `reports/bot-game-analysis-active-controls-since-2026-06-08-1100.md`：较早的 `Fischer_Bot` / `MEGA-NOOB-BOT` 损失均已在 block list 中，且相关时钟压力 cap 在这些 PGN 之后才部署。
5. 等待 02:43 matchmaking 窗口：bot 挑战 `abdcebot`，但对手未应答，无新 PGN 可分析。

## 5. Root Cause

本轮没有确认新的对弈弱点。当前可见负面 PGN 分为三类：

- `MznBGMQZ`：深度 11 战术漏算，已由 `02a97c0` 增加高分 BOT 浅搜阈值处理。
- `YDxZJH1Q`：低分/负分重复和棋，已由 `08783ea` 的重复和棋 root 过滤处理。
- `Fischer_Bot` / `MEGA-NOOB-BOT` 旧损失：发生在对应 clock-pressure cap / block-list 策略前，当前也已从 actionable watchlist 中隐藏。

因此本轮正确动作是保留证据、等待新 post-deploy PGN，而不是基于旧样本继续调参。

## 6. Changes Made

- 新增 active-control 分析报告：
  - `reports/bot-game-analysis-active-controls-since-2026-06-08-1500.md`
  - `reports/bot-game-analysis-active-controls-since-2026-06-08-1100.md`
- 新增本摘要：
  - `reports/current-active-control-triage-2026-06-09.md`
- 未修改运行代码或私有配置。

## 7. Verification

执行过的轻量命令：

```bash
rtk .venv/bin/python scripts/analyze_bot_games.py --records-dir game_records --bot ilovecatgirl --since-utc 2026-06-08T15:00:00Z --speeds bullet,blitz --modes rated --time-controls 60+1,90+1,120+1,180+3,240+2,300+3 --focus-time-controls 60+1,90+1,120+1 --block-list-config config.yml --output reports/bot-game-analysis-active-controls-since-2026-06-08-1500.md
```

结果：`10` 盘，rating `+9`，active-control 负面项只剩已处理样本。

```bash
rtk .venv/bin/python scripts/analyze_bot_games.py --records-dir game_records --bot ilovecatgirl --since-utc 2026-06-08T11:00:00Z --speeds bullet --modes rated --time-controls 60+1,90+1,120+1 --focus-time-controls 60+1,90+1,120+1 --block-list-config config.yml --output reports/bot-game-analysis-active-controls-since-2026-06-08-1100.md
```

结果：`15` 盘，旧损失被区分为已 block 或已由后续 clock/depth/repetition 策略覆盖。

## 8. Problems Encountered During Debugging

- 第一次手写 Python heredoc 时被 shell 引号破坏；后续直接用 `.venv/bin/python` 避免激活脚本和 heredoc 的嵌套 quoting 问题。
- `scripts/analyze_bot_games.py` 直接执行时缺少 `chess` 依赖；必须使用 repo venv。
- 当前没有 post-`02a97c0` 对局 PGN，无法证明最新高分 BOT 浅搜 guard 的线上收益，只能确认没有新的线上反例。

## 9. Reuse Notes and Lessons

- 每次部署后优先分析 post-deploy PGN；没有新 PGN 时不要用旧样本继续叠加补丁。
- `--block-list-config config.yml` 很重要，否则报告会把已屏蔽对手继续列为 actionable。
- 旧损失是否还能代表当前问题，必须和提交时间线对齐。

## 10. Appendix: Reusable Commands

查看最新 PGN 头部：

```bash
rtk .venv/bin/python - <<'PY'
import chess.pgn
from pathlib import Path
paths = sorted(Path('game_records').glob('*.pgn'), key=lambda path: path.stat().st_mtime, reverse=True)[:20]
for path in paths:
    with path.open(encoding='utf-8') as handle:
        game = chess.pgn.read_game(handle)
    if not game:
        continue
    headers = game.headers
    print(path.name, headers.get('UTCDate'), headers.get('UTCTime'), headers.get('Result'), headers.get('WhiteRatingDiff'), headers.get('BlackRatingDiff'))
PY
```

检查下次 matchmaking 事件：

```bash
rtk sh -c 'tail -n 160 lichess_bot_auto_logs/run.log'
```

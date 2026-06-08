# lichess-bot Loss Analysis

基于 `game_records/*.pgn` 与 `lichess_bot_auto_logs/run.log` 的交叉分析。
说明：这里的“原因”是最像的主因，不是法律意义上的唯一因果。旧局包含旧配置阶段（如开启 Syzygy、旧版对局流处理）。

- 败局总数：**77**
- 终局方式：{'Normal': 43, 'Time forfeit': 34}
- 主因统计：
  - 整体被更强引擎压制: 37
  - 重复启动/事件流 bug 导致超时: 18
  - 均势局面纯掉时: 11
  - 中盘败着: 4
  - 优势/可下局面纯掉时: 3
  - 开局/早中盘败着: 1
  - 残局败着: 1
  - 略劣局面掉时: 1
  - 对局流异常后超时: 1

## 逐盘

- `2026-04-14 06:52:47` `WfQW5piN` vs `Chesszyh` `60+0` `white` `Time forfeit`
  开局：Modern Defense: Standard Line
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=3；终局评估 +583；PGN: `game_records/ilovecatgirl vs Chesszyh - WfQW5piN.pgn`
- `2026-04-14 07:09:36` `Qq7RihQK` vs `Chesszyh` `60+0` `white` `Time forfeit`
  开局：Modern Defense: Standard Line
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=7；终局评估 +281；PGN: `game_records/ilovecatgirl vs Chesszyh - Qq7RihQK.pgn`
- `2026-04-14 09:03:14` `gWACwMkn` vs `abcd_engine` `60+0` `black` `Normal`
  开局：Scandinavian Defense: Valencian Variation, Ilundain Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：duplicate_start_logs=2；终局评估 mate-lost；PGN: `game_records/abcd_engine vs ilovecatgirl - gWACwMkn.pgn`
- `2026-04-14 09:38:00` `2bpImqoX` vs `CloudNetBot` `60+0` `black` `Normal`
  开局：Caro-Kann Defense: Two Knights Attack
  主因：开局/早中盘败着。5 回合 g8f6 把评估从 -53 打到 mate-lost，属于开局/早中盘走崩。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - 2bpImqoX.pgn`
- `2026-04-14 10:06:52` `97yq32Jv` vs `DarkOnBot` `120+1` `black` `Normal`
  开局：French Defense: Rubinstein Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - 97yq32Jv.pgn`
- `2026-04-14 10:15:10` `I7d7o1Z7` vs `Cheszter` `60+0` `white` `Normal`
  开局：Nimzo-Larsen Attack: Indian Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs Cheszter - I7d7o1Z7.pgn`
- `2026-04-14 10:31:06` `FUrZXki0` vs `bot1e` `60+0` `black` `Normal`
  开局：Owen Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/bot1e vs ilovecatgirl - FUrZXki0.pgn`
- `2026-04-14 11:38:23` `zgbUIQX3` vs `Cheszter` `60+0` `black` `Normal`
  开局：Zukertort Opening
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Cheszter vs ilovecatgirl - zgbUIQX3.pgn`
- `2026-04-14 11:42:10` `B3afaf6d` vs `Cheszter` `120+0` `black` `Normal`
  开局：Ruy Lopez: Steinitz Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Cheszter vs ilovecatgirl - B3afaf6d.pgn`
- `2026-04-14 12:47:17` `hsNmrqpM` vs `Fischer_Bot` `120+1` `black` `Normal`
  开局：Sicilian Defense: Scheveningen Variation, Keres Attack
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Fischer_Bot vs ilovecatgirl - hsNmrqpM.pgn`
- `2026-04-14 14:19:18` `6QKMxWQ6` vs `BorkaTower` `60+0` `white` `Time forfeit`
  开局：Queen's Pawn Game: Veresov, Richter Attack
  主因：均势局面纯掉时。大致均势（终局评估 0），主因是时间分配。
  附加信号：-；终局评估 0；PGN: `game_records/ilovecatgirl vs BorkaTower - 6QKMxWQ6.pgn`
- `2026-04-15 06:36:41` `yxoZcdPT` vs `TakticproChess` `120+1` `white` `Normal`
  开局：Queen's Gambit Declined: Traditional Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs TakticproChess - yxoZcdPT.pgn`
- `2026-04-15 07:41:29` `g6cJXfgh` vs `MDBOT` `60+1` `black` `Normal`
  开局：Scandinavian Defense: Modern Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/MDBOT vs ilovecatgirl - g6cJXfgh.pgn`
- `2026-04-15 14:32:05` `acAezKqI` vs `RockingSuperstars` `60+1` `white` `Normal`
  开局：Scotch Game: Mieses Variation
  主因：中盘败着。21 回合 h2h3 把评估从 +59 打到 mate-lost，属于中盘败着。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs RockingSuperstars - acAezKqI.pgn`
- `2026-04-15 14:45:29` `gla85tmy` vs `RockingSuperstars` `60+0` `white` `Normal`
  开局：Indian Defense
  主因：中盘败着。30 回合 f1d2 把评估从 -108 打到 -378，属于中盘败着。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs RockingSuperstars - gla85tmy.pgn`
- `2026-04-15 15:43:47` `WsrVL0wc` vs `abhisun_bot` `120+1` `black` `Normal`
  开局：Caro-Kann Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/abhisun_bot vs ilovecatgirl - WsrVL0wc.pgn`
- `2026-04-15 15:56:46` `AGsU5EQB` vs `abhisun_bot` `120+0` `black` `Normal`
  开局：Caro-Kann Defense: Advance Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/abhisun_bot vs ilovecatgirl - AGsU5EQB.pgn`
- `2026-04-15 18:35:21` `T2PtNmvB` vs `simbelmyne-bot` `60+0` `white` `Normal`
  开局：Ruy Lopez: Closed, Averbakh Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs simbelmyne-bot - T2PtNmvB.pgn`
- `2026-04-15 18:47:51` `MyIMxFM3` vs `BorkaTower` `60+1` `black` `Normal`
  开局：Sicilian Defense: Prins Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/BorkaTower vs ilovecatgirl - MyIMxFM3.pgn`
- `2026-04-15 20:15:11` `MjV1YYHt` vs `pawn_git` `120+0` `black` `Normal`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/pawn_git vs ilovecatgirl - MjV1YYHt.pgn`
- `2026-04-16 06:35:53` `tL4IFy6A` vs `SF_Bot1nok` `120+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/SF_Bot1nok vs ilovecatgirl - tL4IFy6A.pgn`
- `2026-04-16 07:11:58` `uzkXLscd` vs `DarkOnBot` `60+1` `black` `Normal`
  开局：Queen's Pawn Game: London System
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - uzkXLscd.pgn`
- `2026-04-16 07:20:37` `FRB64zn6` vs `abdcebot` `60+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：残局败着。41 回合 f4f3 把评估从 -130 打到 -411，属于残局败着。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/abdcebot vs ilovecatgirl - FRB64zn6.pgn`
- `2026-04-16 07:29:23` `hJM7q4ll` vs `duchessAI` `120+0` `black` `Normal`
  开局：Sicilian Defense: Modern Variations
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/duchessAI vs ilovecatgirl - hJM7q4ll.pgn`
- `2026-04-16 07:41:06` `0D9rqw9h` vs `bot1e` `60+1` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/bot1e vs ilovecatgirl - 0D9rqw9h.pgn`
- `2026-04-16 07:45:38` `PH6wN37D` vs `CloudNetBot` `120+0` `black` `Normal`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - PH6wN37D.pgn`
- `2026-04-16 08:00:02` `wi9hRV1A` vs `DarkOnBot` `60+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：中盘败着。30 回合 e3e4 把评估从 +384 打到 -322，属于中盘败着。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - wi9hRV1A.pgn`
- `2026-04-16 08:23:45` `0Rnepta1` vs `DarkOnBot` `60+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - 0Rnepta1.pgn`
- `2026-04-16 08:48:10` `e4jWw4eD` vs `CloudNetBot` `120+0` `white` `Normal`
  开局：Ruy Lopez: Closed, Zaitsev System
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs CloudNetBot - e4jWw4eD.pgn`
- `2026-04-16 08:55:16` `JXNc9ERc` vs `DarkOnBot` `120+0` `black` `Normal`
  开局：Semi-Slav Defense: Chigorin Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - JXNc9ERc.pgn`
- `2026-04-16 09:15:54` `aNxPW999` vs `DarkOnBot` `120+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - aNxPW999.pgn`
- `2026-04-16 09:37:37` `dnft2mwL` vs `DarkOnBot` `60+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/DarkOnBot vs ilovecatgirl - dnft2mwL.pgn`
- `2026-04-16 10:11:03` `bF2TstZV` vs `CloudNetBot` `60+0` `black` `Normal`
  开局：English Opening: Anglo-Indian Defense, King's Knight Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - bF2TstZV.pgn`
- `2026-04-16 10:16:48` `rwQvKECY` vs `CloudNetBot` `120+0` `black` `Normal`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - rwQvKECY.pgn`
- `2026-04-16 10:47:39` `BLZr1CQ0` vs `CloudNetBot` `60+0` `white` `Normal`
  开局：Ruy Lopez: Berlin Defense, l'Hermet Variation, Berlin Wall Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs CloudNetBot - BLZr1CQ0.pgn`
- `2026-04-16 10:59:10` `oz8LxsIo` vs `CloudNetBot` `120+0` `black` `Normal`
  开局：Sicilian Defense: Closed
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - oz8LxsIo.pgn`
- `2026-04-16 11:07:19` `AmX1ztAe` vs `CloudNetBot` `120+1` `white` `Normal`
  开局：Ruy Lopez: Marshall Attack, Modern Main Line
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs CloudNetBot - AmX1ztAe.pgn`
- `2026-04-16 11:20:43` `qaj0rCxZ` vs `CloudNetBot` `120+0` `white` `Normal`
  开局：Ruy Lopez: Berlin Defense, l'Hermet Variation, Berlin Wall Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs CloudNetBot - qaj0rCxZ.pgn`
- `2026-04-16 12:08:07` `Po1l3xhG` vs `prokopakop` `60+0` `white` `Normal`
  开局：Ruy Lopez: Closed, Chigorin Defense
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs prokopakop - Po1l3xhG.pgn`
- `2026-04-16 17:52:21` `rvpRi5Z1` vs `Chesszyh` `60+0` `black` `Normal`
  开局：Nimzo-Indian Defense: Normal Variation, Gligoric System
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Chesszyh vs ilovecatgirl - rvpRi5Z1.pgn`
- `2026-04-17 03:50:52` `qbsKlR3F` vs `Chesszyh` `60+0` `black` `Normal`
  开局：Mieses Opening: Reversed Rat
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Chesszyh vs ilovecatgirl - qbsKlR3F.pgn`
- `2026-04-17 12:47:47` `yP08VPxR` vs `grail-bot` `60+0` `white` `Time forfeit`
  开局：French Defense: Steinitz Variation, Boleslavsky Variation
  主因：优势/可下局面纯掉时。局面并不差（终局评估 +242），主因是时间分配。
  附加信号：-；终局评估 +242；PGN: `game_records/ilovecatgirl vs grail-bot - yP08VPxR.pgn`
- `2026-04-18 07:03:04` `dtKhwWkj` vs `Fischer_Bot` `120+0` `black` `Normal`
  开局：Sicilian Defense: Najdorf Variation, Opocensky Variation
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/Fischer_Bot vs ilovecatgirl - dtKhwWkj.pgn`
- `2026-04-18 08:52:19` `vA46oJ7M` vs `BorkaTower` `60+2` `black` `Time forfeit`
  开局：Rapport-Jobava System
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 0；PGN: `game_records/BorkaTower vs ilovecatgirl - vA46oJ7M.pgn`
- `2026-04-18 08:58:36` `w1SoZlnY` vs `simbelmyne-bot` `60+0` `black` `Time forfeit`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +34；PGN: `game_records/simbelmyne-bot vs ilovecatgirl - w1SoZlnY.pgn`
- `2026-04-18 09:28:19` `f2VRDFpP` vs `bot_adario` `240+1` `white` `Time forfeit`
  开局：Ruy Lopez: Marshall Attack
  主因：优势/可下局面纯掉时。局面并不差（终局评估 +330），主因是时间分配。
  附加信号：-；终局评估 +330；PGN: `game_records/ilovecatgirl vs bot_adario - f2VRDFpP.pgn`
- `2026-04-18 09:38:11` `a5T94EC5` vs `DarkOnBot` `180+2` `white` `Time forfeit`
  开局：Ruy Lopez: Berlin Defense, Berlin Wall
  主因：均势局面纯掉时。大致均势（终局评估 0），主因是时间分配。
  附加信号：-；终局评估 0；PGN: `game_records/ilovecatgirl vs DarkOnBot - a5T94EC5.pgn`
- `2026-04-18 09:48:20` `01XLwuzl` vs `SF_Bot1nok` `180+2` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +22；PGN: `game_records/SF_Bot1nok vs ilovecatgirl - 01XLwuzl.pgn`
- `2026-04-18 10:02:43` `allwigmJ` vs `abcd_engine` `180+0` `black` `Time forfeit`
  开局：Catalan Opening: Open Defense, Modern Sharp Variation
  主因：均势局面纯掉时。大致均势（终局评估 -30），主因是时间分配。
  附加信号：-；终局评估 -30；PGN: `game_records/abcd_engine vs ilovecatgirl - allwigmJ.pgn`
- `2026-04-18 10:27:29` `ReQcTIPK` vs `SoloBot` `240+2` `white` `Time forfeit`
  开局：French Defense: Winawer Variation, Warsaw Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +632；PGN: `game_records/ilovecatgirl vs SoloBot - ReQcTIPK.pgn`
- `2026-04-18 10:44:35` `U0cxy4QG` vs `duchessAI` `60+0` `white` `Time forfeit`
  开局：French Defense: Rubinstein Variation, Blackburne Defense
  主因：均势局面纯掉时。大致均势（终局评估 +16），主因是时间分配。
  附加信号：-；终局评估 +16；PGN: `game_records/ilovecatgirl vs duchessAI - U0cxy4QG.pgn`
- `2026-04-18 11:48:34` `b6B9rXdo` vs `PeachFruit` `90+0` `white` `Time forfeit`
  开局：Sicilian Defense: Lasker-Pelikan Variation, Sveshnikov Variation, Chelyabinsk Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +705；PGN: `game_records/ilovecatgirl vs PeachFruit - b6B9rXdo.pgn`
- `2026-04-18 14:44:23` `hhWhuvhJ` vs `Weiawaga` `60+2` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：均势局面纯掉时。大致均势（终局评估 0），主因是时间分配。
  附加信号：-；终局评估 0；PGN: `game_records/Weiawaga vs ilovecatgirl - hhWhuvhJ.pgn`
- `2026-04-19 06:46:40` `lya0el3l` vs `Ctrl_Alt_Destroy` `30+0` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, Poisoned Pawn Variation
  主因：均势局面纯掉时。大致均势（终局评估 -29），主因是时间分配。
  附加信号：-；终局评估 -29；PGN: `game_records/Ctrl_Alt_Destroy vs ilovecatgirl - lya0el3l.pgn`
- `2026-04-19 08:06:24` `rLIfn4PV` vs `Worst-ai` `240+0` `black` `Time forfeit`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 0；PGN: `game_records/Worst-ai vs ilovecatgirl - rLIfn4PV.pgn`
- `2026-04-19 08:56:00` `F52MoWDL` vs `PeachFruit` `240+0` `white` `Time forfeit`
  开局：Ruy Lopez: Closed, Karpov Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +589；PGN: `game_records/ilovecatgirl vs PeachFruit - F52MoWDL.pgn`
- `2026-04-19 09:17:28` `8mUWUtnH` vs `abcd_engine` `60+0` `white` `Time forfeit`
  开局：Ruy Lopez: Berlin Defense, Berlin Wall
  主因：略劣局面掉时。局面略差（终局评估 -199），但直接死因仍是掉时。
  附加信号：-；终局评估 -199；PGN: `game_records/ilovecatgirl vs abcd_engine - 8mUWUtnH.pgn`
- `2026-04-19 10:44:49` `NLi2dFL4` vs `CloudNetBot` `240+2` `black` `Normal`
  开局：Sicilian Defense: Delayed Alapin Variation, Basman-Palatnik Double Gambit
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - NLi2dFL4.pgn`
- `2026-04-19 11:26:12` `5AGHTY3D` vs `CloudNetBot` `60+0` `black` `Time forfeit`
  开局：Sicilian Defense: Moscow Variation, Main Line
  主因：均势局面纯掉时。大致均势（终局评估 0），主因是时间分配。
  附加信号：-；终局评估 0；PGN: `game_records/CloudNetBot vs ilovecatgirl - 5AGHTY3D.pgn`
- `2026-04-19 12:41:20` `ZgPSiaJO` vs `ChessatronBot` `120+2` `black` `Time forfeit`
  开局：Sicilian Defense: Smith-Morra Gambit Accepted, Scheveningen Formation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +185；PGN: `game_records/ChessatronBot vs ilovecatgirl - ZgPSiaJO.pgn`
- `2026-04-19 13:37:27` `sz469X3f` vs `CloudNetBot` `240+0` `black` `Normal`
  开局：Sicilian Defense: Delayed Alapin Variation, Basman-Palatnik Double Gambit
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/CloudNetBot vs ilovecatgirl - sz469X3f.pgn`
- `2026-04-20 08:33:22` `BjLeqnju` vs `bot64jaques` `240+2` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +522；PGN: `game_records/bot64jaques vs ilovecatgirl - BjLeqnju.pgn`
- `2026-04-20 09:36:44` `Mc0JDs9S` vs `Worst-ai` `240+2` `white` `Time forfeit`
  开局：Sicilian Defense: Lasker-Pelikan Variation, Sveshnikov Variation, Chelyabinsk Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +83；PGN: `game_records/ilovecatgirl vs Worst-ai - Mc0JDs9S.pgn`
- `2026-04-20 09:47:04` `3aGbkTv9` vs `grail-bot` `240+0` `white` `Time forfeit`
  开局：French Defense: Steinitz Variation, Boleslavsky Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=3；终局评估 mate-win；PGN: `game_records/ilovecatgirl vs grail-bot - 3aGbkTv9.pgn`
- `2026-04-20 11:12:23` `b285okET` vs `ToromBot` `60+0` `black` `Normal`
  开局：Queen's Pawn Game: London System
  主因：整体被更强引擎压制。没有找到单一决定性败着，整体是被更强引擎持续压制到败势。
  附加信号：-；终局评估 mate-lost；PGN: `game_records/ToromBot vs ilovecatgirl - b285okET.pgn`
- `2026-04-20 13:17:09` `ZUY3Bd5a` vs `bot_adario` `120+2` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, Poisoned Pawn Variation
  主因：均势局面纯掉时。大致均势（终局评估 +118），主因是时间分配。
  附加信号：-；终局评估 +118；PGN: `game_records/bot_adario vs ilovecatgirl - ZUY3Bd5a.pgn`
- `2026-04-21 07:54:09` `URpXZ3Sr` vs `Eichkatzerl` `90+2` `black` `Time forfeit`
  开局：Sicilian Defense: Modern Variations
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=3；终局评估 +229；PGN: `game_records/Eichkatzerl vs ilovecatgirl - URpXZ3Sr.pgn`
- `2026-04-21 08:30:39` `J8DBwV2o` vs `CloudNetBot` `60+2` `black` `Time forfeit`
  开局：Sicilian Defense: Modern Variations
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 -9；PGN: `game_records/CloudNetBot vs ilovecatgirl - J8DBwV2o.pgn`
- `2026-04-21 08:36:49` `bW9dmdgA` vs `DarkOnBot` `120+2` `white` `Time forfeit`
  开局：Ruy Lopez: Marshall Attack, Modern Main Line
  主因：均势局面纯掉时。大致均势（终局评估 0），主因是时间分配。
  附加信号：-；终局评估 0；PGN: `game_records/ilovecatgirl vs DarkOnBot - bW9dmdgA.pgn`
- `2026-04-21 09:45:19` `EYiU3jst` vs `grail-bot` `240+2` `white` `Time forfeit`
  开局：French Defense: Steinitz Variation, Boleslavsky Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +486；PGN: `game_records/ilovecatgirl vs grail-bot - EYiU3jst.pgn`
- `2026-04-21 11:55:14` `yaCbwGWQ` vs `simbelmyne-bot` `120+2` `white` `Time forfeit`
  开局：Philidor Defense: Exchange Variation
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +639；PGN: `game_records/ilovecatgirl vs simbelmyne-bot - yaCbwGWQ.pgn`
- `2026-04-21 12:47:32` `61Tlv0gL` vs `bot64jaques` `90+0` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：重复启动/事件流 bug 导致超时。旧版重复 gameStart/重复 worker 路径导致的超时。
  附加信号：duplicate_start_logs=2；终局评估 +426；PGN: `game_records/bot64jaques vs ilovecatgirl - 61Tlv0gL.pgn`
- `2026-04-21 14:48:39` `3u8v1bS7` vs `bot64jaques` `240+2` `black` `Time forfeit`
  开局：Queen's Gambit Declined: Orthodox Defense, Rubinstein Attack
  主因：优势/可下局面纯掉时。局面并不差（终局评估 +420），主因是时间分配。
  附加信号：-；终局评估 +420；PGN: `game_records/bot64jaques vs ilovecatgirl - 3u8v1bS7.pgn`
- `2026-04-22 07:36:05` `piLZJK8Y` vs `DarkOnBot` `90+2` `white` `Time forfeit`
  开局：Carr Defense
  主因：均势局面纯掉时。大致均势（终局评估 +51），主因是时间分配。
  附加信号：-；终局评估 +51；PGN: `game_records/ilovecatgirl vs DarkOnBot - piLZJK8Y.pgn`
- `2026-04-22 08:31:22` `W5e6TFeo` vs `Weiawaga` `90+2` `black` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：均势局面纯掉时。大致均势（终局评估 -3），主因是时间分配。
  附加信号：-；终局评估 -3；PGN: `game_records/Weiawaga vs ilovecatgirl - W5e6TFeo.pgn`
- `2026-04-22 09:13:15` `rLpy9U8U` vs `simbelmyne-bot` `240+1` `white` `Normal`
  开局：Ruy Lopez: Marshall Attack
  主因：中盘败着。30 回合 e3c5 把评估从 +413 打到 -4，属于中盘败着。
  附加信号：stream_errors=32, duplicate_start_logs=3；终局评估 mate-lost；PGN: `game_records/ilovecatgirl vs simbelmyne-bot - rLpy9U8U.pgn`
- `2026-04-22 09:48:57` `9OV1RR96` vs `nebubot` `90+2` `white` `Time forfeit`
  开局：Sicilian Defense: Najdorf Variation, English Attack
  主因：对局流异常后超时。对局流异常重连 14 次，最后超时。
  附加信号：stream_errors=14, duplicate_start_logs=2；终局评估 +282；PGN: `game_records/ilovecatgirl vs nebubot - 9OV1RR96.pgn`

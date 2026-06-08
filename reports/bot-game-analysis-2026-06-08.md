# Bot Game Analysis for ilovecatgirl

## Scope

- Games analyzed: `2354`
- Results: `{'draw': 1397, 'loss': 465, 'unknown': 45, 'win': 447}`
- Opening risk gate: FAILED (66 >= 3)
- No local engine analysis was run.

## Loss Openings

- `66` x Sicilian Defense: Najdorf Variation, English Attack
- `24` x Caro-Kann Defense: Advance Variation, Short Variation
- `10` x Ruy Lopez: Berlin Defense, Berlin Wall
- `9` x French Defense: Steinitz Variation, Boleslavsky Variation
- `8` x Sicilian Defense: Moscow Variation, Main Line
- `8` x Semi-Slav Defense
- `8` x Caro-Kann Defense: Advance Variation
- `7` x Queen's Pawn Game: London System
- `7` x Sicilian Defense: Nyezhmetdinov-Rossolimo Attack
- `7` x Sicilian Defense: Najdorf Variation

## Results by Speed

- `1128` x blitz draw
- `386` x blitz loss
- `269` x bullet draw
- `242` x bullet win
- `205` x blitz win
- `79` x bullet loss
- `31` x blitz unknown
- `14` x bullet unknown

## Results by Time Control

- `197` x 180+2 draw
- `161` x 240+2 draw
- `143` x 300+2 draw
- `113` x 300+3 draw
- `103` x 180+3 draw
- `100` x 240+3 draw
- `96` x 180+0 loss
- `90` x 180+1 draw
- `58` x 180+0 draw
- `57` x 180+2 loss

## Worst Scoring Controls

- `180+0 black`: W-D-L `8-26-51`, score `24.7%` over `85` games
- `180+0 white`: W-D-L `12-32-45`, score `31.5%` over `89` games
- `300+2 black`: W-D-L `2-60-36`, score `32.7%` over `98` games
- `180+3 black`: W-D-L `3-34-19`, score `35.7%` over `56` games
- `180+2 black`: W-D-L `10-87-47`, score `37.2%` over `144` games
- `240+2 black`: W-D-L `12-68-40`, score `38.3%` over `120` games
- `180+1 black`: W-D-L `11-41-27`, score `39.9%` over `79` games
- `300+3 black`: W-D-L `4-40-16`, score `40.0%` over `60` games
- `300+1 black`: W-D-L `1-23-7`, score `40.3%` over `31` games
- `240+3 black`: W-D-L `1-36-10`, score `40.4%` over `47` games

## Loss Colors

- `330` x black
- `135` x white

## Loss Terminations

- `333` x Normal
- `132` x Time forfeit

## Time Forfeit Loss Controls

- `27` x 180+0 white
- `22` x 180+0 black
- `10` x 180+1 black
- `5` x 180+2 black
- `5` x 60+0 white
- `5` x 240+0 white
- `5` x 240+2 white
- `4` x 120+2 black
- `4` x 180+1 white
- `3` x 60+2 black

## Loss Prefixes

- `58` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5`
- `15` x `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6`
- `14` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Bg5 e6`
- `13` x `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5`
- `7` x `e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 Nd7 O-O Bg6`
- `7` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 Nc6 Bg5 e6`
- `7` x `e4 e6 d4 d5 Nc3 Nf6 e5 Nfd7 f4 c5 Nf3 Nc6`
- `5` x `d4 Nf6 Nf3 d5 Bf4 c5 e3 Nc6 Nbd2 Qb6 dxc5 Qxb2`
- `5` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 h3 e6`
- `5` x `e4 c5 Nf3 d6 Nc3 Nf6 d4 cxd4 Nxd4 a6 Be3 e5`

## Loss Prefix Contexts

- `23` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | blitz | Normal`
- `13` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | bullet | Normal`
- `7` x `e4 c6 d4 d5 e5 Bf5 Nf3 e6 Be2 Nd7 O-O Bg6 | black | blitz | Normal`
- `7` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 Nc6 Bg5 e6 | black | blitz | Normal`
- `7` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | blitz | Time forfeit`
- `6` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Bg5 e6 | black | blitz | Normal`
- `6` x `e4 e5 Nf3 Nc6 Bb5 a6 Ba4 Nf6 O-O Be7 Re1 b5 | white | blitz | Normal`
- `6` x `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 | white | blitz | Time forfeit`
- `6` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | white | blitz | Time forfeit`
- `5` x `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 | white | blitz | Normal`

## Lower-Rated Draws

- Lower-rated draws found: `247`

## Lower-Rated Draw Openings

- `25` x Sicilian Defense: Najdorf Variation, English Attack
- `12` x Sicilian Defense: Najdorf Variation
- `9` x Catalan Opening: Open Defense, Modern Sharp Variation
- `8` x Sicilian Defense: Lasker-Pelikan Variation, Sveshnikov Variation, Chelyabinsk Variation
- `6` x Semi-Slav Defense: Meran Variation, Wade Variation
- `6` x Semi-Slav Defense: Chigorin Defense
- `6` x Semi-Slav Defense
- `6` x Ruy Lopez: Berlin Defense, l'Hermet Variation, Berlin Wall Defense
- `4` x Sicilian Defense: Closed
- `4` x Catalan Opening: Open Defense, Classical Line

## Lower-Rated Draw Prefixes

- `22` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5`
- `8` x `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6`
- `7` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 f3 e5`
- `4` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Bd3 e5`
- `4` x `e4 c5 Nf3 e6 d4 cxd4 Nxd4 Nf6 Nc3 Nc6 Ndb5 d6`
- `3` x `d4 Nf6 Nf3 d5 c4 e6 Nc3 c6 e3 Nbd7 Bd3 dxc4`
- `3` x `d4 Nf6 c4 e6 g3 d5 Nf3 dxc4 Bg2 Nc6 Qa4 Bb4+`
- `3` x `d4 Nf6 Nf3 d5 c4 e6 Nc3 c6 Bg5 Be7 e3 Nbd7`
- `3` x `e4 c5 Nc3 d6 f4 Nc6 Nf3 g6 d4 cxd4 Nxd4 Bg7`
- `3` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Bg5 e6`

## Lower-Rated Draw Contexts

- `5` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 f3 e5 | black | blitz | 180+2`
- `3` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | white | blitz | 240+1`
- `2` x `d4 Nf6 c4 e6 g3 d5 Nf3 dxc4 Bg2 Nc6 Qa4 Bb4+ | black | blitz | 180+1`
- `2` x `d4 Nf6 Nf3 d5 c4 e6 Nc3 c6 Bg5 Be7 e3 Nbd7 | black | blitz | 180+2`
- `2` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | bullet | 60+1`
- `2` x `e4 c5 Nc3 d6 f4 Nc6 Nf3 g6 d4 cxd4 Nxd4 Bg7 | black | blitz | 180+2`
- `2` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | blitz | 240+0`
- `2` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Be3 e5 | black | bullet | 90+0`
- `2` x `e4 e5 Nf3 Nc6 Bb5 Nf6 O-O Nxe4 d4 Nd6 Bxc6 dxc6 | white | blitz | 180+2`
- `2` x `e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6 Bd3 e5 | black | bullet | 60+0`

## Largest Lower-Rated Draw Gaps

- gap `576` vs `GNUPassant` (2330) in `ilovecatgirl vs GNUPassant - Cdt4VUHk.pgn`: Caro-Kann Defense: Advance Variation, Short Variation
- gap `561` vs `PeachFruit` (2381) in `ilovecatgirl vs PeachFruit - aD2Tfss0.pgn`: Sicilian Defense: Taimanov Variation, Bastrikov Variation
- gap `528` vs `PeachFruit` (2360) in `PeachFruit vs ilovecatgirl - nWc2j90j.pgn`: Catalan Opening: Open Defense, Modern Sharp Variation
- gap `483` vs `SoloBot` (2508) in `SoloBot vs ilovecatgirl - ke35DrrS.pgn`: Sicilian Defense: Moscow Variation, Main Line
- gap `478` vs `simbelmyne-bot` (2578) in `simbelmyne-bot vs ilovecatgirl - 0kLqYVhg.pgn`: Sicilian Defense: Moscow Variation, Main Line
- gap `472` vs `Eichkatzerl` (2426) in `Eichkatzerl vs ilovecatgirl - 42ytSeFu.pgn`: Sicilian Defense: Sozin Attack
- gap `450` vs `prokopakop` (2525) in `prokopakop vs ilovecatgirl - TQr2RUE6.pgn`: Sicilian Defense: Najdorf Variation, English Attack
- gap `429` vs `prokopakop` (2510) in `ilovecatgirl vs prokopakop - FfzXRpyW.pgn`: Ruy Lopez: Closed, Smyslov Defense
- gap `427` vs `prokopakop` (2513) in `prokopakop vs ilovecatgirl - SO2bW34b.pgn`: Sicilian Defense: Najdorf Variation
- gap `419` vs `prokopakop` (2511) in `prokopakop vs ilovecatgirl - ZnbOQOsf.pgn`: Sicilian Defense: Najdorf Variation

## Recent Losses

- `2026-06-08 10:16:53+00:00` `ilovecatgirl vs abcd_engine - 2QVD5cp2.pgn` vs `abcd_engine`: Nimzo-Indian Defense: Normal Variation, Classical Defense
- `2026-06-08 08:51:21+00:00` `ArasanX vs ilovecatgirl - CNjERGD9.pgn` vs `ArasanX`: Sicilian Defense: Najdorf Variation, English Attack
- `2026-06-08 08:05:00+00:00` `TakticproChess vs ilovecatgirl - cArqfmSd.pgn` vs `TakticproChess`: Semi-Slav Defense
- `2026-06-07 23:01:40+00:00` `TakticproChess vs ilovecatgirl - fLBNC4KL.pgn` vs `TakticproChess`: Sicilian Defense: Najdorf Variation, English Attack
- `2026-06-07 20:07:10+00:00` `SimonEricAfonso vs ilovecatgirl - WUJo1fC0.pgn` vs `SimonEricAfonso`: Semi-Slav Defense
- `2026-06-07 19:21:11+00:00` `suniferia vs ilovecatgirl - Cgxa3C6t.pgn` vs `suniferia`: Sicilian Defense: Najdorf Variation, Adams Attack
- `2026-06-07 18:39:20+00:00` `suniferia vs ilovecatgirl - GxAtiN96.pgn` vs `suniferia`: Sicilian Defense: Najdorf Variation, English Attack
- `2026-06-07 17:29:47+00:00` `CupchessBot vs ilovecatgirl - x4Cr3jad.pgn` vs `CupchessBot`: Sicilian Defense: Najdorf Variation, Zagreb Variation
- `2026-06-07 16:05:57+00:00` `ilovecatgirl vs suniferia - 2Yrx6U31.pgn` vs `suniferia`: Caro-Kann Defense: Advance Variation, Short Variation
- `2026-06-07 13:40:13+00:00` `rascal1 vs ilovecatgirl - wHib2C1q.pgn` vs `rascal1`: Sicilian Defense: Moscow Variation, Sokolsky Variation

# Bullet Clock-Pressure Threshold Triage

## Scope

- Game: `21mY5MXC`
- Record: `game_records/CupchessBot vs ilovecatgirl - 21mY5MXC.pgn`
- Control: rated bullet `90+1`
- Bot color: black
- Opponent: `CupchessBot`, `3064`
- Result: loss, `-6`

## Evidence

- Runtime was idle before investigation: LaunchAgent PID `4463`, `active_count=0`.
- The post-depth-guard analysis found one new game and one new loss since `02a97c0`.
- Largest bot eval drops in the generated analysis were after `Ke8`, `fxg5`, and `Qxh8`.
- The game log repeatedly capped Black to exact `2000 ms` while White was under `10s` and Black still had roughly `17s` to `24s`.
- Representative logged snapshots:
  - `w=9050 b=24029 -> cap=2000`
  - `w=5100 b=21309 -> cap=2000`
  - `w=3560 b=17729 -> cap=2000`

## Root Cause

The existing clock-pressure movetime rule already protects positions where the opponent is near flagging, but the configured own-clock gate was too high for this `90+1` game:

- Previous local setting: `clock_pressure_own_clock_threshold_ms: 30000`
- Opponent pressure setting: `clock_pressure_opponent_clock_threshold_ms: 10000`
- Pressure movetime setting: `clock_pressure_movetime_ms: 6000`
- Low-clock exact cap: `low_clock_threshold_ms: 25000`, `low_clock_ms: 2000`

With Black at `17s` to `24s`, the pressure rule never fired, so the low-clock exact cap forced `2000 ms` despite the opponent being under `10s`.

## Change

Updated ignored local runtime configuration and its private mirror:

- `config.yml`: `clock_pressure_own_clock_threshold_ms` from `30000` to `15000`
- `.config-history/config.yml`: mirrored the same threshold

This keeps the change scoped to opponent-low-clock bullet positions and does not broadly increase all low-clock move caps.

## Validation

A config-backed probe of representative `21mY5MXC` snapshots now returns the intended exact pressure movetime:

- `w=9050 b=24029 -> time=6.0`
- `w=5100 b=21309 -> time=6.0`
- `w=3560 b=17729 -> time=6.0`
- `w=7430 b=23559 -> time=6.0`
- `w=12000 b=14900 -> time=2.0`

The final snapshot confirms that the bot still falls back to the existing low-clock cap below the new `15000 ms` own-clock gate.

## Deployment Note

Because `config.yml` is ignored and loaded by the LaunchAgent at process start, a safe restart is required before the running bot uses the new threshold. Restart only after confirming:

- no active OS-level bot game handling conflict,
- recent log tail is not mid-game,
- `/api/account/playing` returns `active_count=0`.

# Blitz Matchmaking Probe

## Scope

- Objective: keep improving both bullet and blitz bot-vs-bot performance toward `3080`.
- Runtime config files changed locally:
  - `config.yml`
  - `.config-history/config.yml`
- Tracked code changed: none.

## Evidence

- The active local matchmaking config was only selecting bullet-style controls:
  - `challenge_initial_time`: repeated `60`, `90`, and `120`
  - `challenge_increment`: only `1`
- Recent post-threshold evidence contained one fresh rated bullet game:
  - `oi6DonOy` vs `Cheszter`, rated bullet `90+1`, draw, `+2`
- No fresh post-threshold blitz games existed, so the current setup could not produce the blitz evidence required by the objective.
- `engine.blitz_time_management.enabled` is already `true`, so blitz-specific time-management config is available once matchmaking creates blitz games.

## Change

Added one local matchmaking override:

```yaml
matchmaking:
  overrides:
    blitz_probe:
      challenge_initial_time:
      - 180
      - 240
      - 300
      challenge_increment:
      - 2
      - 3
      challenge_days:
      - null
```

The existing default bullet pool remains unchanged. With one override plus the default path, the matcher can now sample blitz controls while still preserving bullet coverage.

## Validation

- Parsed both local runtime config files successfully.
- Confirmed `blitz_probe.challenge_initial_time == [180, 240, 300]`.
- Confirmed `blitz_probe.challenge_increment == [2, 3]`.
- Confirmed `blitz_probe.challenge_days == [None]`.

## Deployment Note

Because `config.yml` is ignored and read at startup, the LaunchAgent must be restarted while idle before the new override affects matchmaking. Restart must only happen after checking:

- no active game in `/api/account/playing`,
- no mid-game log tail,
- LaunchAgent process is running and idle.

## Post-Restart Samples

- `04:15:54`: `blitz_probe` selected rated `240+3` as black against `BlueMoonBot`; the outgoing challenge was not accepted and was canceled.
- `04:26:30`: `blitz_probe` selected rated `240+3` as black against `Void_Bot`; the game was aborted before any move because White was inactive, so it gives no playing-strength evidence.
- `04:36:56`: `blitz_probe` selected rated `180+2` as white against `CupchessBot` (`3025`); game `Q3bzjLhX` ended as a normal draw by agreement with bot rating diff `+1`.
- The refreshed fast aggregate now has blitz at `+0` rating over `13` scored games, while bullet remains `-37` over `21` scored games.

## Current Decision

- No runtime config change from these samples.
- The `180+2` draw is positive evidence for keeping the blitz probe active.
- The sample is not enough to drop bullet probing yet, because the separate white-book mitigation still needs fresh post-restart bullet games.

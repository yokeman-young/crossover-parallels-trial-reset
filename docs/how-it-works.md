# How it works

## Two shapes of a trial

**Timestamp trials** (CrossOver)

```
FirstRunDate     = first run
SULastCheckTime  = last update check
remaining        ≈ trial_days − (today − FirstRunDate)
```

Nothing server-side; shifting both dates back makes the client compute a fresh window. This is
why a pre-launch reset is immediately effective and no network layer is needed.

**Licence-blob trials** (Parallels)

```
com.parallels.Parallels Desktop.plist
  License.Flags / License.Params.*     ← licence type and parameters
  WiConfig = { mode = "trial" }
```

The client reads these via `prl_disp_service`, caches parsed state in
`~/Library/Preferences/Parallels/*`, and may contact account/licence endpoints. Resetting means
deleting the keys, clearing caches, and restarting the service so nothing is served from memory.

## Why ordering matters

```
launch → read state → decide trial → write prefs
```

A reset triggered by a file watcher fires *after* the read, so it benefits the **next** launch.
A launcher that resets before opening guarantees the current launch. The kit ships both:
`launch` (deterministic) and `watch` (safety net).

## Why processes must be killed

`prl_disp_service` holds licence state in memory and writes it back. Editing prefs while it runs
can be overwritten. CrossOver is lighter but still caches; the kit kills declared `procs` before
touching prefs.

## The network layer

For licence-blob trials, the vendor can return an authoritative verdict. Blocking
`account.* / my.* / licensing.* / activation.* / pcs.*` at DNS level means the client cannot
obtain one and falls back to local state. This does not change what the vendor already knows; it
only prevents the verdict from being written into local cache.

Escalation path when hosts blocking is bypassed: PF rule → local MITM (observe/ replay) →
binary patch of the root daemon (last resort, highest cost).

## Backups and state

```
~/.trialreset/<app>/backup/    prefs copies, one per day, keep 10
~/.trialreset/<app>/last-reset epoch
~/.trialreset/<app>/version    app version at last reset (update detection)
~/.trialreset/<app>/disabled   sentinel: skip all resets (after buying a licence)
```

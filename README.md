# crossover-parallels-trial-reset

Reset the local trial state of **CrossOver** and **Parallels Desktop** on macOS before they launch,
with a generic adapter layer, a launchd watcher and an agent-executable skill.

> `pip install -e .` → `trialreset`

Reset the local trial/licence state of macOS desktop apps **before they launch**, with a
launchd watcher as a safety net and optional network blocking for account/licence checks.

Adapters included: **CrossOver**, **Parallels Desktop**. Adding an app is one small spec file.

![status](https://img.shields.io/badge/platform-macOS-lightgrey) ![python](https://img.shields.io/badge/python-3.9%2B-blue)

## How it works

```
launcher (optional)         launchd agent (optional)
      │ reset before launch        │ reset after app writes prefs
      ▼                            ▼
            trialreset reset <app>
      ┌──────────────┬───────────────┬────────────────┐
      │ delete/shift │ kill procs    │ clear caches    │ block endpoints
      │ prefs keys   │ (so service   │ (stale licence  │ (account/licence
      │              │  re-reads)    │  cache)         │  domains → 0.0.0.0)
      └──────────────┴───────────────┴────────────────┘
```

Two trial models are covered:

| Model | Example | Reset action |
| --- | --- | --- |
| timestamp | CrossOver (`FirstRunDate`, `SULastCheckTime`) | shift dates back N hours |
| licence blob | Parallels (`License.*`, `WiConfig`) | delete keys, clear caches, restart service |

See [docs/how-it-works.md](docs/how-it-works.md) for the mechanics and
[docs/pitfalls.md](docs/pitfalls.md) for the traps (Automation prompts, agents that kill live
sessions, IPv6 name cache, cfprefsd).

## Install

```bash
git clone https://github.com/yokeman-young/crossover-parallels-trial-reset.git
cd trial-reset-kit
python3 -m venv .venv && . .venv/bin/activate
pip install -e .
trialreset --json doctor
```

macOS only; no third-party dependencies.

## Usage

```bash
trialreset list                                   # adapters, install state, running state
trialreset check parallels                        # prefs keys, version, processes
trialreset reset parallels --dry-run              # show the plan, change nothing
trialreset reset parallels                        # backup → kill → delete keys → clear caches
trialreset launch parallels                       # reset if not running, then open
trialreset watch install parallels                # launchd WatchPaths agent
trialreset block parallels                        # add /etc/hosts entries (asks for sudo)
trialreset block parallels --unblock              # remove them
```

Every command accepts `--json` and prints exactly one JSON document. Exit codes: `0` ok,
`1` verification failure, `2` app missing/unsupported.

### Launcher app (reset before launch)

```bash
./scripts/build-launcher.sh parallels
# → ~/Applications/Parallels (Trial Reset).app
```

The launcher runs `trialreset launch <key>` (no compiler at runtime; the Swift stub is tiny).

### Watcher (safety net)

`trialreset watch install <app>` writes `~/Library/LaunchAgents/local.trialreset.<app>.plist`
watching the preference plist and the app's `Info.plist`. The watcher runs with `--quiet` and
**skips while the app is running**, so it cannot kill a live session.

## Adding an app

Create `trialreset/adapters/myapp.py`:

```python
from .base import AppSpec

SPEC = AppSpec(
    key="myapp",
    name="My App",
    bundle_id="com.example.myapp",
    app_paths=["/Applications/My App.app"],
    procs=["My App.app/Contents/MacOS/MyApp"],
    domain="com.example.myapp",
    delete_key_prefixes=["Trial."],          # or shift_datetime_keys={"FirstRun": 3}
    caches=["~/Library/Caches/com.example.myapp/*"],
    watch_paths=["~/Library/Preferences/com.example.myapp.plist"],
    domains=["licence.example.com"],
)
```

Register it in `trialreset/adapters/__init__.py`. Then `trialreset list` shows it.

Step-by-step in [docs/adding-an-app.md](docs/adding-an-app.md).

## Agent skill

`skills/trial-reset/SKILL.md` is a ready-to-install skill (frontmatter + procedure + assertion
table + failure map). Install with `cp -R skills/trial-reset ~/.claude/skills/` (or
`~/.dsh/skills/`), see [docs/skills.md](docs/skills.md).

## For agents

`AGENTS.md` is the contract (JSON surface, exit codes, assertion table, failure modes).
Recipes in [docs/agent-usage.md](docs/agent-usage.md).

## Limitations

- Parallels may validate trials server-side; blocking endpoints prevents an authoritative
  verdict, but does not change what the vendor already knows.
- Deleting licence keys also removes a **purchased** activation. Set
  `~/.trialreset/<app>/disabled` to disable resetting after you buy a licence.
- Hosts blocking only covers name resolution; hard-coded IPs need a PF rule (documented).
- macOS only. The adapter layer is deliberately thin so other platforms can be added later.

## Disclaimer

For local interoperability testing on machines you own. No vendor binaries are redistributed.

MIT licensed.

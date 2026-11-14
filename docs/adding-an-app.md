# Adding an app

## 1. Find where the state lives

```bash
defaults read com.example.myapp | grep -Ei 'trial|licen[cs]e|expire|firstrun|lastcheck'
ls ~/Library/Preferences | grep -i myapp
ls ~/Library/Caches | grep -i myapp
lsof -p $(pgrep -f MyApp | head -1) | grep -i prefs
```

Two outcomes:

- date keys → `shift_datetime_keys={"FirstRunDate": 3}`
- blob keys → `delete_key_prefixes=["License.", "Trial."]`

## 2. Write the spec

`trialreset/adapters/myapp.py`:

```python
from .base import AppSpec

SPEC = AppSpec(
    key="myapp",
    name="My App",
    bundle_id="com.example.myapp",
    app_paths=["/Applications/My App.app"],
    procs=["My App.app/Contents/MacOS/MyApp", "myapp_helper"],
    domain="com.example.myapp",
    delete_key_prefixes=["License."],
    caches=["~/Library/Preferences/MyApp/*", "~/Library/Caches/com.example.myapp/*"],
    domains=["licensing.example.com"],
    watch_paths=["~/Library/Preferences/com.example.myapp.plist"],
)
```

Register it in `trialreset/adapters/__init__.py`:

```python
from .myapp import SPEC as MYAPP
SPECS = {s.key: s for s in (CROSSOVER, PARALLELS, MYAPP)}
```

## 3. Validate

```bash
trialreset --json list
trialreset reset myapp --dry-run          # plan only
trialreset check myapp                    # keys currently present
trialreset reset myapp --force            # backup + apply
trialreset launch myapp                   # reset then open
```

## 4. Add a test

`tests/test_core.py`: assert the plan deletes/shifts the expected keys for a synthetic snapshot.
No app install required — `plan_reset` is pure.

## 5. Document limits

If the vendor tracks the trial server-side, say so in the adapter `notes` and add the endpoints
to `domains`. The kit's `block` only prevents the client from receiving a verdict.

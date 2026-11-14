"""Adapter contract: a small data spec plus optional overrides.

Adding an application means adding one module with an `AppSpec` instance to
`trialreset/adapters/__init__.py`. Everything else (CLI, watch agent, doctor,
blocking) is generic and works off the spec.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppSpec:
    key: str                      # CLI name, e.g. "crossover"
    name: str                     # human label
    bundle_id: str | None         # macOS bundle identifier; None for portable builds
    app_paths: list[str]          # fallbacks, ~ expanded
    procs: list[str] = field(default_factory=list)      # pkill -f patterns
    domain: str | None = None                            # macOS preference domain
    delete_key_prefixes: list[str] = field(default_factory=list)
    shift_datetime_keys: dict[str, int] = field(default_factory=dict)  # key -> hours back
    caches: list[str] = field(default_factory=list)      # glob patterns to clear
    domains: list[str] = field(default_factory=list)     # network endpoints to block
    watch_paths: list[str] = field(default_factory=list) # paths watched by the agent
    platform: str = "darwin"
    notes: str = ""

    def prefs_path(self) -> str | None:
        if not self.domain:
            return None
        return f"~/Library/Preferences/{self.domain}.plist"

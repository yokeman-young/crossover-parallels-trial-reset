"""Platform-agnostic helpers: preference snapshots, backups, process control."""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import plistlib
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Iterable


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, (proc.stdout or proc.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


def read_defaults(domain: str) -> dict:
    """Snapshot a macOS preference domain as a dict (empty when missing)."""
    code, out = run(["defaults", "export", domain, "-"])
    if code != 0 or not out:
        return {}
    try:
        data = plistlib.loads(out.encode("utf-8", "replace"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_datetime(domain: str, key: str, value: _dt.datetime) -> bool:
    stamp = value.strftime("%Y-%m-%dT%H:%M:%SZ")
    code, _ = run(["defaults", "write", domain, key, "-date", stamp])
    return code == 0


def delete_key(domain: str, key: str) -> bool:
    code, _ = run(["defaults", "delete", domain, key])
    return code == 0


def kill_processes(patterns: Iterable[str], dry_run: bool = False) -> list[str]:
    killed = []
    for pattern in patterns:
        code, _ = run(["pgrep", "-f", pattern])
        if code != 0:
            continue
        if dry_run:
            killed.append(pattern)
            continue
        run(["pkill", "-f", pattern])
        killed.append(pattern)
    return killed


def backup_prefs(prefs_path: str, backup_dir: str, keep: int = 10) -> str | None:
    if not prefs_path or not os.path.exists(prefs_path):
        return None
    os.makedirs(backup_dir, exist_ok=True)
    stamp = _dt.date.today().strftime("%Y%m%d")
    target = os.path.join(backup_dir, f"{os.path.basename(prefs_path)}.{stamp}")
    if not os.path.exists(target):
        shutil.copy2(prefs_path, target)
    backups = sorted(glob.glob(os.path.join(backup_dir, f"{os.path.basename(prefs_path)}.*")), reverse=True)
    for stale in backups[keep:]:
        os.remove(stale)
    return target


def locate_app(spec) -> str | None:
    """Resolve an app bundle by id, then by known paths."""
    if spec.bundle_id:
        code, out = run(["mdfind", f"kMDItemCFBundleIdentifier == '{spec.bundle_id}'"])
        if code == 0:
            for line in out.splitlines():
                if line.strip().endswith(".app"):
                    return line.strip()
    for path in spec.app_paths:
        expanded = os.path.expanduser(path)
        if os.path.isdir(expanded):
            return expanded
    return None


def app_version(app: str | None) -> str | None:
    if not app:
        return None
    plist = os.path.join(app, "Contents", "Info.plist")
    code, out = run(["/usr/libexec/PlistBuddy", "-c", "Print CFBundleShortVersionString", plist])
    return out if code == 0 else None


@dataclass
class Plan:
    """Pure description of what a reset would do — testable without side effects."""
    app: str | None
    delete_keys: list[str] = field(default_factory=list)
    set_dates: dict[str, str] = field(default_factory=dict)
    kill: list[str] = field(default_factory=list)
    caches: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "app": self.app,
            "delete_keys": self.delete_keys,
            "set_dates": self.set_dates,
            "kill": self.kill,
            "caches": self.caches,
            "warnings": self.warnings,
        }


def plan_reset(spec, snapshot: dict, now: _dt.datetime | None = None) -> Plan:
    """Decide which keys to delete / shift from a preference snapshot."""
    now = now or _dt.datetime.utcnow()
    plan = Plan(app=locate_app(spec))
    for key in snapshot:
        if spec.delete_key_prefixes and any(key.startswith(p) for p in spec.delete_key_prefixes):
            plan.delete_keys.append(key)
    for key, hours in (spec.shift_datetime_keys or {}).items():
        plan.set_dates[key] = (now - _dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    plan.kill = list(spec.procs)
    plan.caches = expand_caches(spec.caches)
    if not plan.delete_keys and not plan.set_dates:
        plan.warnings.append("no matching preference keys found (schema changed?)")
    return plan


def expand_caches(patterns: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        paths.extend(glob.glob(os.path.expanduser(pattern)))
    return paths


def mask_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)

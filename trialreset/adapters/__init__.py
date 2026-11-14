"""Adapter registry. Import a spec here to make it available to the CLI."""
from .base import AppSpec
from .crossover import SPEC as CROSSOVER
from .parallels import SPEC as PARALLELS

SPECS: dict[str, AppSpec] = {spec.key: spec for spec in (CROSSOVER, PARALLELS)}


def get(key: str) -> AppSpec:
    try:
        return SPECS[key]
    except KeyError:
        raise SystemExit(f"unknown app '{key}'; known: {', '.join(sorted(SPECS))}")

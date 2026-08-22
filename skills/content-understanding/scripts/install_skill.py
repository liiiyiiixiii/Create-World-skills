#!/usr/bin/env python3
"""Compare or copy this skill into a Codex skills directory."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {"__pycache__", ".pytest_cache", "output"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def default_target() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    root = Path(codex_home).expanduser() if codex_home else Path.home() / ".codex"
    return root / "skills" / "content-understanding"


def source_files() -> list[Path]:
    return sorted(
        path
        for path in SKILL_ROOT.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.parts)
        and path.suffix not in IGNORED_SUFFIXES
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changes(target: Path) -> list[tuple[Path, Path, str]]:
    result = []
    for source in source_files():
        relative = source.relative_to(SKILL_ROOT)
        destination = target / relative
        if not destination.exists():
            state = "add"
        elif digest(source) != digest(destination):
            state = "update"
        else:
            state = "same"
        result.append((source, destination, state))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=default_target())
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update", action="store_true", help="Apply additions and updates")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target = args.target.expanduser().resolve()
    source_root = SKILL_ROOT.resolve()
    if target == source_root or source_root in target.parents:
        print("ERROR: target must not be the source skill directory or its child")
        return 2
    plan = changes(target)
    changed = [item for item in plan if item[2] != "same"]
    for source, destination, state in plan:
        if state != "same":
            print(f"{state.upper()}: {source.relative_to(source_root)} -> {destination}")
    if not changed:
        print(f"OK: {target} already matches the source files")
        return 0
    if args.dry_run or not args.update:
        print(f"DRY RUN: {len(changed)} file(s) would change; pass --update to apply")
        return 0
    for source, destination, state in changed:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    remaining = [item for item in changes(target) if item[2] != "same"]
    if remaining:
        print("ERROR: target verification failed")
        return 1
    print(f"OK: synchronized {len(changed)} file(s) to {target}")
    print("NOTE: target-only extra files were not deleted")
    return 0


if __name__ == "__main__":
    sys.exit(main())


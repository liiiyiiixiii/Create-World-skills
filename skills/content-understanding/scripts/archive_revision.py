#!/usr/bin/env python3
"""Validate and archive the current revision, then render CHANGELOG.md."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

from validate_structure import load_yaml, validate_data


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_changelog(data: dict) -> str:
    lines = [f"# 《{data['work']['title']}》修订记录", ""]
    history = sorted(data["metadata"]["revision_history"], key=lambda item: item["revision"])
    for entry in history:
        lines += [
            f"## r{entry['revision']:04d} · {entry['generated_at']}",
            "",
            entry["summary"],
            "",
            f"- 影响ID：{'、'.join(entry['affected_ids']) if entry['affected_ids'] else '无'}",
            "",
        ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.structure.resolve()
    data = load_yaml(source)
    result = validate_data(data)
    for message in result.errors:
        print(f"ERROR: {message}")
    for message in result.warnings:
        print(f"WARNING: {message}")
    if result.errors:
        return 1
    revision = data["metadata"]["revision"]
    if revision < 2:
        print("ERROR: revision archives start at r0002")
        return 2
    revisions_dir = source.parent / "revisions"
    snapshot = revisions_dir / f"r{revision:04d}.yaml"
    if snapshot.exists() and digest(snapshot) != digest(source):
        print(f"ERROR: {snapshot} already exists with different content")
        return 3
    revisions_dir.mkdir(parents=True, exist_ok=True)
    if not snapshot.exists():
        shutil.copy2(source, snapshot)
    changelog = source.parent / "CHANGELOG.md"
    changelog.write_text(render_changelog(data), encoding="utf-8")
    print(f"WROTE: {snapshot}")
    print(f"WROTE: {changelog}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


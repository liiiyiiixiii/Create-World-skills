#!/usr/bin/env python3
"""Validate Content Understanding structure.yaml files (schema 2.0)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = SKILL_ROOT / "references" / "structure-v2.schema.json"
ID_PATTERN = re.compile(r"^(SRC|SEG|N|CL|NF|CHR|EL|SP|GAP|UNIT)-[0-9]{3,}$")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_text(parts: Iterable[Any]) -> str:
    text = "$"
    for part in parts:
        text += f"[{part}]" if isinstance(part, int) else f".{part}"
    return text


def _schema_validation(data: dict[str, Any], schema_path: Path) -> list[str]:
    validator = Draft202012Validator(load_schema(schema_path), format_checker=FormatChecker())
    return [
        f"{_path_text(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path))
    ]


def _all_ids(data: dict[str, Any]) -> tuple[dict[str, set[str]], list[str]]:
    collections = {
        "SRC": data.get("sources", []),
        "SEG": data.get("segments", []),
        "N": data.get("nodes", []),
        "CL": data.get("causal_links", []),
        "NF": data.get("notable_fragments", []),
        "CHR": data.get("characters", []),
        "EL": data.get("story_elements", []),
        "SP": data.get("setup_payoffs", []),
        "GAP": data.get("gaps", []),
        "UNIT": data.get("coverage", {}).get("material_coverage", {}).get("units", []),
    }
    result: dict[str, set[str]] = {prefix: set() for prefix in collections}
    duplicates: list[str] = []
    seen: set[str] = set()
    for prefix, items in collections.items():
        for item in items:
            identifier = item.get("id", "") if isinstance(item, dict) else ""
            if identifier in seen:
                duplicates.append(identifier)
            seen.add(identifier)
            result[prefix].add(identifier)
    return result, duplicates


def _walk_refs(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.endswith("_id") and isinstance(child, str) and child:
                yield child_path, child
            elif key.endswith("_ids") and isinstance(child, list):
                for index, identifier in enumerate(child):
                    if isinstance(identifier, str) and identifier:
                        yield f"{child_path}[{index}]", identifier
            yield from _walk_refs(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_refs(child, f"{path}[{index}]")


def validate_data(data: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA) -> ValidationResult:
    result = ValidationResult(errors=_schema_validation(data, schema_path))
    if result.errors:
        return result

    ids, duplicates = _all_ids(data)
    if duplicates:
        result.errors.append(f"duplicate IDs: {', '.join(sorted(set(duplicates)))}")

    id_union = set().union(*ids.values())
    for path, identifier in _walk_refs(data):
        if ID_PATTERN.match(identifier) and identifier not in id_union:
            result.errors.append(f"{path}: unknown ID {identifier}")

    sources = {item["id"]: item for item in data["sources"]}
    nodes = {item["id"]: item for item in data["nodes"]}
    active_nodes = {key: item for key, item in nodes.items() if not item.get("superseded_by")}
    segments = {item["id"]: item for item in data["segments"]}

    material = data["coverage"]["material_coverage"]
    unit_statuses = [unit["status"] for unit in material["units"]]
    if material["status"] == "complete" and any(status != "analyzed" for status in unit_statuses):
        result.errors.append("material_coverage is complete but not every unit is analyzed")
    if material["status"] == "partial" and unit_statuses and all(status == "analyzed" for status in unit_statuses):
        result.warnings.append("material_coverage is partial although every declared unit is analyzed")
    for unit in material["units"]:
        if unit["source_id"] not in sources:
            result.errors.append(f"{unit['id']}: unknown source {unit['source_id']}")

    for segment in data["segments"]:
        expected = {
            node["id"] for node in active_nodes.values() if node["segment_id"] == segment["id"]
        }
        listed = set(segment["node_ids"])
        if expected != listed:
            result.errors.append(
                f"{segment['id']}: node_ids mismatch; expected {sorted(expected)}, got {sorted(listed)}"
            )
    for node in active_nodes.values():
        if node["segment_id"] not in segments:
            result.errors.append(f"{node['id']}: unknown segment {node['segment_id']}")

    for node in data["nodes"]:
        hint = node["adaptation_hint"]
        if hint["priority"] == "normal":
            if hint["selection_reason"] or hint["interaction_shape"] or hint["pressure_or_feedback"]:
                result.errors.append(f"{node['id']}: normal hint must keep high-priority fields empty")
        else:
            if not hint["selection_reason"] or not hint["pressure_or_feedback"]:
                result.errors.append(f"{node['id']}: high hint lacks reason or pressure/feedback")
            if not 2 <= len(hint["interaction_shape"]) <= 4:
                result.errors.append(f"{node['id']}: high hint interaction_shape must contain 2-4 steps")
        superseded = node.get("superseded_by", "")
        if superseded and superseded not in active_nodes:
            result.errors.append(f"{node['id']}: superseded_by must point to an active node")
        parent = node.get("parent_node_id", "")
        if parent and parent not in nodes:
            result.errors.append(f"{node['id']}: unknown parent_node_id {parent}")

    links = []
    for link in data["causal_links"]:
        if link["from_node_id"] not in active_nodes or link["to_node_id"] not in active_nodes:
            result.errors.append(f"{link['id']}: causal link must connect active nodes")
        elif link["from_node_id"] == link["to_node_id"]:
            result.errors.append(f"{link['id']}: self-link is not allowed")
        else:
            links.append(link)

    spine = sorted(
        [node for node in active_nodes.values() if node["importance"] == "spine"],
        key=lambda item: (item["order"], item["id"]),
    )
    if len(spine) > 1:
        incoming = {node["id"]: 0 for node in spine}
        outgoing = {node["id"]: 0 for node in spine}
        spine_ids = set(incoming)
        for link in links:
            if link["from_node_id"] in spine_ids:
                outgoing[link["from_node_id"]] += 1
            if link["to_node_id"] in spine_ids:
                incoming[link["to_node_id"]] += 1
        for node in spine[1:]:
            if incoming[node["id"]] == 0:
                result.errors.append(f"{node['id']}: spine node has no incoming causal link")
        for node in spine[:-1]:
            if outgoing[node["id"]] == 0:
                result.errors.append(f"{node['id']}: spine node has no outgoing causal link")

    review = data["review"]
    active_count = len(active_nodes)
    spine_ratio = len(spine) / active_count if active_count else 0.0
    if (len(spine) > 12 or spine_ratio > 0.65) and not review["spine_expansion_reason"]:
        result.warnings.append(
            f"spine is expanded ({len(spine)}/{active_count}); add review.spine_expansion_reason or compress it"
        )
    high_count = sum(node["adaptation_hint"]["priority"] == "high" for node in active_nodes.values())
    high_ratio = high_count / active_count if active_count else 0.0
    if high_ratio > 0.40 and not review["high_priority_expansion_reason"]:
        result.warnings.append(
            f"high-priority hints are expanded ({high_count}/{active_count}); "
            "add review.high_priority_expansion_reason or downgrade candidates"
        )

    locked = {fragment["id"] for fragment in data["notable_fragments"] if fragment["status"] == "locked"}
    declared_locked = set(review["user_locked_fragment_ids"])
    if locked != declared_locked:
        result.errors.append(
            f"locked fragment mismatch: statuses={sorted(locked)}, review={sorted(declared_locked)}"
        )

    for fragment in data["notable_fragments"]:
        if fragment["segment_id"] not in segments:
            result.errors.append(f"{fragment['id']}: unknown segment {fragment['segment_id']}")
        covered = fragment["presentation_hint"]["covered_by_node_id"]
        if covered and covered not in fragment["related_node_ids"]:
            result.errors.append(f"{fragment['id']}: covered_by_node_id must appear in related_node_ids")
        if fragment["notability_basis"] == "external_reception":
            if not fragment["external_support_refs"]:
                result.errors.append(f"{fragment['id']}: external_reception lacks support refs")
            for ref in fragment["external_support_refs"]:
                source = sources.get(ref["source_id"])
                if not source or source["role"] != "secondary":
                    result.errors.append(
                        f"{fragment['id']}: external support must reference a secondary source"
                    )

    revision = data["metadata"]["revision"]
    history = data["metadata"]["revision_history"]
    if revision > 1 and not any(entry["revision"] == revision for entry in history):
        result.errors.append("current revision is missing from metadata.revision_history")
    return result


def validate_file(path: Path, schema_path: Path = DEFAULT_SCHEMA) -> ValidationResult:
    try:
        return validate_data(load_yaml(path), schema_path)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        return ValidationResult(errors=[str(exc)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, help="Path to structure.yaml")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--warnings-as-errors", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = validate_file(args.structure.resolve(), args.schema.resolve())
    for message in result.errors:
        print(f"ERROR: {message}")
    for message in result.warnings:
        print(f"WARNING: {message}")
    if result.errors or (args.warnings_as_errors and result.warnings):
        return 1
    print(f"OK: {args.structure} ({len(result.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())


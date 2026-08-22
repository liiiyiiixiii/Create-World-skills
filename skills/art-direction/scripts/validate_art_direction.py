#!/usr/bin/env python3
"""Validate Create World Art Direction YAML files (schema 1.0)."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = SKILL_ROOT / "references" / "art-direction-v1.schema.json"
SCORE_KEYS = (
    "source_fidelity",
    "gameplay_readability",
    "production_feasibility",
    "distinctiveness",
    "system_coherence",
)


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


def _schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    validator = Draft202012Validator(load_schema(schema_path), format_checker=FormatChecker())
    return [
        f"{_path_text(error.absolute_path)}: {error.message}"
        for error in sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path))
    ]


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _ids(data: dict[str, Any]) -> list[str]:
    collections = (
        data["sources"],
        data["observations"],
        data["territories"],
        data["style_kernel"]["pillars"],
        data["translation_rules"],
        data["asset_families"],
        data["pilot_plan"]["tests"],
        data["qa"]["gates"],
    )
    return [item["id"] for collection in collections for item in collection]


def territory_score(territory: dict[str, Any]) -> int:
    return sum(int(territory["scores"][key]) for key in SCORE_KEYS)


def validate_data(
    data: dict[str, Any], schema_path: Path = DEFAULT_SCHEMA
) -> ValidationResult:
    result = ValidationResult(errors=_schema_errors(data, schema_path))
    if result.errors:
        return result

    duplicates = _duplicates(_ids(data))
    if duplicates:
        result.errors.append(f"duplicate IDs: {', '.join(duplicates)}")

    sources = {item["id"]: item for item in data["sources"]}
    observations = {item["id"]: item for item in data["observations"]}
    territories = {item["id"]: item for item in data["territories"]}
    families = {item["id"]: item for item in data["asset_families"]}

    for observation in data["observations"]:
        for ref in observation["source_refs"]:
            if ref["source_id"] not in sources:
                result.errors.append(
                    f"{observation['id']}: unknown source {ref['source_id']}"
                )

    selected = [item for item in data["territories"] if item["status"] == "selected"]
    if len(selected) != 1:
        result.errors.append("territories must contain exactly one selected item")
    else:
        selected_id = selected[0]["id"]
        selection_id = data["selection"]["selected_territory_id"]
        kernel_id = data["style_kernel"]["selected_territory_id"]
        if selected_id != selection_id or selected_id != kernel_id:
            result.errors.append(
                "selected territory, selection.selected_territory_id, and "
                "style_kernel.selected_territory_id must match"
            )
        highest = max(territory_score(item) for item in data["territories"])
        if territory_score(selected[0]) < highest:
            result.warnings.append(
                f"{selected_id} is selected without the highest numeric score; preserve the tradeoff in selection_rationale"
            )

    for identifier in (
        data["selection"]["selected_territory_id"],
        data["style_kernel"]["selected_territory_id"],
    ):
        if identifier not in territories:
            result.errors.append(f"unknown territory {identifier}")

    for rule in data["translation_rules"]:
        for observation_id in rule["source_observation_ids"]:
            if observation_id not in observations:
                result.errors.append(
                    f"{rule['id']}: unknown observation {observation_id}"
                )
        for family_id in rule["asset_family_ids"]:
            if family_id not in families:
                result.errors.append(f"{rule['id']}: unknown asset family {family_id}")

    pixel = data["visual_system"]["pixel_policy"]
    if pixel["mode"] == "strict_pixel":
        if pixel["sampling"] != "nearest_neighbor":
            result.errors.append("strict_pixel requires nearest_neighbor sampling")
        if pixel["display_scaling"] != "integer_only":
            result.errors.append("strict_pixel requires integer_only display scaling")
    if pixel["mode"] == "hybrid_pixel" and not pixel["exception_rules"]:
        result.errors.append("hybrid_pixel requires at least one exception rule")

    colors = data["visual_system"]["palette"]["colors"]
    duplicate_names = _duplicates(color["name"].casefold() for color in colors)
    if duplicate_names:
        result.errors.append(f"duplicate palette color names: {', '.join(duplicate_names)}")
    roles = {color["role"] for color in colors}
    for required_role in ("accent", "ui_text"):
        if required_role not in roles:
            result.errors.append(f"palette requires a {required_role} color role")

    note_keys = set(data["prompt_capsule"]["asset_specific_notes"])
    unknown_note_keys = note_keys - set(families)
    if unknown_note_keys:
        result.errors.append(
            "prompt_capsule.asset_specific_notes has unknown asset family keys: "
            + ", ".join(sorted(unknown_note_keys))
        )

    pilot_families: set[str] = set()
    for test in data["pilot_plan"]["tests"]:
        family_id = test["asset_family_id"]
        if family_id not in families:
            result.errors.append(f"{test['id']}: unknown asset family {family_id}")
        pilot_families.add(family_id)
    uncovered_families = set(families) - pilot_families
    if uncovered_families:
        result.warnings.append(
            "pilot plan does not cover asset families: "
            + ", ".join(sorted(uncovered_families))
        )

    status = data["pilot_plan"]["generation_status"]
    artifact_paths = data["pilot_plan"]["artifact_paths"]
    if status == "completed" and not artifact_paths:
        result.errors.append("completed pilot plan requires artifact_paths")
    if status != "completed" and artifact_paths:
        result.warnings.append(
            "pilot artifact_paths are present although generation_status is not completed"
        )

    qa_categories = {item["category"] for item in data["qa"]["gates"]}
    for required_category in ("readability", "consistency", "technical"):
        if required_category not in qa_categories:
            result.errors.append(f"QA gates must include category {required_category}")

    used_families = {
        family_id
        for rule in data["translation_rules"]
        for family_id in rule["asset_family_ids"]
    }
    unconnected_families = set(families) - used_families
    if unconnected_families:
        result.warnings.append(
            "asset families lack translation rules: "
            + ", ".join(sorted(unconnected_families))
        )

    primary_sources = [item for item in data["sources"] if item["role"] == "primary"]
    if not primary_sources:
        result.warnings.append("no primary source is declared")
    approval = data["review"]["approval_status"]
    if approval == "approved" and primary_sources and all(
        item["evidence_status"] == "unverified" for item in primary_sources
    ):
        result.errors.append("approved direction cannot rely only on unverified primary sources")
    if approval == "approved" and status != "completed":
        result.warnings.append("approved direction has no completed visual pilot")
    if approval == "approved" and data["constraints"]["assumptions"]:
        result.warnings.append("approved direction still contains unresolved assumptions")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_path", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    try:
        data = load_yaml(args.yaml_path)
        result = validate_data(data, args.schema)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"VALID: {args.yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

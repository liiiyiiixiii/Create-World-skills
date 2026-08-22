from __future__ import annotations

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE = ROOT / "tests" / "fixtures" / "fog-harbor-v2.yaml"
sys.path.insert(0, str(SCRIPTS))

from render_structure import render_overview, render_structure  # noqa: E402
from validate_structure import validate_data  # noqa: E402


class ContentUnderstandingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_fixture(self) -> None:
        result = validate_data(self.data)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_partial_material_accepts_failed_unit(self) -> None:
        data = copy.deepcopy(self.data)
        data["coverage"]["material_coverage"]["status"] = "partial"
        data["coverage"]["material_coverage"]["units"][0]["status"] = "failed"
        self.assertTrue(validate_data(data).ok)

    def test_short_story_is_a_supported_target_medium(self) -> None:
        self.assertEqual(
            "short_story",
            self.data["coverage"]["target_fidelity"]["target_medium"],
        )
        self.assertTrue(validate_data(self.data).ok)

    def test_complete_material_rejects_failed_unit(self) -> None:
        data = copy.deepcopy(self.data)
        data["coverage"]["material_coverage"]["units"][0]["status"] = "failed"
        result = validate_data(data)
        self.assertTrue(any("not every unit is analyzed" in item for item in result.errors))

    def test_subtitle_locator_is_preserved(self) -> None:
        data = copy.deepcopy(self.data)
        data["sources"][0]["kind"] = "subtitle"
        data["sources"][0]["locator_scheme"] = "timestamp"
        data["nodes"][0]["facts"][0]["source_refs"][0]["locator"] = "00:00:01.000 --> 00:00:05.000"
        self.assertTrue(validate_data(data).ok)

    def test_normal_hint_rejects_expanded_fields(self) -> None:
        data = copy.deepcopy(self.data)
        data["nodes"][0]["adaptation_hint"]["selection_reason"] = "不应出现"
        result = validate_data(data)
        self.assertTrue(any("normal hint" in item for item in result.errors))

    def test_high_hint_requires_two_to_four_steps(self) -> None:
        data = copy.deepcopy(self.data)
        data["nodes"][1]["adaptation_hint"]["interaction_shape"] = ["一步"]
        result = validate_data(data)
        self.assertTrue(any("2-4 steps" in item for item in result.errors))

    def test_high_priority_ratio_warns(self) -> None:
        data = copy.deepcopy(self.data)
        for node in data["nodes"]:
            node["adaptation_hint"].update(
                priority="high",
                selection_reason="测试高价值比例",
                interaction_shape=["观察", "行动"],
                pressure_or_feedback="即时反馈",
            )
        result = validate_data(data)
        self.assertTrue(any("high-priority" in item for item in result.warnings))

    def test_expanded_spine_warns_without_reason(self) -> None:
        data = copy.deepcopy(self.data)
        data["review"]["spine_expansion_reason"] = ""
        result = validate_data(data)
        self.assertTrue(any("spine is expanded" in item for item in result.warnings))

    def test_locked_fragment_must_match_review(self) -> None:
        data = copy.deepcopy(self.data)
        data["review"]["user_locked_fragment_ids"] = []
        self.assertFalse(validate_data(data).ok)

    def test_external_reception_requires_secondary_support(self) -> None:
        data = copy.deepcopy(self.data)
        fragment = data["notable_fragments"][0]
        fragment["notability_basis"] = "external_reception"
        result = validate_data(data)
        self.assertTrue(any("external_reception" in item for item in result.errors))

    def test_film_can_be_complete_but_unverified(self) -> None:
        data = copy.deepcopy(self.data)
        data["coverage"]["target_fidelity"].update(
            target_medium="film",
            target_version="上映成片",
            status="unverified",
            caveats=["仅分析完整剧本"],
        )
        self.assertTrue(validate_data(data).ok)

    def test_revision_two_requires_history_and_preserves_lock(self) -> None:
        data = copy.deepcopy(self.data)
        data["metadata"]["revision"] = 2
        data["metadata"]["revision_history"] = [
            {
                "revision": 2,
                "generated_at": "2026-08-22T13:00:00+08:00",
                "summary": "调整节点层级",
                "affected_ids": ["N-002", "NF-001"],
            }
        ]
        result = validate_data(data)
        self.assertTrue(result.ok)
        self.assertEqual("locked", data["notable_fragments"][0]["status"])

    def test_renderer_contains_all_ids_and_hints(self) -> None:
        result = validate_data(self.data)
        overview = render_overview(self.data)
        detail = render_structure(self.data, result.warnings)
        for node in self.data["nodes"]:
            self.assertIn(node["id"], detail)
            self.assertIn(node["adaptation_hint"]["player_action"], detail)
        for fragment in self.data["notable_fragments"]:
            self.assertIn(fragment["id"], overview)
            self.assertIn(fragment["id"], detail)

    def test_excluded_fragment_is_hidden_only_from_overview(self) -> None:
        data = copy.deepcopy(self.data)
        data["notable_fragments"][0]["status"] = "excluded"
        data["review"]["user_locked_fragment_ids"] = []
        result = validate_data(data)
        self.assertTrue(result.ok)
        self.assertNotIn("NF-001", render_overview(data))
        self.assertIn("NF-001", render_structure(data, result.warnings))

    def test_cli_render_writes_two_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_structure.py"),
                    str(FIXTURE),
                    "--output-dir",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertTrue((output / "overview.md").exists())
            self.assertTrue((output / "structure.md").exists())

    def test_revision_archive_writes_snapshot_and_changelog(self) -> None:
        data = copy.deepcopy(self.data)
        data["metadata"]["revision"] = 2
        data["metadata"]["revision_history"] = [
            {
                "revision": 2,
                "generated_at": "2026-08-22T13:00:00+08:00",
                "summary": "锁定片段并调整提示",
                "affected_ids": ["NF-001", "N-002"],
            }
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            structure = root / "structure.yaml"
            structure.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPTS / "archive_revision.py"), str(structure)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertTrue((root / "revisions" / "r0002.yaml").exists())
            self.assertIn("NF-001", (root / "CHANGELOG.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


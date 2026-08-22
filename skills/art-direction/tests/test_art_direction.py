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
FIXTURE = ROOT / "tests" / "fixtures" / "fog-harbor.yaml"
sys.path.insert(0, str(SCRIPTS))

from render_art_direction import render  # noqa: E402
from validate_art_direction import territory_score, validate_data  # noqa: E402


class ArtDirectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))

    def test_valid_fixture_has_no_warnings(self) -> None:
        result = validate_data(self.data)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_score_is_sum_of_five_axes(self) -> None:
        selected = next(item for item in self.data["territories"] if item["status"] == "selected")
        self.assertEqual(24, territory_score(selected))

    def test_selected_ids_must_match(self) -> None:
        data = copy.deepcopy(self.data)
        data["style_kernel"]["selected_territory_id"] = "T-001"
        result = validate_data(data)
        self.assertTrue(any("must match" in item for item in result.errors))

    def test_exactly_one_territory_is_selected(self) -> None:
        data = copy.deepcopy(self.data)
        data["territories"][0]["status"] = "selected"
        result = validate_data(data)
        self.assertTrue(any("exactly one" in item for item in result.errors))

    def test_non_highest_selection_warns(self) -> None:
        data = copy.deepcopy(self.data)
        for item in data["territories"]:
            item["status"] = "selected" if item["id"] == "T-001" else "rejected"
        data["selection"]["selected_territory_id"] = "T-001"
        data["style_kernel"]["selected_territory_id"] = "T-001"
        result = validate_data(data)
        self.assertTrue(result.ok)
        self.assertTrue(any("highest numeric score" in item for item in result.warnings))

    def test_strict_pixel_requires_nearest_integer_scaling(self) -> None:
        data = copy.deepcopy(self.data)
        pixel = data["visual_system"]["pixel_policy"]
        pixel.update(mode="strict_pixel", sampling="smooth", display_scaling="free")
        result = validate_data(data)
        self.assertTrue(any("nearest_neighbor" in item for item in result.errors))
        self.assertTrue(any("integer_only" in item for item in result.errors))

    def test_hybrid_pixel_requires_exception(self) -> None:
        data = copy.deepcopy(self.data)
        data["visual_system"]["pixel_policy"]["exception_rules"] = []
        result = validate_data(data)
        self.assertTrue(any("exception rule" in item for item in result.errors))

    def test_translation_refs_must_exist(self) -> None:
        data = copy.deepcopy(self.data)
        data["translation_rules"][0]["asset_family_ids"] = ["AF-999"]
        result = validate_data(data)
        self.assertTrue(any("unknown asset family" in item for item in result.errors))

    def test_palette_requires_accent_and_ui_text(self) -> None:
        data = copy.deepcopy(self.data)
        for color in data["visual_system"]["palette"]["colors"]:
            if color["role"] in {"accent", "ui_text"}:
                color["role"] = "custom"
        result = validate_data(data)
        self.assertTrue(any("accent" in item for item in result.errors))
        self.assertTrue(any("ui_text" in item for item in result.errors))

    def test_prompt_notes_use_asset_family_ids(self) -> None:
        data = copy.deepcopy(self.data)
        data["prompt_capsule"]["asset_specific_notes"]["characters"] = "invalid key"
        result = validate_data(data)
        self.assertTrue(any("unknown asset family keys" in item for item in result.errors))

    def test_completed_pilots_require_paths(self) -> None:
        data = copy.deepcopy(self.data)
        data["pilot_plan"]["generation_status"] = "completed"
        result = validate_data(data)
        self.assertTrue(any("requires artifact_paths" in item for item in result.errors))

    def test_qa_requires_core_categories(self) -> None:
        data = copy.deepcopy(self.data)
        for gate in data["qa"]["gates"]:
            if gate["category"] == "technical":
                gate["category"] = "production"
        result = validate_data(data)
        self.assertTrue(any("category technical" in item for item in result.errors))

    def test_approved_direction_rejects_unverified_primary_sources(self) -> None:
        data = copy.deepcopy(self.data)
        data["review"]["approval_status"] = "approved"
        data["pilot_plan"]["generation_status"] = "completed"
        data["pilot_plan"]["artifact_paths"] = ["pilots/proof.png"]
        for source in data["sources"]:
            if source["role"] == "primary":
                source["evidence_status"] = "unverified"
        result = validate_data(data)
        self.assertTrue(any("unverified primary" in item for item in result.errors))

    def test_renderer_contains_all_major_ids(self) -> None:
        result = validate_data(self.data)
        markdown = render(self.data, result.warnings)
        for collection in (
            self.data["observations"],
            self.data["territories"],
            self.data["style_kernel"]["pillars"],
            self.data["translation_rules"],
            self.data["asset_families"],
            self.data["pilot_plan"]["tests"],
            self.data["qa"]["gates"],
        ):
            for item in collection:
                self.assertIn(item["id"], markdown)
        for color in self.data["visual_system"]["palette"]["colors"]:
            self.assertIn(color["hex"], markdown)

    def test_cli_render_writes_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_art_direction.py"),
                    str(FIXTURE),
                    "--output-dir",
                    temp,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            output = Path(temp) / "art-direction.md"
            self.assertTrue(output.exists())
            self.assertIn("锈色信号灯", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

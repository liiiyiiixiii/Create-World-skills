from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "scene_collision.py"
ASSET_SCRIPT = ROOT / "scripts" / "generate_reference_assets.py"


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


class SceneCollisionTests(unittest.TestCase):
    def valid_spec(self) -> dict:
        return {
            "version": 1,
            "metadata": {
                "scene_id": "test-room",
                "generation_mode": "balanced",
                "input_type": "description",
                "image_generation_calls": 1,
                "art_direction_id": None,
            },
            "coordinate_space": {"width": 100, "height": 100},
            "collision_model": "footpoint",
            "walkable": [{"id": "floor", "points": [[10, 10], [90, 10], [90, 90], [10, 90]]}],
            "obstacles": [
                {"id": "desk", "shape": "rect", "x": 40, "y": 40, "width": 20, "height": 20},
                {"id": "barrel", "shape": "circle", "cx": 72, "cy": 42, "radius": 5},
            ],
            "anchors": [
                {"id": "spawn", "kind": "spawn", "x": 20, "y": 20},
                {"id": "exit", "kind": "exit", "x": 80, "y": 80},
            ],
        }

    def test_render_preserves_scene_and_adds_red_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            scene = temp / "scene.png"
            spec = temp / "collision.json"
            output = temp / "overlay.png"
            report = temp / "qa-report.json"
            Image.new("RGB", (100, 100), (30, 40, 50)).save(scene)
            write_json(spec, self.valid_spec())
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    "--scene",
                    str(scene),
                    "--spec",
                    str(spec),
                    "--output",
                    str(output),
                    "--report",
                    str(report),
                    "--line-width",
                    "2",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(output) as rendered:
                rgba = rendered.convert("RGBA")
                self.assertEqual(rgba.size, (100, 100))
                self.assertEqual(rgba.getpixel((10, 10)), (255, 24, 24, 255))
                self.assertEqual(rgba.getpixel((30, 30)), (30, 40, 50, 255))
                self.assertEqual(rgba.getpixel((40, 40)), (255, 24, 24, 255))
                with Image.open(scene) as source:
                    original = source.convert("RGBA")
                changed = 0
                for y in range(rgba.height):
                    for x in range(rgba.width):
                        before = original.getpixel((x, y))
                        after = rgba.getpixel((x, y))
                        if before != after:
                            changed += 1
                            self.assertEqual(after, (255, 24, 24, 255))
                self.assertGreater(changed, 0)
            qa = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(qa["ok"])
            self.assertTrue(qa["alignment"]["passed"])
            self.assertTrue(qa["alignment"]["same_dimensions"])
            self.assertTrue(qa["alignment"]["only_red_added"])
            self.assertTrue(qa["alignment"]["non_red_pixels_preserved"])
            self.assertEqual(qa["alignment"]["dimensions"]["scene"], {"width": 100, "height": 100})
            self.assertEqual(qa["metadata"]["generation_mode"], "balanced")
            self.assertEqual(qa["metadata"]["image_generation_calls"], 1)
            self.assertEqual(qa["generation"]["image_generation_calls"], 1)
            self.assertFalse(qa["generation"]["art_direction_used"])

    def test_guide_uses_fixed_palette_and_preserves_door_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            spec_path = temp / "collision.json"
            guide_path = temp / "layout-guide.png"
            report_path = temp / "guide-report.json"
            spec = self.valid_spec()
            spec["walkable"] = [
                {
                    "id": "room-with-south-door",
                    "points": [[10, 10], [90, 10], [90, 80], [60, 80], [60, 95], [40, 95], [40, 80], [10, 80]],
                }
            ]
            spec["anchors"][1].update({"x": 50, "y": 90})
            write_json(spec_path, spec)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "guide",
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(guide_path),
                    "--report",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with Image.open(guide_path) as guide:
                rgba = guide.convert("RGBA")
                self.assertEqual(rgba.size, (100, 100))
                self.assertEqual(rgba.getpixel((20, 20)), (218, 205, 176, 255))
                self.assertEqual(rgba.getpixel((50, 50)), (51, 55, 57, 255))
                self.assertEqual(rgba.getpixel((50, 90)), (218, 205, 176, 255))
                self.assertEqual(rgba.getpixel((30, 90)), (8, 9, 10, 255))
            qa = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(qa["ok"])
            self.assertFalse(qa["guide"]["contains_text_or_markers"])

    def test_disconnected_anchors_fail_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            spec_path = temp / "collision.json"
            report = temp / "qa-report.json"
            spec = self.valid_spec()
            spec["obstacles"] = [
                {"id": "wall", "shape": "rect", "x": 48, "y": 10, "width": 4, "height": 80}
            ]
            spec["anchors"][1].update({"x": 80, "y": 20})
            write_json(spec_path, spec)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--spec", str(spec_path), "--report", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            qa = json.loads(report.read_text(encoding="utf-8"))
            self.assertFalse(qa["ok"])
            self.assertTrue(any("not mutually reachable" in error for error in qa["errors"]))

    def test_fast_mode_rejects_more_than_one_generation_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            spec_path = temp / "collision.json"
            spec = self.valid_spec()
            spec["metadata"].update({"generation_mode": "fast", "image_generation_calls": 2})
            write_json(spec_path, spec)
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--spec", str(spec_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("fast mode permits at most one", result.stdout)

    def test_anonymous_courtyard_fixture_keeps_five_obstacles_and_anchors(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "courtyard-collision.json"
        spec = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertIn("south-bench", {item["id"] for item in spec["obstacles"]})
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "qa-report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "validate", "--spec", str(fixture), "--report", str(report)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            qa = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(qa["ok"])
            self.assertEqual(qa["counts"]["walkable"], 1)
            self.assertEqual(qa["counts"]["obstacles"], 5)
            self.assertEqual(qa["counts"]["anchors"], 5)

    def test_reference_assets_are_pixel_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(ASSET_SCRIPT), "--output-dir", temp_dir],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("playable-scene-style-board.png", "collision-notation-board.png"):
                generated_path = Path(temp_dir) / name
                committed_path = ROOT / "assets" / name
                self.assertTrue(generated_path.is_file())
                with Image.open(generated_path) as generated, Image.open(committed_path) as committed:
                    generated_rgb = generated.convert("RGB")
                    committed_rgb = committed.convert("RGB")
                    self.assertEqual(generated_rgb.size, committed_rgb.size)
                    self.assertEqual(generated_rgb.tobytes(), committed_rgb.tobytes())


if __name__ == "__main__":
    unittest.main()

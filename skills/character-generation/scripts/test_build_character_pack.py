#!/usr/bin/env python3
"""Regression tests for build_character_pack.py."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

import build_character_pack as builder
import generate_reference_assets as reference_assets


def draw_pose(canvas: Image.Image, origin_x: int, variant: int, direction: str) -> None:
    draw = ImageDraw.Draw(canvas)
    skin = (201, 139, 91, 255)
    hair = (65, 45, 35, 255)
    shirt = (80, 120, 155, 255)
    trousers = (65, 65, 72, 255)
    shoes = (55, 35, 25, 255)
    outline = (25, 25, 29, 255)

    center = origin_x + 50
    head_left = center - (25 if direction != "right" else 20)
    head_right = center + (25 if direction != "right" else 20)
    draw.ellipse((head_left - 2, 16, head_right + 2, 70), fill=outline)
    draw.ellipse((head_left, 18, head_right, 68), fill=skin)
    draw.rectangle((head_left, 18, head_right, 33), fill=hair)
    if direction == "down":
        draw.rectangle((center - 12, 44, center - 7, 50), fill=(30, 30, 30, 255))
        draw.rectangle((center + 7, 44, center + 12, 50), fill=(30, 30, 30, 255))

    draw.rectangle((center - 28, 70, center + 28, 140), fill=outline)
    draw.rectangle((center - 25, 72, center + 25, 138), fill=shirt)
    draw.rectangle((center - 32, 78, center - 25, 139), fill=skin)
    draw.rectangle((center + 25, 78, center + 32, 139), fill=skin)

    left_shift = -12 if variant == 3 else 0
    right_shift = 12 if variant == 1 else 0
    draw.rectangle((center - 23 + left_shift, 138, center - 3 + left_shift, 208), fill=trousers)
    draw.rectangle((center + 3 + right_shift, 138, center + 23 + right_shift, 208), fill=trousers)
    draw.rectangle((center - 25 + left_shift, 204, center - 1 + left_shift, 217), fill=shoes)
    draw.rectangle((center + 1 + right_shift, 204, center + 25 + right_shift, 217), fill=shoes)


def make_master(path: Path, count: int, direction: str, spacing: int = 150) -> Path:
    if direction == "right" and count == 4:
        builder.compose_pose_master(bundled_template_poses("right")).save(path)
        return path
    canvas = Image.new("RGBA", (spacing * count + 30, 250), (0, 0, 0, 0))
    for index in range(count):
        draw_pose(canvas, index * spacing + 15, index, direction)
    canvas.save(path)
    return path


def bundled_template_poses(direction: str) -> list[Image.Image]:
    template = Path(__file__).resolve().parents[1] / "assets" / "walk-layout-template.png"
    cleaned = builder.load_master_with_qa(template, "test-layout-template")
    production = builder.split_production_sheet(cleaned.image)
    return [pose.copy() for pose in production.groups[direction].poses]


def paste_pose_in_slot(layer: Image.Image, pose: Image.Image, index: int) -> None:
    alpha = pose.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
    bbox = alpha.getbbox()
    assert bbox is not None
    cropped = pose.crop(bbox).convert("RGBA")
    scale = min(110 / cropped.width, 202 / cropped.height)
    size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
    resized = cropped.resize(size, Image.Resampling.NEAREST)
    center_x = index * 150 + 65
    layer.alpha_composite(resized, (center_x - resized.width // 2, 218 - resized.height))


def make_production_sheet(
    path: Path,
    *,
    background: str = "white",
    rows: int = 3,
    white_patch: bool = False,
    same_leg_directions: tuple[str, ...] = (),
) -> Path:
    width = 630
    row_height = 250
    subjects = Image.new("RGBA", (width, row_height * 3), (0, 0, 0, 0))
    for row, direction in enumerate(("down", "up", "right")[:rows]):
        layer = Image.new("RGBA", (width, row_height), (0, 0, 0, 0))
        template_poses = bundled_template_poses("right") if direction == "right" else None
        for index in range(4):
            if template_poses is not None:
                pose_index = 1 if direction in same_leg_directions and index == 3 else index
                paste_pose_in_slot(layer, template_poses[pose_index], index)
            else:
                variant = 1 if direction in same_leg_directions and index == 3 else index
                draw_pose(layer, index * 150 + 15, variant, direction)
                if direction in same_leg_directions and index == 3:
                    center = index * 150 + 65
                    ImageDraw.Draw(layer).rectangle(
                        (center - 16, 92, center + 16, 106), fill=(130, 75, 145, 255)
                    )
            if white_patch:
                center = index * 150 + 65
                ImageDraw.Draw(layer).rectangle(
                    (center - 8, 88, center + 8, 105), fill=(255, 255, 255, 255)
                )
        subjects.alpha_composite(layer, (0, row * row_height))

    if background == "transparent":
        output = subjects
    else:
        output = Image.new("RGB", subjects.size, "white")
        if background == "checkerboard":
            draw = ImageDraw.Draw(output)
            tile = 32
            for y in range(0, output.height, tile):
                for x in range(0, output.width, tile):
                    shade = 226 if (x // tile + y // tile) % 2 else 252
                    draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=(shade,) * 3)
        output.paste(subjects.convert("RGB"), mask=subjects.getchannel("A"))
    output.save(path)
    return path


def rgba_master_on_white(source: Path, destination: Path) -> Path:
    image = Image.open(source).convert("RGBA")
    output = Image.new("RGB", image.size, "white")
    output.paste(image.convert("RGB"), mask=image.getchannel("A"))
    output.save(destination)
    return destination


def normalized_template_frames(direction: str, cell_size: str = "48x64") -> list[Image.Image]:
    width, height = builder.parse_cell_size(cell_size)
    cell = builder.make_cell_spec(width, height)
    frames = [builder.normalize_pose(pose, cell) for pose in bundled_template_poses(direction)]
    frames[2] = frames[0].copy()
    return frames


def recolor_preserving_luminance(frame: Image.Image) -> Image.Image:
    alpha = frame.getchannel("A")
    gray = ImageOps.grayscale(frame)
    recolored = ImageOps.colorize(gray, black=(15, 35, 70), white=(245, 170, 90)).convert("RGBA")
    recolored.putalpha(alpha)
    return recolored


class CharacterPackBuilderTests(unittest.TestCase):
    def make_inputs(self, root: Path) -> dict[str, Path]:
        return {
            "turnaround": make_master(root / "turnaround.png", 3, "down"),
            "down": make_master(root / "down.png", 4, "down"),
            "up": make_master(root / "up.png", 4, "up"),
            "right": make_master(root / "right.png", 4, "right"),
        }

    def build(self, root: Path, character_id: str = "test-person") -> Path:
        inputs = self.make_inputs(root)
        return builder.build_character_pack(
            character_id=character_id,
            turnaround_path=inputs["turnaround"],
            walk_down_path=inputs["down"],
            walk_up_path=inputs["up"],
            walk_right_path=inputs["right"],
            output_dir=root / "中文 输出目录",
        )

    def test_complete_pack_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = self.build(root)
            self.assertEqual(pack.name, "test-person")

            manifest_path = pack / "character.json"
            qa_path = pack / "qa-report.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["cell"], {"width": 48, "height": 64})
            self.assertEqual(manifest["foot_anchor"], {"x": 24, "y": 61})
            self.assertEqual(manifest["frame_order"], builder.FRAME_ORDER)
            self.assertEqual(manifest["directions"]["left"]["derived_from"], "right")
            self.assertTrue(qa["passed"])
            self.assertNotIn(str(root), manifest_path.read_text(encoding="utf-8"))

            with Image.open(pack / manifest["turnaround"]["sheet_png"]) as source:
                views = source.convert("RGBA")
            self.assertEqual(views.size, (144, 64))
            self.assertTrue(set(builder.alpha_values(views)).issubset({0, 255}))
            self.assertLessEqual(builder.opaque_color_count(views), 64)

            with Image.open(pack / manifest["directions"]["right"]["sheet_png"]) as source:
                right = source.convert("RGBA")
            with Image.open(pack / manifest["directions"]["left"]["sheet_png"]) as source:
                left = source.convert("RGBA")
            self.assertEqual(right.size, (192, 64))
            self.assertEqual(left.size, (192, 64))
            for index in range(4):
                box = (index * 48, 0, (index + 1) * 48, 64)
                expected = ImageOps.mirror(right.crop(box))
                actual = left.crop(box)
                self.assertIsNone(ImageChops.difference(expected, actual).getbbox())

            with Image.open(pack / manifest["directions"]["down"]["sheet_webp"]) as source:
                webp = source.convert("RGBA")
            self.assertEqual(webp.size, (192, 64))
            self.assertEqual(builder.alpha_values(webp), [0, 255])

            for direction in builder.DIRECTIONS:
                animation_path = pack / manifest["directions"][direction]["animation_apng"]
                with Image.open(animation_path) as animation:
                    self.assertEqual(animation.n_frames, 4)
                    self.assertEqual(animation.size, (48, 64))

            with Image.open(pack / manifest["overview_gif"]) as overview:
                self.assertEqual(overview.n_frames, 4)
                self.assertEqual(overview.size, (384, 512))

    def test_existing_pack_gets_versioned_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = self.build(root)
            second = self.build(root)
            third = self.build(root)
            self.assertEqual(first.name, "test-person")
            self.assertEqual(second.name, "test-person-v2")
            self.assertEqual(third.name, "test-person-v3")

    def test_rejects_invalid_character_id(self) -> None:
        with self.assertRaises(builder.CharacterPackError):
            builder.validate_character_id("人物 One")
        with self.assertRaises(builder.CharacterPackError):
            builder.validate_character_id("../escape")

    def test_rejects_opaque_or_empty_master(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            opaque = root / "opaque.png"
            Image.new("RGB", (64, 64), "white").save(opaque)
            with self.assertRaises(builder.CharacterPackError):
                builder.load_master(opaque, "opaque")

            empty = root / "empty.png"
            Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(empty)
            with self.assertRaises(builder.CharacterPackError):
                builder.load_master(empty, "empty")

    def test_rejects_wrong_subject_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = Image.open(make_master(root / "three.png", 3, "down", spacing=280)).convert("RGBA")
            with self.assertRaises(builder.CharacterPackError):
                builder.split_subjects(image, 4, "walk-down")

    def test_production_sheet_on_white_background(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = make_production_sheet(root / "production.png")
            pack = builder.build_character_pack(
                character_id="production-person",
                production_sheet_path=production,
                output_dir=root / "输出",
            )
            manifest = json.loads((pack / "character.json").read_text(encoding="utf-8"))
            qa = json.loads((pack / "qa-report.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["style_profile"], "create-world-bright-chibi-v1")
            self.assertEqual(
                qa["master_preprocessing"]["production_sheet"]["method"],
                "rgb-light-neutral-flood",
            )
            self.assertTrue(qa["production_grid"]["valid_directions"])
            self.assertTrue(all(record["passed"] for record in qa["motion"].values()))

            with Image.open(pack / manifest["directions"]["down"]["sheet_png"]) as source:
                sheet = source.convert("RGBA")
            first = sheet.crop((0, 0, 48, 64))
            third = sheet.crop((96, 0, 144, 64))
            self.assertIsNone(ImageChops.difference(first, third).getbbox())

            for direction in builder.GENERATED_DIRECTIONS:
                self.assertTrue(qa["motion"][direction]["leg_alternation_passed"])

    def test_same_side_legs_fail_even_when_action_pixels_differ(self) -> None:
        frames = normalized_template_frames("down")
        repeated_phase = frames[1].copy()
        draw = ImageDraw.Draw(repeated_phase)
        draw.rectangle((21, 31, 27, 35), fill=(180, 40, 150, 255))
        frames[3] = repeated_phase

        result = builder.motion_qa(frames, "down")
        self.assertTrue(result["basic_motion_passed"])
        self.assertFalse(result["leg_alternation_passed"])
        self.assertFalse(result["passed"])

    def test_anonymous_front_and_back_have_opposite_dominant_foot_offsets(self) -> None:
        for direction in ("down", "up"):
            result = builder.motion_qa(normalized_template_frames(direction), direction)
            offsets = result["dominant_foot_offsets"]
            self.assertGreaterEqual(offsets[1], builder.MIN_DOMINANT_FOOT_OFFSET)
            self.assertLessEqual(offsets[3], -builder.MIN_DOMINANT_FOOT_OFFSET)
            self.assertTrue(result["leg_alternation_passed"])

    def test_anonymous_side_phases_pass_and_repeated_phase_fails(self) -> None:
        frames = normalized_template_frames("right")
        valid = builder.motion_qa(frames, "right")
        self.assertEqual(
            [valid["side_phase_classifications"][index]["classified_as"] for index in (1, 3)],
            ["A", "B"],
        )
        self.assertTrue(valid["leg_alternation_passed"])

        repeated = [frame.copy() for frame in frames]
        repeated[3] = recolor_preserving_luminance(frames[1])
        invalid = builder.motion_qa(repeated, "right")
        self.assertTrue(invalid["basic_motion_passed"])
        self.assertEqual(invalid["side_phase_classifications"][3]["classified_as"], "A")
        self.assertFalse(invalid["leg_alternation_passed"])

    def test_reference_assets_are_exactly_reproducible(self) -> None:
        committed = Path(__file__).resolve().parents[1] / "assets"
        with tempfile.TemporaryDirectory() as temp:
            generated = reference_assets.generate_assets(Path(temp))
            for name, expected_size in (
                (reference_assets.STYLE_BOARD_NAME, (1780, 576)),
                (reference_assets.WALK_TEMPLATE_NAME, (768, 768)),
            ):
                with Image.open(committed / name) as expected, Image.open(generated[name]) as actual:
                    self.assertEqual(expected.mode, "RGB")
                    self.assertEqual(actual.mode, "RGB")
                    self.assertEqual(expected.size, expected_size)
                    self.assertEqual(actual.size, expected_size)
                    self.assertIsNone(
                        ImageChops.difference(expected.convert("RGB"), actual.convert("RGB")).getbbox(),
                        name,
                    )

    def test_swapped_action_frame_order_is_rejected(self) -> None:
        for direction in builder.GENERATED_DIRECTIONS:
            frames = normalized_template_frames(direction)
            frames[1], frames[3] = frames[3], frames[1]
            result = builder.motion_qa(frames, direction)
            self.assertFalse(result["leg_alternation_passed"], direction)

    def test_body_jitter_does_not_hide_repeated_leg_phase(self) -> None:
        frames = normalized_template_frames("down")
        repeated = ImageChops.offset(frames[1], 1, 0)
        repeated.putalpha(ImageChops.offset(frames[1].getchannel("A"), 1, 0))
        frames[3] = repeated
        result = builder.motion_qa(frames, "down")
        self.assertTrue(result["basic_motion_passed"])
        self.assertFalse(result["leg_alternation_passed"])

    def test_side_phase_matching_survives_outfit_recolor(self) -> None:
        frames = [recolor_preserving_luminance(frame) for frame in normalized_template_frames("right")]
        frames[2] = frames[0].copy()
        result = builder.motion_qa(frames, "right")
        self.assertTrue(result["leg_alternation_passed"])
        self.assertGreaterEqual(
            result["side_phase_classifications"][1]["confidence_margin"],
            builder.MIN_SIDE_PHASE_CONFIDENCE,
        )
        self.assertGreaterEqual(
            result["side_phase_classifications"][3]["confidence_margin"],
            builder.MIN_SIDE_PHASE_CONFIDENCE,
        )

    def test_motion_phase_error_lists_only_failed_directions_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = make_production_sheet(
                root / "same-leg.png", same_leg_directions=("down", "up")
            )
            output = root / "output"
            with self.assertRaisesRegex(
                builder.CharacterPackError,
                r"^MOTION_PHASE_FAILED directions=down,up$",
            ):
                builder.build_character_pack(
                    character_id="same-leg-person",
                    production_sheet_path=production,
                    output_dir=output,
                )
            self.assertFalse(output.exists())

    def test_failed_motion_row_can_be_overridden_without_replacing_valid_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = make_production_sheet(
                root / "same-leg-down.png", same_leg_directions=("down",)
            )
            replacement = rgba_master_on_white(
                make_master(root / "down-rgba.png", 4, "down"), root / "down.png"
            )
            pack = builder.build_character_pack(
                character_id="motion-row-override",
                production_sheet_path=production,
                walk_down_path=replacement,
                output_dir=root / "output",
            )
            qa = json.loads((pack / "qa-report.json").read_text(encoding="utf-8"))
            self.assertTrue(qa["passed"])
            self.assertEqual(qa["motion"]["down"]["expected_action_frame_sides"], ["screen-right", "screen-left"])
            self.assertIn("down", qa["master_preprocessing"])

    def test_checkerboard_cleanup_preserves_enclosed_white(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = make_production_sheet(
                root / "checkerboard.png",
                background="checkerboard",
                white_patch=True,
            )
            result = builder.load_master_with_qa(production, "checkerboard")
            self.assertEqual(result.method, "rgb-light-neutral-flood")
            self.assertEqual(result.image.getpixel((65, 96)), (255, 255, 255, 255))
            self.assertEqual(builder.alpha_values(result.image), [0, 255])

    def test_low_alpha_halo_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = Image.open(make_master(root / "source.png", 3, "down")).convert("RGBA")
            alpha = source.getchannel("A")
            expanded = alpha.filter(ImageFilter.MaxFilter(9))
            halo_alpha = ImageChops.subtract(expanded, alpha).point(lambda value: 64 if value else 0)
            halo = Image.new("RGBA", source.size, (160, 90, 30, 0))
            halo.putalpha(halo_alpha)
            halo.alpha_composite(source)
            path = root / "halo.png"
            halo.save(path)
            result = builder.load_master_with_qa(path, "halo")
            self.assertEqual(result.method, "alpha-threshold")
            self.assertEqual(builder.alpha_values(result.image), [0, 255])
            self.assertGreater(result.removed_fraction, 0)

    def test_complex_background_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = Image.new("RGB", (320, 240), (18, 25, 35))
            draw = ImageDraw.Draw(image)
            for y in range(0, 240, 8):
                draw.line((0, y, 319, y), fill=(30 + y % 40, 35, 45))
            path = root / "complex.png"
            image.save(path)
            with self.assertRaisesRegex(builder.CharacterPackError, "complex or low-confidence"):
                builder.load_master_with_qa(path, "complex")

    def test_failed_production_row_can_be_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            production = make_production_sheet(root / "production.png", rows=2)
            transparent_right = make_master(root / "right-rgba.png", 4, "right")
            right = rgba_master_on_white(transparent_right, root / "right.png")
            pack = builder.build_character_pack(
                character_id="row-override",
                production_sheet_path=production,
                walk_right_path=right,
                output_dir=root / "output",
            )
            qa = json.loads((pack / "qa-report.json").read_text(encoding="utf-8"))
            self.assertTrue(qa["passed"])
            self.assertIn("right", qa["master_preprocessing"])

    def test_bundled_anonymous_template_regression(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = Path(__file__).resolve().parents[1] / "assets" / "walk-layout-template.png"
            pack = builder.build_character_pack(
                character_id="anonymous-template-regression",
                production_sheet_path=template,
                output_dir=root / "output",
            )
            qa = json.loads((pack / "qa-report.json").read_text(encoding="utf-8"))
            self.assertTrue(qa["passed"])
            self.assertEqual(qa["artifacts"]["down"]["dimensions"], [192, 64])
            self.assertLessEqual(qa["artifacts"]["right"]["opaque_color_count"], 64)

    def test_custom_cell_size_and_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = self.make_inputs(root)
            pack = builder.build_character_pack(
                character_id="small-person",
                turnaround_path=inputs["turnaround"],
                walk_down_path=inputs["down"],
                walk_up_path=inputs["up"],
                walk_right_path=inputs["right"],
                output_dir=root / "output",
                cell_size="32x48",
                frame_duration_ms=220,
            )
            manifest = json.loads((pack / "character.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["cell"], {"width": 32, "height": 48})
            self.assertEqual(manifest["frame_duration_ms"], 220)
            with Image.open(pack / manifest["directions"]["down"]["sheet_png"]) as sheet:
                self.assertEqual(sheet.size, (128, 48))


if __name__ == "__main__":
    unittest.main(verbosity=2)

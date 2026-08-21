#!/usr/bin/env python3
"""Generate anonymous, reproducible pixel-art references for this skill."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image, ImageDraw
except ImportError as exc:  # pragma: no cover - exercised only without Pillow
    raise SystemExit("Pillow is required to generate the bundled reference assets.") from exc

import build_character_pack as builder
import build_showcase_preview as showcase_preview


STYLE_BOARD_NAME = "beyond-walls-style-board.png"
WALK_TEMPLATE_NAME = "walk-layout-template.png"
SHOWCASE_SOURCE_NAME = "character-generation-showcase-source.png"
README_PREVIEW_NAME = showcase_preview.OVERVIEW_NAME
PREVIEW_CHARACTER_ID = "anonymous-readme-preview"
PREVIEW_FRAME_DURATION_MS = 170
UPSCALE = 4


def _rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str | tuple[int, ...]) -> None:
    draw.rectangle(box, fill=fill)


def _style_character(
    canvas: Image.Image,
    *,
    center_x: int,
    palette: tuple[str, str, str, str, str],
    hair_shape: int,
    outfit_shape: int,
) -> None:
    """Draw one deliberately generic chibi sprite with no real-person likeness."""
    outline, hair, skin, primary, accent = palette
    draw = ImageDraw.Draw(canvas)
    head = (center_x - 20, 18, center_x + 20, 58)
    draw.rounded_rectangle(head, radius=8, fill=outline)
    draw.rounded_rectangle((head[0] + 3, head[1] + 3, head[2] - 3, head[3] - 2), radius=6, fill=skin)

    if hair_shape == 0:
        draw.polygon(
            [(center_x - 20, 36), (center_x - 18, 16), (center_x + 17, 16),
             (center_x + 22, 35), (center_x + 13, 30), (center_x + 7, 39),
             (center_x, 29), (center_x - 8, 39), (center_x - 14, 30)],
            fill=hair,
        )
    elif hair_shape == 1:
        draw.ellipse((center_x - 23, 13, center_x + 22, 48), fill=outline)
        draw.ellipse((center_x - 20, 16, center_x + 19, 45), fill=hair)
        _rect(draw, (center_x - 21, 34, center_x - 16, 62), hair)
        _rect(draw, (center_x + 16, 34, center_x + 21, 62), hair)
    else:
        draw.polygon(
            [(center_x - 22, 35), (center_x - 16, 14), (center_x + 8, 13),
             (center_x + 21, 25), (center_x + 15, 37), (center_x + 6, 31),
             (center_x - 4, 38), (center_x - 12, 29)],
            fill=outline,
        )
        draw.polygon(
            [(center_x - 18, 33), (center_x - 13, 18), (center_x + 7, 17),
             (center_x + 17, 26), (center_x + 12, 33), (center_x + 5, 27),
             (center_x - 4, 34), (center_x - 11, 26)],
            fill=hair,
        )

    for eye_x in (center_x - 9, center_x + 7):
        _rect(draw, (eye_x - 3, 39, eye_x + 3, 48), outline)
        _rect(draw, (eye_x - 1, 40, eye_x + 2, 46), accent)
        _rect(draw, (eye_x, 40, eye_x + 1, 42), "white")
    _rect(draw, (center_x - 3, 52, center_x + 3, 54), accent)

    draw.rounded_rectangle((center_x - 17, 58, center_x + 17, 100), radius=4, fill=outline)
    if outfit_shape == 0:
        _rect(draw, (center_x - 14, 61, center_x + 14, 97), primary)
        _rect(draw, (center_x - 3, 61, center_x + 3, 91), accent)
    elif outfit_shape == 1:
        _rect(draw, (center_x - 14, 61, center_x + 14, 97), accent)
        _rect(draw, (center_x - 9, 73, center_x + 9, 97), primary)
        _rect(draw, (center_x - 12, 70, center_x + 12, 75), outline)
    else:
        _rect(draw, (center_x - 14, 61, center_x + 14, 97), primary)
        draw.polygon(
            [(center_x - 13, 62), (center_x, 79), (center_x + 13, 62),
             (center_x + 13, 72), (center_x, 88), (center_x - 13, 72)],
            fill=accent,
        )

    _rect(draw, (center_x - 21, 65, center_x - 17, 96), outline)
    _rect(draw, (center_x + 17, 65, center_x + 21, 96), outline)
    _rect(draw, (center_x - 20, 92, center_x - 17, 99), skin)
    _rect(draw, (center_x + 17, 92, center_x + 20, 99), skin)
    _rect(draw, (center_x - 14, 99, center_x - 2, 128), outline)
    _rect(draw, (center_x + 2, 99, center_x + 14, 128), outline)
    _rect(draw, (center_x - 11, 100, center_x - 3, 121), primary)
    _rect(draw, (center_x + 3, 100, center_x + 11, 121), primary)
    _rect(draw, (center_x - 15, 122, center_x - 2, 132), accent)
    _rect(draw, (center_x + 2, 122, center_x + 15, 132), accent)

    # Small block highlights keep the reference pixel-based rather than painterly.
    _rect(draw, (center_x - 12, 65, center_x - 8, 77), "#ffffff")
    _rect(draw, (center_x - 15, 20, center_x - 10, 29), "#ffffff")


def create_style_board() -> Image.Image:
    native = Image.new("RGB", (445, 144), "white")
    palettes = (
        ("#24183d", "#5f3dc4", "#f1b39b", "#285e9d", "#32c5b4"),
        ("#3b1b16", "#e56b1f", "#f3b18f", "#d7a62f", "#3f9b4b"),
        ("#15254c", "#1878d1", "#f0a18e", "#c73145", "#45c8e8"),
        ("#26152d", "#38203f", "#edac91", "#5a3f73", "#d59bd8"),
        ("#5a1c2e", "#e7b934", "#f2b49c", "#2879bb", "#e34f9a"),
        ("#4a1711", "#d9581f", "#efa68a", "#2f8a46", "#d52828"),
    )
    for index, palette in enumerate(palettes):
        _style_character(
            native,
            center_x=38 + index * 74,
            palette=palette,
            hair_shape=index % 3,
            outfit_shape=(index // 2) % 3,
        )
    return native.resize((1780, 576), Image.Resampling.NEAREST)


def _front_or_back_pose(direction: str, phase: str) -> Image.Image:
    image = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline, dark, mid, light = "#252525", "#555555", "#858585", "#b8b8b8"
    draw.rounded_rectangle((13, 3, 35, 25), radius=6, fill=outline)
    draw.rounded_rectangle((15, 5, 33, 24), radius=5, fill=light)
    if direction == "up":
        draw.ellipse((14, 3, 34, 21), fill=dark)
        _rect(draw, (15, 15, 33, 24), mid)
    else:
        draw.polygon([(14, 12), (16, 4), (33, 4), (35, 13), (29, 10), (24, 15), (19, 10)], fill=dark)
        _rect(draw, (18, 15, 21, 19), outline)
        _rect(draw, (27, 15, 30, 19), outline)
        _rect(draw, (19, 15, 20, 16), "white")
        _rect(draw, (28, 15, 29, 16), "white")
    _rect(draw, (17, 24, 31, 43), outline)
    _rect(draw, (19, 25, 29, 42), mid)

    if phase == "a":
        _rect(draw, (13, 27, 17, 43), light)
        _rect(draw, (31, 25, 35, 40), dark)
        _rect(draw, (19, 42, 23, 56), dark)
        _rect(draw, (26, 41, 30, 59), light)
        _rect(draw, (26, 57, 34, 61), outline)
        _rect(draw, (18, 54, 23, 58), outline)
    elif phase == "b":
        _rect(draw, (13, 25, 17, 40), dark)
        _rect(draw, (31, 27, 35, 43), light)
        _rect(draw, (18, 41, 22, 59), light)
        _rect(draw, (25, 42, 29, 56), dark)
        _rect(draw, (14, 57, 22, 61), outline)
        _rect(draw, (25, 54, 30, 58), outline)
    else:
        _rect(draw, (13, 26, 17, 42), mid)
        _rect(draw, (31, 26, 35, 42), mid)
        _rect(draw, (19, 42, 23, 58), dark)
        _rect(draw, (25, 42, 29, 58), dark)
        _rect(draw, (17, 57, 23, 61), outline)
        _rect(draw, (25, 57, 31, 61), outline)
    return image


def _right_pose(phase: str) -> Image.Image:
    image = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline, dark, mid, light = "#252525", "#505050", "#858585", "#bcbcbc"
    draw.rounded_rectangle((13, 4, 34, 25), radius=6, fill=outline)
    draw.rounded_rectangle((16, 6, 33, 23), radius=5, fill=light)
    draw.polygon([(13, 15), (15, 5), (30, 4), (35, 11), (30, 15), (25, 12), (20, 18)], fill=dark)
    _rect(draw, (31, 14, 36, 17), light)
    _rect(draw, (29, 13, 32, 17), outline)
    _rect(draw, (20, 24, 31, 43), outline)
    _rect(draw, (22, 25, 29, 42), mid)

    if phase == "a":
        _rect(draw, (17, 28, 21, 42), dark)
        _rect(draw, (17, 39, 22, 44), light)
        draw.polygon([(22, 41), (28, 41), (35, 56), (32, 59), (26, 52)], fill=light)
        _rect(draw, (31, 56, 39, 61), outline)
        draw.polygon([(21, 41), (25, 43), (19, 56), (14, 57), (18, 48)], fill=dark)
        _rect(draw, (12, 55, 20, 60), outline)
    elif phase == "b":
        _rect(draw, (30, 27, 34, 41), light)
        _rect(draw, (31, 38, 36, 44), light)
        draw.polygon([(22, 41), (27, 42), (20, 56), (15, 58), (18, 49)], fill=light)
        _rect(draw, (12, 56, 21, 61), outline)
        draw.polygon([(25, 42), (29, 41), (35, 55), (38, 57), (31, 58)], fill=dark)
        _rect(draw, (32, 55, 40, 60), outline)
    else:
        _rect(draw, (18, 27, 22, 42), mid)
        _rect(draw, (22, 42, 26, 58), dark)
        _rect(draw, (27, 42, 30, 58), mid)
        _rect(draw, (19, 57, 27, 61), outline)
        _rect(draw, (26, 57, 33, 61), outline)
    return image


def create_walk_template() -> Image.Image:
    native = Image.new("RGB", (48 * 4, 64 * 3), "white")
    phases = ("neutral", "a", "neutral", "b")
    for row, direction in enumerate(("down", "up", "right")):
        for column, phase in enumerate(phases):
            pose = _right_pose(phase) if direction == "right" else _front_or_back_pose(direction, phase)
            native.paste(pose.convert("RGB"), (column * 48, row * 64), pose.getchannel("A"))
    return native.resize((768, 768), Image.Resampling.NEAREST)


def _colored_front_or_back_pose(direction: str, phase: str) -> Image.Image:
    """Draw a colorful anonymous pose while preserving the validated gait geometry."""
    image = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline = "#24183d"
    hair = "#3b294f"
    skin = "#f1b39b"
    jacket = "#2879bb"
    jacket_light = "#45c8e8"
    trousers = "#3c4d78"
    far_limb = "#2f3157"
    shoes = "#4a2c28"

    draw.rounded_rectangle((13, 3, 35, 25), radius=6, fill=outline)
    draw.rounded_rectangle((15, 5, 33, 24), radius=5, fill=skin)
    if direction == "up":
        draw.ellipse((14, 3, 34, 21), fill=hair)
        _rect(draw, (15, 15, 33, 24), hair)
    else:
        draw.polygon(
            [(14, 12), (16, 4), (33, 4), (35, 13), (29, 10), (24, 15), (19, 10)],
            fill=hair,
        )
        _rect(draw, (18, 15, 21, 19), outline)
        _rect(draw, (27, 15, 30, 19), outline)
        _rect(draw, (19, 15, 20, 16), "white")
        _rect(draw, (28, 15, 29, 16), "white")
    _rect(draw, (17, 24, 31, 43), outline)
    _rect(draw, (19, 25, 29, 42), jacket)
    _rect(draw, (20, 26, 22, 38), jacket_light)

    if phase == "a":
        _rect(draw, (13, 27, 17, 43), jacket_light)
        _rect(draw, (31, 25, 35, 40), jacket)
        _rect(draw, (19, 42, 23, 56), far_limb)
        _rect(draw, (26, 41, 30, 59), trousers)
        _rect(draw, (26, 57, 34, 61), shoes)
        _rect(draw, (18, 54, 23, 58), shoes)
    elif phase == "b":
        _rect(draw, (13, 25, 17, 40), jacket)
        _rect(draw, (31, 27, 35, 43), jacket_light)
        _rect(draw, (18, 41, 22, 59), trousers)
        _rect(draw, (25, 42, 29, 56), far_limb)
        _rect(draw, (14, 57, 22, 61), shoes)
        _rect(draw, (25, 54, 30, 58), shoes)
    else:
        _rect(draw, (13, 26, 17, 42), jacket)
        _rect(draw, (31, 26, 35, 42), jacket)
        _rect(draw, (19, 42, 23, 58), trousers)
        _rect(draw, (25, 42, 29, 58), far_limb)
        _rect(draw, (17, 57, 23, 61), shoes)
        _rect(draw, (25, 57, 31, 61), shoes)
    return image


def _colored_right_pose(phase: str) -> Image.Image:
    image = Image.new("RGBA", (48, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    outline = "#24183d"
    hair = "#3b294f"
    skin = "#f1b39b"
    jacket = "#2879bb"
    jacket_light = "#45c8e8"
    trousers = "#3c4d78"
    far_limb = "#2f3157"
    shoes = "#4a2c28"

    draw.rounded_rectangle((13, 4, 34, 25), radius=6, fill=outline)
    draw.rounded_rectangle((16, 6, 33, 23), radius=5, fill=skin)
    draw.polygon(
        [(13, 15), (15, 5), (30, 4), (35, 11), (30, 15), (25, 12), (20, 18)],
        fill=hair,
    )
    _rect(draw, (31, 14, 36, 17), skin)
    _rect(draw, (29, 13, 32, 17), outline)
    _rect(draw, (20, 24, 31, 43), outline)
    _rect(draw, (22, 25, 29, 42), jacket)
    _rect(draw, (23, 26, 24, 38), jacket_light)

    if phase == "a":
        _rect(draw, (17, 28, 21, 42), jacket)
        _rect(draw, (17, 39, 22, 44), skin)
        draw.polygon([(22, 41), (28, 41), (35, 56), (32, 59), (26, 52)], fill=trousers)
        _rect(draw, (31, 56, 39, 61), shoes)
        draw.polygon([(21, 41), (25, 43), (19, 56), (14, 57), (18, 48)], fill=far_limb)
        _rect(draw, (12, 55, 20, 60), shoes)
    elif phase == "b":
        _rect(draw, (30, 27, 34, 41), jacket_light)
        _rect(draw, (31, 38, 36, 44), skin)
        draw.polygon([(22, 41), (27, 42), (20, 56), (15, 58), (18, 49)], fill=trousers)
        _rect(draw, (12, 56, 21, 61), shoes)
        draw.polygon([(25, 42), (29, 41), (35, 55), (38, 57), (31, 58)], fill=far_limb)
        _rect(draw, (32, 55, 40, 60), shoes)
    else:
        _rect(draw, (18, 27, 22, 42), jacket)
        _rect(draw, (22, 42, 26, 58), trousers)
        _rect(draw, (27, 42, 30, 58), far_limb)
        _rect(draw, (19, 57, 27, 61), shoes)
        _rect(draw, (26, 57, 33, 61), shoes)
    return image


def create_preview_production_sheet() -> Image.Image:
    """Create the anonymous colored 3x4 sheet consumed by the production builder."""
    native = Image.new("RGB", (48 * 4, 64 * 3), "white")
    phases = ("neutral", "a", "neutral", "b")
    for row, direction in enumerate(("down", "up", "right")):
        for column, phase in enumerate(phases):
            pose = (
                _colored_right_pose(phase)
                if direction == "right"
                else _colored_front_or_back_pose(direction, phase)
            )
            native.paste(pose.convert("RGB"), (column * 48, row * 64), pose.getchannel("A"))
    return native.resize((768, 768), Image.Resampling.NEAREST)


def _generate_anonymous_preview(destination: Path) -> dict[str, Path]:
    """Build the anonymous fallback used when the showcase sheet is unavailable."""
    with tempfile.TemporaryDirectory(prefix="character-generation-preview-") as temp:
        temp_root = Path(temp)
        production_sheet = temp_root / "production-sheet.png"
        create_preview_production_sheet().save(production_sheet, format="PNG", optimize=True)
        pack = builder.build_character_pack(
            character_id=PREVIEW_CHARACTER_ID,
            production_sheet_path=production_sheet,
            output_dir=temp_root / "output",
            frame_duration_ms=PREVIEW_FRAME_DURATION_MS,
        )
        overview = pack / "animations" / f"{PREVIEW_CHARACTER_ID}_walk_overview.gif"
        preview_path = destination / README_PREVIEW_NAME
        shutil.copyfile(overview, preview_path)
        return {"overview": preview_path}


def _generate_readme_previews(destination: Path) -> dict[str, Path]:
    """Regenerate the public directional GIFs from the bundled showcase sheet."""
    source = Path(__file__).resolve().parents[1] / "assets" / SHOWCASE_SOURCE_NAME
    if not source.is_file():
        return _generate_anonymous_preview(destination)
    canonical_source = destination / SHOWCASE_SOURCE_NAME
    canonical = showcase_preview.canonicalize_showcase_sheet(source)
    canonical.save(canonical_source, format="PNG", optimize=True, compress_level=9)
    previews = showcase_preview.build_showcase_preview(
        canonical_source,
        destination,
        frame_duration_ms=PREVIEW_FRAME_DURATION_MS,
    )
    return {"source": canonical_source, **previews}


def generate_assets(output_dir: str | Path) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    assets = {
        STYLE_BOARD_NAME: create_style_board(),
        WALK_TEMPLATE_NAME: create_walk_template(),
    }
    paths: dict[str, Path] = {}
    for name, image in assets.items():
        path = destination / name
        image.save(path, format="PNG", optimize=True)
        paths[name] = path
    for preview_path in _generate_readme_previews(destination).values():
        paths[preview_path.name] = preview_path
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate anonymous reference assets.")
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "assets"),
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for path in generate_assets(args.output_dir).values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

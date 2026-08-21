#!/usr/bin/env python3
"""Build README-ready directional GIFs from a validated 3x4 character sheet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageOps

import build_character_pack as builder


DEFAULT_CELL_SIZE = "192x256"
DEFAULT_FRAME_DURATION_MS = 170
DEFAULT_PALETTE_COLORS = 64
OVERVIEW_NAME = "character-generation-preview.gif"
DIRECTION_NAMES = {
    "down": "character-generation-preview-forward.gif",
    "up": "character-generation-preview-backward.gif",
    "right": "character-generation-preview-right.gif",
    "left": "character-generation-preview-left.gif",
}


def _load_generated_groups(
    production_sheet_path: str | Path,
    cell_size: str,
) -> tuple[dict[str, list[Image.Image]], builder.MasterCleanupResult]:
    width, height = builder.parse_cell_size(cell_size)
    cleanup = builder.load_master_with_qa(production_sheet_path, "showcase-production")
    production = builder.split_production_sheet(cleanup.image)
    missing = [direction for direction in builder.GENERATED_DIRECTIONS if direction not in production.groups]
    if missing:
        details = "; ".join(
            f"{direction}: {production.errors.get(direction, 'missing row')}" for direction in missing
        )
        raise builder.CharacterPackError(f"showcase sheet could not be segmented: {details}")

    cell = builder.make_cell_spec(width, height)
    groups: dict[str, list[Image.Image]] = {}
    for direction in builder.GENERATED_DIRECTIONS:
        frames = [builder.normalize_pose(pose, cell) for pose in production.groups[direction].poses]
        frames[2] = frames[0].copy()
        groups[direction] = frames
    return groups, cleanup


def canonicalize_showcase_sheet(
    production_sheet_path: str | Path,
    *,
    cell_size: str = DEFAULT_CELL_SIZE,
    palette_colors: int = DEFAULT_PALETTE_COLORS,
) -> Image.Image:
    """Normalize a source sheet into the compact, reproducible 3x4 repository form."""
    width, height = builder.parse_cell_size(cell_size)
    groups, _ = _load_generated_groups(production_sheet_path, cell_size)
    groups = builder.apply_shared_palette(groups, palette_colors)
    sheet = Image.new("RGBA", (width * 4, height * 3), (0, 0, 0, 0))
    for row, direction in enumerate(builder.GENERATED_DIRECTIONS):
        for column, frame in enumerate(groups[direction]):
            sheet.alpha_composite(frame, (column * width, row * height))
    return sheet


def _validate_groups(groups: dict[str, list[Image.Image]]) -> None:
    for direction in builder.DIRECTIONS:
        frames = groups[direction]
        if len(frames) != 4:
            raise builder.CharacterPackError(f"{direction} preview must contain four frames")
        if ImageChops.difference(frames[0], frames[2]).getbbox() is not None:
            raise builder.CharacterPackError(f"{direction} neutral frames must be identical")
        if builder.frame_difference_ratio(frames[0], frames[1]) <= 0.005:
            raise builder.CharacterPackError(f"{direction} gait-A is indistinguishable from neutral")
        if builder.frame_difference_ratio(frames[1], frames[3]) <= 0.005:
            raise builder.CharacterPackError(f"{direction} gait phases are indistinguishable")
        for frame in frames:
            alpha = frame.getchannel("A")
            binary = alpha.point(lambda value: 255 if value else 0)
            if ImageChops.difference(alpha, binary).getbbox() is not None:
                raise builder.CharacterPackError(f"{direction} preview contains non-binary alpha")


def build_showcase_preview(
    production_sheet_path: str | Path,
    output_dir: str | Path,
    *,
    cell_size: str = DEFAULT_CELL_SIZE,
    frame_duration_ms: int = DEFAULT_FRAME_DURATION_MS,
    palette_colors: int = DEFAULT_PALETTE_COLORS,
) -> dict[str, Path]:
    """Create four direction GIFs and one 2x2 overview without weakening pack QA."""
    width, height = builder.parse_cell_size(cell_size)
    if frame_duration_ms < 20 or frame_duration_ms > 5000:
        raise builder.CharacterPackError("frame duration must be between 20 and 5000 milliseconds")

    groups, _ = _load_generated_groups(production_sheet_path, cell_size)
    groups["left"] = [ImageOps.mirror(frame) for frame in groups["right"]]
    groups = builder.apply_shared_palette(groups, palette_colors)
    _validate_groups(groups)

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for direction in builder.DIRECTIONS:
        path = destination / DIRECTION_NAMES[direction]
        builder.save_gif(groups[direction], path, frame_duration_ms)
        qa = builder.animation_qa(path, 4, (width, height))
        if not qa["passed"]:
            raise builder.CharacterPackError(f"{direction} preview GIF failed animation QA")
        paths[direction] = path

    overview = destination / OVERVIEW_NAME
    builder.save_gif(builder.make_overview_frames(groups, scale=1), overview, frame_duration_ms)
    overview_qa = builder.animation_qa(overview, 4, (width * 2, height * 2))
    if not overview_qa["passed"]:
        raise builder.CharacterPackError("overview preview GIF failed animation QA")
    paths["overview"] = overview
    return paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build directional README preview GIFs.")
    parser.add_argument("--production-sheet", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cell-size", default=DEFAULT_CELL_SIZE)
    parser.add_argument("--frame-duration", type=int, default=DEFAULT_FRAME_DURATION_MS)
    parser.add_argument("--palette-colors", type=int, default=DEFAULT_PALETTE_COLORS)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = build_showcase_preview(
            args.production_sheet,
            args.output_dir,
            cell_size=args.cell_size,
            frame_duration_ms=args.frame_duration,
            palette_colors=args.palette_colors,
        )
    except (builder.CharacterPackError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({name: str(path) for name, path in paths.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

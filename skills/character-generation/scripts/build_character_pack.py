#!/usr/bin/env python3
"""Build a deterministic, engine-agnostic pixel character pack from masters."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

try:
    from PIL import Image, ImageChops, ImageOps
except ImportError as exc:  # pragma: no cover - exercised only without Pillow
    raise SystemExit(
        "Pillow is required. Install it in the active Python environment before running the builder."
    ) from exc


SCHEMA_VERSION = 1
STYLE_PROFILE = "create-world-bright-chibi-v1"
FRAME_ORDER = ["neutral", "left-step", "neutral", "right-step"]
DIRECTIONS = ("down", "up", "right", "left")
GENERATED_DIRECTIONS = ("down", "up", "right")
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_.][a-z0-9]+)*$")
CELL_PATTERN = re.compile(r"^(\d+)[xX](\d+)$")
ALPHA_THRESHOLD = 128
LEG_BAND_FRACTION = 0.18
MIN_DOMINANT_FOOT_OFFSET = 0.015
SIDE_LOWER_BODY_START = 0.55
SIDE_FEATURE_SIZE = (24, 24)
MIN_SIDE_PHASE_CONFIDENCE = 0.05
POSE_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "assets" / "walk-layout-template.png"


class CharacterPackError(ValueError):
    """Raised when an input master or pack option violates the contract."""


@dataclass(frozen=True)
class CellSpec:
    width: int
    height: int
    anchor_x: int
    baseline_y: int


@dataclass(frozen=True)
class SegmentationResult:
    poses: list[Image.Image]
    method: str
    source_size: tuple[int, int]
    subject_bboxes: list[tuple[int, int, int, int]]


@dataclass(frozen=True)
class MasterCleanupResult:
    image: Image.Image
    method: str
    confidence: float
    border_background_fraction: float
    removed_fraction: float


@dataclass(frozen=True)
class ProductionSheetResult:
    groups: dict[str, SegmentationResult]
    method: str
    source_size: tuple[int, int]
    row_bands: list[tuple[int, int]]
    errors: dict[str, str]


def parse_cell_size(value: str) -> tuple[int, int]:
    match = CELL_PATTERN.fullmatch(value.strip())
    if not match:
        raise CharacterPackError("cell-size must use WIDTHxHEIGHT, for example 48x64")
    width, height = (int(match.group(1)), int(match.group(2)))
    if width < 16 or height < 16 or width > 512 or height > 512:
        raise CharacterPackError("cell-size dimensions must each be between 16 and 512 pixels")
    return width, height


def validate_character_id(character_id: str) -> str:
    value = character_id.strip()
    if not ID_PATTERN.fullmatch(value):
        raise CharacterPackError(
            "character-id must contain lowercase ASCII letters or digits separated by -, _, or ."
        )
    return value


def make_cell_spec(width: int, height: int) -> CellSpec:
    bottom_margin = max(1, round(height * 3 / 64))
    return CellSpec(
        width=width,
        height=height,
        anchor_x=width // 2,
        baseline_y=height - bottom_margin,
    )


def _border_opaque_fraction(alpha: Image.Image) -> float:
    width, height = alpha.size
    border = Image.new("L", (width * 2 + max(0, height - 2) * 2, 1), 0)
    offset = 0
    for strip in (
        alpha.crop((0, 0, width, 1)),
        alpha.crop((0, height - 1, width, height)),
        alpha.crop((0, 1, 1, height - 1)).resize((max(0, height - 2), 1)),
        alpha.crop((width - 1, 1, width, height - 1)).resize((max(0, height - 2), 1)),
    ):
        if strip.width:
            border.paste(strip, (offset, 0))
            offset += strip.width
    histogram = border.histogram()
    opaque = sum(histogram[ALPHA_THRESHOLD:])
    return opaque / max(1, border.width)


def _binary_alpha(image: Image.Image) -> Image.Image:
    return image.getchannel("A").point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0)


def _clean_from_alpha(image: Image.Image, label: str) -> MasterCleanupResult:
    alpha = image.getchannel("A")
    minimum, maximum = alpha.getextrema()
    if maximum == 0:
        raise CharacterPackError(f"{label} master is fully transparent")

    binary = alpha.point(lambda value: 255 if value >= ALPHA_THRESHOLD else 0)
    if binary.getbbox() is None:
        raise CharacterPackError(f"{label} master has no visible pixels after alpha cleanup")

    border_opaque = _border_opaque_fraction(binary)
    if border_opaque > 0.25:
        return _clean_from_light_edge_background(image.convert("RGB"), label, "alpha-fallback")

    cleaned = Image.new("RGBA", image.size, (0, 0, 0, 0))
    cleaned.paste(image.convert("RGB"), mask=binary)
    histogram = alpha.histogram()
    low_alpha = sum(histogram[1:ALPHA_THRESHOLD])
    removed = low_alpha / max(1, image.width * image.height)
    return MasterCleanupResult(
        image=cleaned,
        method="alpha-threshold",
        confidence=round(1.0 - border_opaque, 6),
        border_background_fraction=round(1.0 - border_opaque, 6),
        removed_fraction=round(removed, 6),
    )


def _light_neutral(pixel: tuple[int, int, int]) -> bool:
    minimum = min(pixel)
    maximum = max(pixel)
    return minimum >= 195 and maximum - minimum <= 42


def _border_indices(width: int, height: int) -> list[int]:
    if width <= 0 or height <= 0:
        return []
    indices = list(range(width))
    if height > 1:
        indices.extend((height - 1) * width + x for x in range(width))
    if height > 2:
        indices.extend(y * width for y in range(1, height - 1))
        if width > 1:
            indices.extend(y * width + width - 1 for y in range(1, height - 1))
    return indices


def _clean_from_light_edge_background(
    image: Image.Image,
    label: str,
    method_prefix: str = "rgb",
) -> MasterCleanupResult:
    rgb = image.convert("RGB")
    width, height = rgb.size
    raw_pixels = iter(rgb.tobytes())
    candidate = bytearray(
        1 if _light_neutral((red, green, blue)) else 0
        for red, green, blue in zip(raw_pixels, raw_pixels, raw_pixels)
    )
    border = _border_indices(width, height)
    border_candidates = sum(candidate[index] for index in border)
    border_fraction = border_candidates / max(1, len(border))
    if border_fraction < 0.70:
        raise CharacterPackError(
            f"{label} master has a complex or low-confidence background; use a plain white canvas"
        )

    connected = bytearray(width * height)
    queue: deque[int] = deque()
    for index in border:
        if candidate[index] and not connected[index]:
            connected[index] = 1
            queue.append(index)

    while queue:
        index = queue.popleft()
        x = index % width
        if x > 0:
            neighbor = index - 1
            if candidate[neighbor] and not connected[neighbor]:
                connected[neighbor] = 1
                queue.append(neighbor)
        if x + 1 < width:
            neighbor = index + 1
            if candidate[neighbor] and not connected[neighbor]:
                connected[neighbor] = 1
                queue.append(neighbor)
        if index >= width:
            neighbor = index - width
            if candidate[neighbor] and not connected[neighbor]:
                connected[neighbor] = 1
                queue.append(neighbor)
        if index + width < width * height:
            neighbor = index + width
            if candidate[neighbor] and not connected[neighbor]:
                connected[neighbor] = 1
                queue.append(neighbor)

    removed_count = sum(connected)
    candidate_count = sum(candidate)
    removed_fraction = removed_count / max(1, width * height)
    connectivity = removed_count / max(1, candidate_count)
    confidence = min(border_fraction, connectivity)
    if removed_fraction < 0.20 or removed_fraction >= 0.995 or confidence < 0.80:
        raise CharacterPackError(
            f"{label} master background cleanup confidence is too low; use a plain white canvas"
        )

    alpha = Image.frombytes(
        "L",
        (width, height),
        bytes(0 if value else 255 for value in connected),
    )
    if alpha.getbbox() is None:
        raise CharacterPackError(f"{label} master contains no subject after background cleanup")
    if _border_opaque_fraction(alpha) > 0.02:
        raise CharacterPackError(f"{label} master subject touches the canvas border")

    cleaned = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    cleaned.paste(rgb, mask=alpha)
    method = f"{method_prefix}-light-neutral-flood"
    return MasterCleanupResult(
        image=cleaned,
        method=method,
        confidence=round(confidence, 6),
        border_background_fraction=round(border_fraction, 6),
        removed_fraction=round(removed_fraction, 6),
    )


def load_master_with_qa(path: str | Path, label: str) -> MasterCleanupResult:
    source = Path(path)
    if not source.is_file():
        raise CharacterPackError(f"{label} master not found: {source}")

    with Image.open(source) as raw:
        has_alpha = "A" in raw.getbands() or "transparency" in raw.info
        if has_alpha:
            image = raw.convert("RGBA")
            minimum, maximum = image.getchannel("A").getextrema()
            if maximum == 0:
                raise CharacterPackError(f"{label} master is fully transparent")
            if minimum < 255:
                return _clean_from_alpha(image, label)
            return _clean_from_light_edge_background(image.convert("RGB"), label, "opaque-alpha")
        return _clean_from_light_edge_background(raw.convert("RGB"), label)


def load_master(path: str | Path, label: str) -> Image.Image:
    return load_master_with_qa(path, label).image


def _projection_runs(projection: Sequence[int], gap_limit: int, min_width: int) -> list[tuple[int, int]]:
    occupied = [bool(value) for value in projection]
    index = 0
    while index < len(occupied):
        if occupied[index]:
            index += 1
            continue
        start = index
        while index < len(occupied) and not occupied[index]:
            index += 1
        if start > 0 and index < len(occupied) and index - start <= gap_limit:
            occupied[start:index] = [True] * (index - start)

    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(occupied):
        if not occupied[index]:
            index += 1
            continue
        start = index
        while index < len(occupied) and occupied[index]:
            index += 1
        if index - start >= min_width:
            runs.append((start, index))
    return runs


def _boxes_from_projection(image: Image.Image, expected: int) -> list[tuple[int, int, int, int]]:
    mask = _binary_alpha(image)
    x_projection, _ = mask.getprojection()
    runs = _projection_runs(
        x_projection,
        gap_limit=max(1, image.width // 256),
        min_width=max(2, image.width // 256),
    )
    if len(runs) != expected:
        return []

    boxes: list[tuple[int, int, int, int]] = []
    for left, right in runs:
        local_bbox = mask.crop((left, 0, right, image.height)).getbbox()
        if local_bbox is None:
            return []
        boxes.append((left + local_bbox[0], local_bbox[1], left + local_bbox[2], local_bbox[3]))
    return boxes


def _boxes_from_equal_cells(image: Image.Image, expected: int) -> list[tuple[int, int, int, int]]:
    mask = _binary_alpha(image)
    boxes: list[tuple[int, int, int, int]] = []
    for index in range(expected):
        left = round(index * image.width / expected)
        right = round((index + 1) * image.width / expected)
        local_bbox = mask.crop((left, 0, right, image.height)).getbbox()
        if local_bbox is None:
            return []
        if local_bbox[0] == 0 or local_bbox[2] == right - left:
            return []
        boxes.append((left + local_bbox[0], local_bbox[1], left + local_bbox[2], local_bbox[3]))
    return boxes


def split_subjects(image: Image.Image, expected: int, label: str) -> SegmentationResult:
    boxes = _boxes_from_projection(image, expected)
    method = "alpha-projection"
    if not boxes:
        boxes = _boxes_from_equal_cells(image, expected)
        method = "equal-columns"
    if len(boxes) != expected:
        raise CharacterPackError(
            f"{label} master must contain exactly {expected} separated subjects on transparency"
        )

    poses = [image.crop(box).convert("RGBA") for box in boxes]
    return SegmentationResult(
        poses=poses,
        method=method,
        source_size=image.size,
        subject_bboxes=boxes,
    )


def _row_bands(image: Image.Image) -> tuple[list[tuple[int, int]], str]:
    mask = _binary_alpha(image)
    _, y_projection = mask.getprojection()
    runs = _projection_runs(
        y_projection,
        gap_limit=max(1, image.height // 128),
        min_width=max(2, image.height // 64),
    )
    if len(runs) == 3:
        return runs, "alpha-projection"
    return [
        (round(index * image.height / 3), round((index + 1) * image.height / 3))
        for index in range(3)
    ], "equal-rows"


def split_production_sheet(image: Image.Image) -> ProductionSheetResult:
    bands, method = _row_bands(image)
    groups: dict[str, SegmentationResult] = {}
    errors: dict[str, str] = {}

    for direction, (top, bottom) in zip(GENERATED_DIRECTIONS, bands):
        row = image.crop((0, top, image.width, bottom)).convert("RGBA")
        try:
            result = split_subjects(row, 4, f"production-{direction}")
        except CharacterPackError as exc:
            errors[direction] = str(exc)
            continue
        absolute_boxes = [
            (left, local_top + top, right, local_bottom + top)
            for left, local_top, right, local_bottom in result.subject_bboxes
        ]
        groups[direction] = SegmentationResult(
            poses=result.poses,
            method=f"{method}/{result.method}",
            source_size=image.size,
            subject_bboxes=absolute_boxes,
        )

    return ProductionSheetResult(
        groups=groups,
        method=method,
        source_size=image.size,
        row_bands=bands,
        errors=errors,
    )


def compose_pose_master(poses: Sequence[Image.Image]) -> Image.Image:
    if not poses:
        raise CharacterPackError("cannot compose a master from zero poses")
    cropped: list[Image.Image] = []
    for pose in poses:
        bbox = _binary_alpha(pose).getbbox()
        if bbox is None:
            raise CharacterPackError("encountered an empty pose while composing a master")
        cropped.append(pose.crop(bbox).convert("RGBA"))
    maximum_width = max(pose.width for pose in cropped)
    maximum_height = max(pose.height for pose in cropped)
    gutter = max(8, maximum_width // 4)
    width = sum(pose.width for pose in cropped) + gutter * (len(cropped) + 1)
    height = maximum_height + gutter * 2
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    x = gutter
    for pose in cropped:
        canvas.alpha_composite(pose, (x, gutter + maximum_height - pose.height))
        x += pose.width + gutter
    return canvas


def normalize_pose(pose: Image.Image, cell: CellSpec) -> Image.Image:
    bbox = _binary_alpha(pose).getbbox()
    if bbox is None:
        raise CharacterPackError("encountered an empty pose while normalizing")
    cropped = pose.crop(bbox).convert("RGBA")

    top_margin = max(1, round(cell.height * 3 / 64))
    side_margin = max(1, round(cell.width * 3 / 48))
    max_height = max(1, cell.baseline_y - top_margin)
    max_width = max(1, cell.width - side_margin * 2)
    scale = min(max_width / cropped.width, max_height / cropped.height)
    new_width = max(1, round(cropped.width * scale))
    new_height = max(1, round(cropped.height * scale))
    resized = cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
    resized.putalpha(_binary_alpha(resized))

    canvas = Image.new("RGBA", (cell.width, cell.height), (0, 0, 0, 0))
    x = cell.anchor_x - new_width // 2
    y = cell.baseline_y - new_height
    if x < 0 or y < 0 or x + new_width > cell.width:
        raise CharacterPackError("pose cannot fit inside the requested cell size")
    canvas.alpha_composite(resized, (x, y))
    return canvas


def _palette_atlas(frames: Sequence[Image.Image]) -> Image.Image:
    if not frames:
        raise CharacterPackError("cannot build a palette from zero frames")
    width = max(frame.width for frame in frames)
    height = max(frame.height for frame in frames)
    atlas = Image.new("RGBA", (width * len(frames), height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        atlas.alpha_composite(frame, (index * width, 0))
    return atlas


def apply_shared_palette(
    groups: dict[str, list[Image.Image]], colors: int
) -> dict[str, list[Image.Image]]:
    if colors < 2 or colors > 256:
        raise CharacterPackError("palette-colors must be between 2 and 256")
    source_frames = [frame for frames in groups.values() for frame in frames]
    palette = _palette_atlas(source_frames).convert("RGB").quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )

    result: dict[str, list[Image.Image]] = {}
    for name, frames in groups.items():
        result[name] = []
        for frame in frames:
            alpha = _binary_alpha(frame)
            quantized_rgb = frame.convert("RGB").quantize(
                palette=palette,
                dither=Image.Dither.NONE,
            ).convert("RGB")
            quantized = quantized_rgb.convert("RGBA")
            quantized.putalpha(alpha)
            result[name].append(quantized)
    return result


def make_sheet(frames: Sequence[Image.Image]) -> Image.Image:
    if not frames:
        raise CharacterPackError("cannot build a sprite sheet from zero frames")
    width, height = frames[0].size
    if any(frame.size != (width, height) for frame in frames):
        raise CharacterPackError("all frames in a sheet must share one cell size")
    sheet = Image.new("RGBA", (width * len(frames), height), (0, 0, 0, 0))
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * width, 0))
    return sheet


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True, compress_level=9)


def save_webp(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="WEBP", lossless=True, quality=100, method=6, exact=True)


def save_apng(frames: Sequence[Image.Image], path: Path, duration_ms: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        format="PNG",
        save_all=True,
        append_images=list(frames[1:]),
        duration=duration_ms,
        loop=0,
        disposal=0,
        blend=0,
        optimize=False,
    )


def _gif_frame(image: Image.Image) -> Image.Image:
    alpha = _binary_alpha(image)
    frame = image.convert("RGB").quantize(
        colors=255,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    transparent_mask = alpha.point(lambda value: 255 if value == 0 else 0)
    frame.paste(255, mask=transparent_mask)
    palette = frame.getpalette() or [0] * 768
    palette[255 * 3 : 255 * 3 + 3] = [0, 0, 0]
    frame.putpalette(palette)
    frame.info["transparency"] = 255
    frame.info["disposal"] = 2
    return frame


def make_overview_frames(groups: dict[str, list[Image.Image]], scale: int = 4) -> list[Image.Image]:
    cell_width, cell_height = groups["down"][0].size
    positions = {
        "down": (0, 0),
        "up": (cell_width, 0),
        "right": (0, cell_height),
        "left": (cell_width, cell_height),
    }
    frames: list[Image.Image] = []
    for frame_index in range(4):
        canvas = Image.new("RGBA", (cell_width * 2, cell_height * 2), (0, 0, 0, 0))
        for direction in DIRECTIONS:
            canvas.alpha_composite(groups[direction][frame_index], positions[direction])
        frames.append(
            canvas.resize((canvas.width * scale, canvas.height * scale), Image.Resampling.NEAREST)
        )
    return frames


def save_gif(frames: Sequence[Image.Image], path: Path, duration_ms: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    converted = [_gif_frame(frame) for frame in frames]
    converted[0].save(
        path,
        format="GIF",
        save_all=True,
        append_images=converted[1:],
        duration=duration_ms,
        loop=0,
        transparency=255,
        disposal=2,
        optimize=False,
    )


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def alpha_values(image: Image.Image) -> list[int]:
    histogram = image.getchannel("A").histogram()
    return [index for index, count in enumerate(histogram) if count]


def opaque_color_count(image: Image.Image) -> int:
    colors = image.getcolors(maxcolors=image.width * image.height)
    if colors is None:
        return image.width * image.height + 1
    return len({rgba[:3] for _, rgba in colors if rgba[3] == 255})


def sheet_qa(
    image: Image.Image,
    frame_count: int,
    cell: CellSpec,
    palette_colors: int,
) -> dict[str, object]:
    frames: list[dict[str, object]] = []
    for index in range(frame_count):
        frame = image.crop((index * cell.width, 0, (index + 1) * cell.width, cell.height))
        bbox = _binary_alpha(frame).getbbox()
        clipped = bbox is None or bbox[0] == 0 or bbox[1] == 0 or bbox[2] == cell.width or bbox[3] > cell.baseline_y
        baseline_aligned = bbox is not None and bbox[3] == cell.baseline_y
        frames.append(
            {
                "index": index,
                "bbox": list(bbox) if bbox else None,
                "baseline_aligned": baseline_aligned,
                "clipped": clipped,
            }
        )

    values = alpha_values(image)
    color_count = opaque_color_count(image)
    dimensions_ok = image.size == (cell.width * frame_count, cell.height)
    passed = (
        dimensions_ok
        and set(values).issubset({0, 255})
        and color_count <= palette_colors
        and all(not frame["clipped"] and frame["baseline_aligned"] for frame in frames)
    )
    return {
        "dimensions": [image.width, image.height],
        "dimensions_ok": dimensions_ok,
        "alpha_values": values,
        "opaque_color_count": color_count,
        "palette_limit": palette_colors,
        "frames": frames,
        "passed": passed,
    }


def frame_difference_ratio(first: Image.Image, second: Image.Image) -> float:
    if first.size != second.size:
        return 1.0
    difference = ImageChops.difference(first.convert("RGBA"), second.convert("RGBA"))
    changed = sum(difference.convert("L").point(lambda value: 255 if value else 0).histogram()[1:])
    union_alpha = ImageChops.lighter(first.getchannel("A"), second.getchannel("A"))
    visible = sum(union_alpha.point(lambda value: 255 if value else 0).histogram()[1:])
    return round(changed / max(1, visible), 6)


def dominant_foot_offset(frame: Image.Image) -> float | None:
    """Return the bottom-band opaque centroid relative to the subject center/width."""
    alpha = _binary_alpha(frame)
    bbox = alpha.getbbox()
    if bbox is None:
        return None
    left, top, right, bottom = bbox
    subject_width = right - left
    subject_height = bottom - top
    band_height = max(1, round(subject_height * LEG_BAND_FRACTION))
    band = alpha.crop((left, max(top, bottom - band_height), right, bottom))
    pixels = band.load()
    opaque_count = 0
    weighted_x = 0.0
    for y in range(band.height):
        for x in range(band.width):
            if pixels[x, y]:
                opaque_count += 1
                weighted_x += x + 0.5
    if opaque_count == 0:
        return None
    mean_x = left + weighted_x / opaque_count
    subject_center = (left + right) / 2
    return round((mean_x - subject_center) / max(1, subject_width), 6)


def _lower_body_feature(frame: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgba = frame.convert("RGBA")
    alpha = _binary_alpha(rgba)
    bbox = alpha.getbbox()
    if bbox is None:
        blank = Image.new("L", SIDE_FEATURE_SIZE, 0)
        return blank, blank.copy()

    left, top, right, bottom = bbox
    lower_top = min(bottom - 1, top + round((bottom - top) * SIDE_LOWER_BODY_START))
    rgba = rgba.crop((left, lower_top, right, bottom))
    alpha = _binary_alpha(rgba)
    luminance = ImageOps.grayscale(rgba)
    histogram = luminance.histogram(mask=alpha)
    occupied_levels = [index for index, count in enumerate(histogram) if count]
    if occupied_levels:
        low, high = occupied_levels[0], occupied_levels[-1]
        if high > low:
            luminance = luminance.point(
                lambda value: max(0, min(255, round((value - low) * 255 / (high - low))))
            )

    feature_width, feature_height = SIDE_FEATURE_SIZE
    scale = min(feature_width / rgba.width, feature_height / rgba.height)
    resized_size = (
        max(1, round(rgba.width * scale)),
        max(1, round(rgba.height * scale)),
    )
    resized_alpha = alpha.resize(resized_size, Image.Resampling.NEAREST)
    resized_luminance = luminance.resize(resized_size, Image.Resampling.NEAREST)
    output_alpha = Image.new("L", SIDE_FEATURE_SIZE, 0)
    output_luminance = Image.new("L", SIDE_FEATURE_SIZE, 0)
    offset = ((feature_width - resized_size[0]) // 2, feature_height - resized_size[1])
    output_alpha.paste(resized_alpha, offset)
    output_luminance.paste(resized_luminance, offset, resized_alpha)
    return output_alpha, output_luminance


def _feature_distance(
    first: tuple[Image.Image, Image.Image],
    second: tuple[Image.Image, Image.Image],
) -> float:
    first_alpha, first_luminance = first
    second_alpha, second_luminance = second
    alpha_difference = ImageChops.difference(first_alpha, second_alpha)
    alpha_histogram = alpha_difference.histogram()
    pixels = first_alpha.width * first_alpha.height
    alpha_distance = sum(value * count for value, count in enumerate(alpha_histogram)) / max(
        1, 255 * pixels
    )

    union_alpha = ImageChops.lighter(first_alpha, second_alpha)
    visible_pixels = sum(union_alpha.histogram()[1:])
    luminance_difference = ImageChops.difference(first_luminance, second_luminance)
    luminance_histogram = luminance_difference.histogram(mask=union_alpha)
    luminance_distance = sum(
        value * count for value, count in enumerate(luminance_histogram)
    ) / max(1, 255 * visible_pixels)
    return 0.65 * alpha_distance + 0.35 * luminance_distance


@lru_cache(maxsize=16)
def _side_phase_templates(
    cell_width: int, cell_height: int
) -> tuple[tuple[Image.Image, Image.Image], tuple[Image.Image, Image.Image]]:
    cleanup = load_master_with_qa(POSE_TEMPLATE_PATH, "bundled walk-layout-template")
    production = split_production_sheet(cleanup.image)
    right = production.groups.get("right")
    if right is None or len(right.poses) != 4:
        raise CharacterPackError("bundled walk-layout-template has no valid right-facing row")
    cell = make_cell_spec(cell_width, cell_height)
    phase_a = normalize_pose(right.poses[1], cell)
    phase_b = normalize_pose(right.poses[3], cell)
    return _lower_body_feature(phase_a), _lower_body_feature(phase_b)


def classify_side_phase(frame: Image.Image) -> dict[str, object]:
    templates = _side_phase_templates(frame.width, frame.height)
    feature = _lower_body_feature(frame)
    distance_a = _feature_distance(feature, templates[0])
    distance_b = _feature_distance(feature, templates[1])
    classified_as = "A" if distance_a <= distance_b else "B"
    confidence = abs(distance_a - distance_b) / max(distance_a, distance_b, 1e-9)
    return {
        "classified_as": classified_as,
        "confidence_margin": round(confidence, 6),
        "distance_to_a": round(distance_a, 6),
        "distance_to_b": round(distance_b, 6),
    }


def motion_qa(frames: Sequence[Image.Image], direction: str) -> dict[str, object]:
    if len(frames) != 4:
        return {
            "passed": False,
            "leg_alternation_passed": False,
            "reason": "expected four frames",
        }
    neutral_repeat = frame_difference_ratio(frames[0], frames[2])
    first_step = frame_difference_ratio(frames[0], frames[1])
    second_step = frame_difference_ratio(frames[0], frames[3])
    alternating_steps = frame_difference_ratio(frames[1], frames[3])
    basic_motion_passed = (
        neutral_repeat == 0
        and first_step >= 0.01
        and second_step >= 0.01
        and alternating_steps >= 0.01
    )
    result: dict[str, object] = {
        "neutral_repeat_difference": neutral_repeat,
        "first_step_difference": first_step,
        "second_step_difference": second_step,
        "alternating_step_difference": alternating_steps,
        "basic_motion_passed": basic_motion_passed,
    }

    if direction in ("down", "up"):
        offsets = [dominant_foot_offset(frame) for frame in frames]
        phase_a = offsets[1]
        phase_b = offsets[3]
        leg_alternation_passed = bool(
            phase_a is not None
            and phase_b is not None
            and phase_a >= MIN_DOMINANT_FOOT_OFFSET
            and phase_b <= -MIN_DOMINANT_FOOT_OFFSET
        )
        result.update(
            {
                "leg_phase_method": "bottom-18-percent-dominant-foot-offset",
                "dominant_foot_offsets": offsets,
                "minimum_absolute_offset": MIN_DOMINANT_FOOT_OFFSET,
                "expected_action_frame_sides": ["screen-right", "screen-left"],
                "leg_alternation_passed": leg_alternation_passed,
            }
        )
    elif direction == "right":
        classifications = [classify_side_phase(frame) for frame in frames]
        phase_a = classifications[1]
        phase_b = classifications[3]
        leg_alternation_passed = bool(
            phase_a["classified_as"] == "A"
            and phase_b["classified_as"] == "B"
            and phase_a["confidence_margin"] >= MIN_SIDE_PHASE_CONFIDENCE
            and phase_b["confidence_margin"] >= MIN_SIDE_PHASE_CONFIDENCE
        )
        result.update(
            {
                "leg_phase_method": "right-profile-24x24-alpha-luminance-template",
                "side_phase_classifications": classifications,
                "expected_action_frame_phases": ["A", "B"],
                "minimum_confidence_margin": MIN_SIDE_PHASE_CONFIDENCE,
                "leg_alternation_passed": leg_alternation_passed,
            }
        )
    else:
        result.update(
            {
                "leg_alternation_passed": False,
                "reason": f"unsupported generated direction: {direction}",
            }
        )

    result["passed"] = basic_motion_passed and result["leg_alternation_passed"]
    return result


def animation_qa(path: Path, expected_frames: int, expected_size: tuple[int, int]) -> dict[str, object]:
    with Image.open(path) as animation:
        result = {
            "frames": getattr(animation, "n_frames", 1),
            "size": [animation.width, animation.height],
        }
    result["passed"] = result["frames"] == expected_frames and result["size"] == list(expected_size)
    return result


def _segmentation_record(result: SegmentationResult) -> dict[str, object]:
    return {
        "method": result.method,
        "source_size": list(result.source_size),
        "subject_bboxes": [list(box) for box in result.subject_bboxes],
    }


def _cleanup_record(result: MasterCleanupResult) -> dict[str, object]:
    return {
        "method": result.method,
        "confidence": result.confidence,
        "border_background_fraction": result.border_background_fraction,
        "removed_fraction": result.removed_fraction,
        "source_size": [result.image.width, result.image.height],
    }


def _production_record(result: ProductionSheetResult) -> dict[str, object]:
    return {
        "method": result.method,
        "source_size": list(result.source_size),
        "row_bands": [list(band) for band in result.row_bands],
        "valid_directions": sorted(result.groups),
        "errors": result.errors,
    }


def _next_target(output_root: Path, character_id: str) -> Path:
    candidate = output_root / character_id
    if not candidate.exists():
        return candidate
    version = 2
    while True:
        candidate = output_root / f"{character_id}-v{version}"
        if not candidate.exists():
            return candidate
        version += 1


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_character_pack(
    *,
    character_id: str,
    production_sheet_path: str | Path | None = None,
    turnaround_path: str | Path | None = None,
    walk_down_path: str | Path | None = None,
    walk_up_path: str | Path | None = None,
    walk_right_path: str | Path | None = None,
    output_dir: str | Path = "output/character-generation",
    cell_size: str = "48x64",
    frame_duration_ms: int = 170,
    palette_colors: int = 64,
) -> Path:
    character_id = validate_character_id(character_id)
    cell_width, cell_height = parse_cell_size(cell_size)
    if frame_duration_ms < 20 or frame_duration_ms > 5000:
        raise CharacterPackError("frame-duration must be between 20 and 5000 milliseconds")
    if palette_colors < 2 or palette_colors > 256:
        raise CharacterPackError("palette-colors must be between 2 and 256")
    cell = make_cell_spec(cell_width, cell_height)

    cleanup_results: dict[str, MasterCleanupResult] = {}
    production_result: ProductionSheetResult | None = None
    segmented: dict[str, SegmentationResult] = {}
    direction_paths = {
        "down": walk_down_path,
        "up": walk_up_path,
        "right": walk_right_path,
    }

    if production_sheet_path is not None:
        production_cleanup = load_master_with_qa(production_sheet_path, "production-sheet")
        cleanup_results["production_sheet"] = production_cleanup
        production_result = split_production_sheet(production_cleanup.image)
        for direction in GENERATED_DIRECTIONS:
            override_path = direction_paths[direction]
            if override_path is not None:
                override = load_master_with_qa(override_path, f"walk-{direction}")
                cleanup_results[direction] = override
                segmented[direction] = split_subjects(
                    override.image, 4, f"walk-{direction}"
                )
            elif direction in production_result.groups:
                segmented[direction] = production_result.groups[direction]

        missing = [direction for direction in GENERATED_DIRECTIONS if direction not in segmented]
        if missing:
            details = "; ".join(
                production_result.errors.get(direction, "row could not be detected")
                for direction in missing
            )
            raise CharacterPackError(
                f"production sheet needs replacement rows for {', '.join(missing)}: {details}"
            )

        if turnaround_path is not None:
            turnaround = load_master_with_qa(turnaround_path, "turnaround")
            cleanup_results["turnaround"] = turnaround
            segmented["views"] = split_subjects(turnaround.image, 3, "turnaround")
        else:
            view_poses = [segmented[direction].poses[0].copy() for direction in GENERATED_DIRECTIONS]
            view_boxes = [segmented[direction].subject_bboxes[0] for direction in GENERATED_DIRECTIONS]
            segmented["views"] = SegmentationResult(
                poses=view_poses,
                method="production-neutral-frames",
                source_size=production_cleanup.image.size,
                subject_bboxes=view_boxes,
            )
    else:
        required = {
            "turnaround": turnaround_path,
            "down": walk_down_path,
            "up": walk_up_path,
            "right": walk_right_path,
        }
        missing = [name for name, path in required.items() if path is None]
        if missing:
            raise CharacterPackError(
                "provide --production-sheet or all legacy masters: " + ", ".join(missing)
            )
        for name, path in required.items():
            label = "turnaround" if name == "turnaround" else f"walk-{name}"
            cleanup_results[name] = load_master_with_qa(path, label)  # type: ignore[arg-type]
        segmented = {
            "views": split_subjects(cleanup_results["turnaround"].image, 3, "turnaround"),
            "down": split_subjects(cleanup_results["down"].image, 4, "walk-down"),
            "up": split_subjects(cleanup_results["up"].image, 4, "walk-up"),
            "right": split_subjects(cleanup_results["right"].image, 4, "walk-right"),
        }

    for direction in GENERATED_DIRECTIONS:
        segmented[direction].poses[2] = segmented[direction].poses[0].copy()

    source_masters = {
        "turnaround": compose_pose_master(segmented["views"].poses),
        **{
            direction: compose_pose_master(segmented[direction].poses)
            for direction in GENERATED_DIRECTIONS
        },
    }

    normalized = {
        name: [normalize_pose(pose, cell) for pose in result.poses]
        for name, result in segmented.items()
    }
    quantized = apply_shared_palette(normalized, palette_colors)
    quantized["left"] = [ImageOps.mirror(frame) for frame in quantized["right"]]

    motion_checks = {
        direction: motion_qa(quantized[direction], direction)
        for direction in GENERATED_DIRECTIONS
    }
    failed_motion = [
        direction for direction in GENERATED_DIRECTIONS if not motion_checks[direction]["passed"]
    ]
    if failed_motion:
        raise CharacterPackError(
            "MOTION_PHASE_FAILED directions=" + ",".join(failed_motion)
        )

    sheets = {
        "views": make_sheet(quantized["views"]),
        **{direction: make_sheet(quantized[direction]) for direction in DIRECTIONS},
    }

    output_root = Path(output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    target = _next_target(output_root, character_id)
    temp_root = Path(tempfile.mkdtemp(prefix=f".{character_id}-building-", dir=output_root))

    try:
        masters_dir = temp_root / "masters"
        png_dir = temp_root / "sprites" / "png"
        webp_dir = temp_root / "sprites" / "webp"
        animations_dir = temp_root / "animations"
        masters_dir.mkdir(parents=True, exist_ok=True)

        master_paths = {
            "turnaround": masters_dir / f"{character_id}_turnaround.png",
            "down": masters_dir / f"{character_id}_walk_down_master.png",
            "up": masters_dir / f"{character_id}_walk_up_master.png",
            "right": masters_dir / f"{character_id}_walk_right_master.png",
        }
        for name, path in master_paths.items():
            save_png(source_masters[name], path)

        png_paths = {"views": png_dir / f"{character_id}_views.png"}
        webp_paths = {"views": webp_dir / f"{character_id}_views.webp"}
        for direction in DIRECTIONS:
            png_paths[direction] = png_dir / f"{character_id}_walk_{direction}_sheet.png"
            webp_paths[direction] = webp_dir / f"{character_id}_walk_{direction}_sheet.webp"

        for name, image in sheets.items():
            save_png(image, png_paths[name])
            save_webp(image, webp_paths[name])

        apng_paths: dict[str, Path] = {}
        for direction in DIRECTIONS:
            apng_path = animations_dir / f"{character_id}_walk_{direction}.apng"
            save_apng(quantized[direction], apng_path, frame_duration_ms)
            apng_paths[direction] = apng_path

        overview_path = animations_dir / f"{character_id}_walk_overview.gif"
        overview_frames = make_overview_frames(quantized)
        save_gif(overview_frames, overview_path, frame_duration_ms)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "character_id": character_id,
            "style_profile": STYLE_PROFILE,
            "cell": {"width": cell.width, "height": cell.height},
            "frame_count": 4,
            "frame_order": FRAME_ORDER,
            "frame_duration_ms": frame_duration_ms,
            "foot_anchor": {"x": cell.anchor_x, "y": cell.baseline_y},
            "turnaround": {
                "view_order": ["front", "back", "right"],
                "master_png": relative_path(master_paths["turnaround"], temp_root),
                "sheet_png": relative_path(png_paths["views"], temp_root),
                "sheet_webp": relative_path(webp_paths["views"], temp_root),
            },
            "directions": {},
            "masters": {
                direction: relative_path(master_paths[direction], temp_root)
                for direction in ("down", "up", "right")
            },
            "overview_gif": relative_path(overview_path, temp_root),
        }
        for direction in DIRECTIONS:
            record: dict[str, object] = {
                "sheet_png": relative_path(png_paths[direction], temp_root),
                "sheet_webp": relative_path(webp_paths[direction], temp_root),
                "animation_apng": relative_path(apng_paths[direction], temp_root),
            }
            if direction == "left":
                record.update({"derived_from": "right", "transform": "mirror-x-per-frame"})
            manifest["directions"][direction] = record

        artifact_qa = {
            "views": sheet_qa(sheets["views"], 3, cell, palette_colors),
            **{
                direction: sheet_qa(sheets[direction], 4, cell, palette_colors)
                for direction in DIRECTIONS
            },
        }
        animation_checks = {
            direction: animation_qa(apng_paths[direction], 4, (cell.width, cell.height))
            for direction in DIRECTIONS
        }
        animation_checks["overview"] = animation_qa(
            overview_path,
            4,
            (cell.width * 2 * 4, cell.height * 2 * 4),
        )
        qa_report = {
            "schema_version": SCHEMA_VERSION,
            "character_id": character_id,
            "passed": all(record["passed"] for record in artifact_qa.values())
            and all(record["passed"] for record in animation_checks.values())
            and all(record["passed"] for record in motion_checks.values()),
            "master_preprocessing": {
                name: _cleanup_record(result) for name, result in cleanup_results.items()
            },
            "production_grid": (
                _production_record(production_result) if production_result is not None else None
            ),
            "input_segmentation": {
                name: _segmentation_record(result) for name, result in segmented.items()
            },
            "artifacts": artifact_qa,
            "animations": animation_checks,
            "motion": motion_checks,
        }

        _write_json(temp_root / "character.json", manifest)
        _write_json(temp_root / "qa-report.json", qa_report)
        if not qa_report["passed"]:
            raise CharacterPackError("generated pack failed deterministic QA; inspect the staging inputs")

        temp_root.rename(target)
        return target
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a transparent four-direction pixel character asset pack."
    )
    parser.add_argument("--character-id", required=True)
    parser.add_argument("--production-sheet")
    parser.add_argument("--turnaround")
    parser.add_argument("--walk-down")
    parser.add_argument("--walk-up")
    parser.add_argument("--walk-right")
    parser.add_argument("--output-dir", default="output/character-generation")
    parser.add_argument("--cell-size", default="48x64")
    parser.add_argument("--frame-duration", type=int, default=170, dest="frame_duration_ms")
    parser.add_argument("--palette-colors", type=int, default=64)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output_path = build_character_pack(
            character_id=args.character_id,
            production_sheet_path=args.production_sheet,
            turnaround_path=args.turnaround,
            walk_down_path=args.walk_down,
            walk_up_path=args.walk_up,
            walk_right_path=args.walk_right,
            output_dir=args.output_dir,
            cell_size=args.cell_size,
            frame_duration_ms=args.frame_duration_ms,
            palette_colors=args.palette_colors,
        )
    except (CharacterPackError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"output_dir": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

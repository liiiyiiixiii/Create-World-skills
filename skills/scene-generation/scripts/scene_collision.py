#!/usr/bin/env python3
"""Validate foot-point collision geometry and render an aligned red overlay."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import deque
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageChops, ImageDraw


RED = (255, 24, 24, 255)
SUPPORTED_OBSTACLES = {"rect", "circle", "polygon"}
GUIDE_EXTERIOR = (8, 9, 10, 255)
GUIDE_WALKABLE = (218, 205, 176, 255)
GUIDE_OBSTACLE = (51, 55, 57, 255)
GUIDE_EDGE = (126, 112, 88, 255)
GENERATION_MODES = {"fast", "balanced", "quality"}
INPUT_TYPES = {"reference-image", "description", "name", "mixed"}
METADATA_FIELDS = {
    "scene_id",
    "generation_mode",
    "input_type",
    "image_generation_calls",
    "art_direction_id",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("collision spec root must be a JSON object")
    return value


def point(value: Any) -> tuple[float, float]:
    if isinstance(value, dict):
        return float(value["x"]), float(value["y"])
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return float(value[0]), float(value[1])
    raise ValueError(f"invalid point: {value!r}")


def polygon_points(value: Any) -> list[tuple[float, float]]:
    raw = value.get("points") if isinstance(value, dict) else value
    if not isinstance(raw, list):
        raise ValueError("polygon points must be a list")
    return [point(item) for item in raw]


def orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a: tuple[float, float], b: tuple[float, float], p: tuple[float, float]) -> bool:
    return (
        min(a[0], b[0]) - 1e-9 <= p[0] <= max(a[0], b[0]) + 1e-9
        and min(a[1], b[1]) - 1e-9 <= p[1] <= max(a[1], b[1]) + 1e-9
        and abs(orientation(a, b, p)) <= 1e-9
    )


def segments_intersect(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    o1, o2 = orientation(a, b, c), orientation(a, b, d)
    o3, o4 = orientation(c, d, a), orientation(c, d, b)
    if ((o1 > 0 > o2) or (o1 < 0 < o2)) and ((o3 > 0 > o4) or (o3 < 0 < o4)):
        return True
    return (
        (abs(o1) <= 1e-9 and on_segment(a, b, c))
        or (abs(o2) <= 1e-9 and on_segment(a, b, d))
        or (abs(o3) <= 1e-9 and on_segment(c, d, a))
        or (abs(o4) <= 1e-9 and on_segment(c, d, b))
    )


def is_simple_polygon(points: list[tuple[float, float]]) -> bool:
    count = len(points)
    for index in range(count):
        a, b = points[index], points[(index + 1) % count]
        for other in range(index + 1, count):
            if other in {index, (index + 1) % count} or (other + 1) % count == index:
                continue
            c, d = points[other], points[(other + 1) % count]
            if segments_intersect(a, b, c, d):
                return False
    return True


def point_in_polygon(p: tuple[float, float], points: list[tuple[float, float]]) -> bool:
    inside = False
    x, y = p
    previous = points[-1]
    for current in points:
        if on_segment(previous, current, p):
            return True
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            x_at_y = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < x_at_y:
                inside = not inside
        previous = current
    return inside


def obstacle_contains(obstacle: dict[str, Any], p: tuple[float, float]) -> bool:
    shape = obstacle.get("shape")
    x, y = p
    if shape == "rect":
        left, top = float(obstacle["x"]), float(obstacle["y"])
        return left <= x <= left + float(obstacle["width"]) and top <= y <= top + float(obstacle["height"])
    if shape == "circle":
        return math.hypot(x - float(obstacle["cx"]), y - float(obstacle["cy"])) <= float(obstacle["radius"])
    if shape == "polygon":
        return point_in_polygon(p, polygon_points(obstacle))
    return False


def draw_mask(spec: dict[str, Any], width: int, height: int) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for area in spec.get("walkable", []):
        draw.polygon([(round(x), round(y)) for x, y in polygon_points(area)], fill=255)
    for obstacle in spec.get("obstacles", []):
        shape = obstacle.get("shape")
        if shape == "rect":
            x, y = float(obstacle["x"]), float(obstacle["y"])
            w, h = float(obstacle["width"]), float(obstacle["height"])
            draw.rectangle((round(x), round(y), round(x + w), round(y + h)), fill=0)
        elif shape == "circle":
            cx, cy, radius = float(obstacle["cx"]), float(obstacle["cy"]), float(obstacle["radius"])
            draw.ellipse((round(cx - radius), round(cy - radius), round(cx + radius), round(cy + radius)), fill=0)
        elif shape == "polygon":
            draw.polygon([(round(x), round(y)) for x, y in polygon_points(obstacle)], fill=0)
    return mask


def check_connectivity(mask: Image.Image, anchors: list[dict[str, Any]]) -> list[str]:
    if len(anchors) < 2:
        return []
    width, height = mask.size
    step = max(1, math.ceil(max(width, height) / 512))
    grid_width = math.ceil(width / step)
    grid_height = math.ceil(height / step)
    grid = mask.resize((grid_width, grid_height), Image.Resampling.NEAREST)
    pixels = grid.load()

    def cell(anchor: dict[str, Any]) -> tuple[int, int]:
        return (
            min(grid_width - 1, max(0, int(float(anchor["x"]) / step))),
            min(grid_height - 1, max(0, int(float(anchor["y"]) / step))),
        )

    seed_anchor = next((item for item in anchors if item.get("kind") == "spawn"), anchors[0])
    seed = cell(seed_anchor)
    if pixels[seed[0], seed[1]] == 0:
        return []

    visited = bytearray(grid_width * grid_height)
    queue: deque[tuple[int, int]] = deque([seed])
    visited[seed[1] * grid_width + seed[0]] = 1
    while queue:
        x, y = queue.popleft()
        for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if not (0 <= next_x < grid_width and 0 <= next_y < grid_height):
                continue
            index = next_y * grid_width + next_x
            if visited[index] or pixels[next_x, next_y] == 0:
                continue
            visited[index] = 1
            queue.append((next_x, next_y))

    unreachable = []
    for anchor in anchors:
        x, y = cell(anchor)
        if not visited[y * grid_width + x]:
            unreachable.append(str(anchor.get("id", "unnamed")))
    return unreachable


def bounds_for_obstacle(obstacle: dict[str, Any]) -> tuple[float, float, float, float]:
    shape = obstacle.get("shape")
    if shape == "rect":
        x, y = float(obstacle["x"]), float(obstacle["y"])
        return x, y, x + float(obstacle["width"]), y + float(obstacle["height"])
    if shape == "circle":
        cx, cy, radius = float(obstacle["cx"]), float(obstacle["cy"]), float(obstacle["radius"])
        return cx - radius, cy - radius, cx + radius, cy + radius
    points = polygon_points(obstacle)
    xs, ys = [item[0] for item in points], [item[1] for item in points]
    return min(xs), min(ys), max(xs), max(ys)


def validate_metadata(value: Any, errors: list[str], warnings: list[str]) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append("metadata must be an object")
        return {}

    unknown = sorted(set(value) - METADATA_FIELDS)
    if unknown:
        warnings.append("metadata contains unrecognized fields: " + ", ".join(unknown))

    scene_id = value.get("scene_id")
    if scene_id is not None:
        if not isinstance(scene_id, str) or not scene_id.strip():
            errors.append("metadata.scene_id must be a non-empty string")
        elif "/" in scene_id or "\\" in scene_id:
            errors.append("metadata.scene_id must not contain a path")

    mode = value.get("generation_mode")
    if mode is not None and mode not in GENERATION_MODES:
        errors.append("metadata.generation_mode must be fast, balanced, or quality")

    input_type = value.get("input_type")
    if input_type is not None and input_type not in INPUT_TYPES:
        errors.append("metadata.input_type must be reference-image, description, name, or mixed")

    calls = value.get("image_generation_calls")
    if calls is not None:
        if isinstance(calls, bool) or not isinstance(calls, int) or calls < 0 or calls > 2:
            errors.append("metadata.image_generation_calls must be an integer from 0 to 2")
        elif mode == "fast" and calls > 1:
            errors.append("fast mode permits at most one image-generation call")

    for field in ("art_direction_id",):
        item = value.get(field)
        if item is None:
            continue
        if not isinstance(item, str) or not item.strip():
            errors.append(f"metadata.{field} must be a non-empty string or null")
        elif Path(item).is_absolute():
            errors.append(f"metadata.{field} must contain an ID, not an absolute path")

    return dict(value)


def validate(spec: dict[str, Any], scene_size: tuple[int, int] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    metadata = validate_metadata(spec.get("metadata"), errors, warnings)
    coordinate_space = spec.get("coordinate_space")
    if not isinstance(coordinate_space, dict):
        return {"ok": False, "errors": ["coordinate_space must be an object"], "warnings": []}
    try:
        width = int(coordinate_space["width"])
        height = int(coordinate_space["height"])
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "errors": ["coordinate_space width and height must be integers"], "warnings": []}
    if width <= 0 or height <= 0:
        errors.append("coordinate_space width and height must be positive")
    if spec.get("collision_model", "footpoint") != "footpoint":
        warnings.append("the bundled validator models foot-point navigation; collision_model is not footpoint")
    if spec.get("version") != 1:
        warnings.append("expected collision spec version 1")

    walkable = spec.get("walkable")
    if not isinstance(walkable, list) or not walkable:
        errors.append("walkable must contain at least one polygon")
        walkable = []
    valid_walkable: list[list[tuple[float, float]]] = []
    for index, area in enumerate(walkable):
        try:
            points = polygon_points(area)
            if len(points) < 3:
                raise ValueError("needs at least three points")
            if len(set(points)) < 3:
                raise ValueError("needs at least three distinct points")
            if not all(0 <= x < width and 0 <= y < height for x, y in points):
                raise ValueError("contains a point outside coordinate_space")
            if not is_simple_polygon(points):
                raise ValueError("self-intersects")
            valid_walkable.append(points)
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"walkable[{index}] {error}")

    obstacles = spec.get("obstacles", [])
    if not isinstance(obstacles, list):
        errors.append("obstacles must be a list")
        obstacles = []
    valid_obstacles: list[dict[str, Any]] = []
    for index, obstacle in enumerate(obstacles):
        try:
            if not isinstance(obstacle, dict) or obstacle.get("shape") not in SUPPORTED_OBSTACLES:
                raise ValueError(f"shape must be one of {sorted(SUPPORTED_OBSTACLES)}")
            left, top, right, bottom = bounds_for_obstacle(obstacle)
            if right <= left or bottom <= top:
                raise ValueError("has a non-positive size")
            if not (0 <= left and 0 <= top and right < width and bottom < height):
                raise ValueError("extends outside coordinate_space")
            if obstacle.get("shape") == "polygon" and not is_simple_polygon(polygon_points(obstacle)):
                raise ValueError("polygon self-intersects")
            valid_obstacles.append(obstacle)
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"obstacles[{index}] {error}")

    anchors = spec.get("anchors", [])
    if not isinstance(anchors, list):
        errors.append("anchors must be a list")
        anchors = []
    if not anchors:
        warnings.append("no anchors supplied; spawn/exit/interaction reachability was not checked")
    valid_anchors: list[dict[str, Any]] = []
    for index, anchor in enumerate(anchors):
        try:
            x, y = float(anchor["x"]), float(anchor["y"])
            if not (0 <= x < width and 0 <= y < height):
                raise ValueError("is outside coordinate_space")
            if valid_walkable and not any(point_in_polygon((x, y), polygon) for polygon in valid_walkable):
                raise ValueError("is outside walkable space")
            if any(obstacle_contains(obstacle, (x, y)) for obstacle in valid_obstacles):
                raise ValueError("is inside an obstacle")
            valid_anchors.append(anchor)
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"anchors[{index}] {error}")

    if not errors and valid_walkable:
        mask = draw_mask({"walkable": walkable, "obstacles": valid_obstacles}, width, height)
        unreachable = check_connectivity(mask, valid_anchors)
        if unreachable:
            errors.append("anchors are not mutually reachable from the spawn: " + ", ".join(unreachable))

    if scene_size and width > 0 and height > 0:
        scene_width, scene_height = scene_size
        if abs((scene_width / scene_height) - (width / height)) > 0.002:
            errors.append(
                f"scene aspect ratio {scene_width}x{scene_height} does not match coordinate_space {width}x{height}"
            )
        elif (scene_width, scene_height) != (width, height):
            warnings.append(
                f"geometry will be scaled from {width}x{height} to scene size {scene_width}x{scene_height}; exact dimensions are preferred"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "metadata": metadata,
        "generation": {
            "mode": metadata.get("generation_mode"),
            "input_type": metadata.get("input_type"),
            "image_generation_calls": metadata.get("image_generation_calls"),
            "art_direction_used": bool(metadata.get("art_direction_id")),
            "art_direction_id": metadata.get("art_direction_id"),
        },
        "coordinate_space": {"width": width, "height": height},
        "counts": {
            "walkable": len(valid_walkable),
            "obstacles": len(valid_obstacles),
            "anchors": len(valid_anchors),
        },
    }


def draw_layout_guide(spec: dict[str, Any]) -> Image.Image:
    coordinate_space = spec["coordinate_space"]
    width = int(coordinate_space["width"])
    height = int(coordinate_space["height"])
    image = Image.new("RGBA", (width, height), GUIDE_EXTERIOR)
    draw = ImageDraw.Draw(image, "RGBA")
    line_width = max(2, round(min(width, height) * 0.003))

    for area in spec.get("walkable", []):
        points = [(round(x), round(y)) for x, y in polygon_points(area)]
        draw.polygon(points, fill=GUIDE_WALKABLE)
        draw.line(points + [points[0]], fill=GUIDE_EDGE, width=line_width, joint="curve")

    for obstacle in spec.get("obstacles", []):
        shape = obstacle.get("shape")
        if shape == "rect":
            x, y = float(obstacle["x"]), float(obstacle["y"])
            right = x + float(obstacle["width"])
            bottom = y + float(obstacle["height"])
            draw.rectangle(
                (round(x), round(y), round(right), round(bottom)),
                fill=GUIDE_OBSTACLE,
                outline=GUIDE_EDGE,
                width=line_width,
            )
        elif shape == "circle":
            cx, cy = float(obstacle["cx"]), float(obstacle["cy"])
            radius = float(obstacle["radius"])
            draw.ellipse(
                (round(cx - radius), round(cy - radius), round(cx + radius), round(cy + radius)),
                fill=GUIDE_OBSTACLE,
                outline=GUIDE_EDGE,
                width=line_width,
            )
        elif shape == "polygon":
            points = [(round(x), round(y)) for x, y in polygon_points(obstacle)]
            draw.polygon(points, fill=GUIDE_OBSTACLE)
            draw.line(points + [points[0]], fill=GUIDE_EDGE, width=line_width, joint="curve")

    return image


def scaled_points(values: Iterable[tuple[float, float]], scale_x: float, scale_y: float) -> list[tuple[int, int]]:
    return [(round(x * scale_x), round(y * scale_y)) for x, y in values]


def draw_collision_lines(image: Image.Image, spec: dict[str, Any], line_width: int) -> None:
    draw = ImageDraw.Draw(image, "RGBA")
    coordinate_space = spec["coordinate_space"]
    scale_x = image.width / float(coordinate_space["width"])
    scale_y = image.height / float(coordinate_space["height"])
    for area in spec.get("walkable", []):
        points = scaled_points(polygon_points(area), scale_x, scale_y)
        draw.line(points + [points[0]], fill=RED, width=line_width, joint="curve")
    for obstacle in spec.get("obstacles", []):
        shape = obstacle.get("shape")
        if shape == "rect":
            x, y = float(obstacle["x"]) * scale_x, float(obstacle["y"]) * scale_y
            w, h = float(obstacle["width"]) * scale_x, float(obstacle["height"]) * scale_y
            draw.rectangle((round(x), round(y), round(x + w), round(y + h)), outline=RED, width=line_width)
        elif shape == "circle":
            cx, cy = float(obstacle["cx"]) * scale_x, float(obstacle["cy"]) * scale_y
            radius_x, radius_y = float(obstacle["radius"]) * scale_x, float(obstacle["radius"]) * scale_y
            draw.ellipse(
                (round(cx - radius_x), round(cy - radius_y), round(cx + radius_x), round(cy + radius_y)),
                outline=RED,
                width=line_width,
            )
        elif shape == "polygon":
            points = scaled_points(polygon_points(obstacle), scale_x, scale_y)
            draw.line(points + [points[0]], fill=RED, width=line_width, joint="curve")


def analyze_overlay(scene: Image.Image, overlay: Image.Image) -> dict[str, Any]:
    same_dimensions = scene.size == overlay.size
    dimensions = {
        "scene": {"width": scene.width, "height": scene.height},
        "collision_overlay": {"width": overlay.width, "height": overlay.height},
    }
    if not same_dimensions:
        return {
            "checked": True,
            "dimensions": dimensions,
            "same_dimensions": False,
            "only_red_added": False,
            "non_red_pixels_preserved": False,
            "changed_pixels": 0,
            "passed": False,
        }

    difference = ImageChops.difference(scene, overlay).convert("L")
    histogram = difference.histogram()
    changed_pixels = sum(histogram[1:])
    changed_mask = difference.point(lambda value: 255 if value else 0)
    red_reference = Image.new("RGBA", scene.size, RED)
    non_red_difference = ImageChops.difference(overlay, red_reference).convert("L")
    changed_non_red = ImageChops.multiply(non_red_difference, changed_mask)
    only_red_added = changed_pixels > 0 and changed_non_red.getbbox() is None
    return {
        "checked": True,
        "dimensions": dimensions,
        "same_dimensions": True,
        "only_red_added": only_red_added,
        "non_red_pixels_preserved": only_red_added,
        "changed_pixels": changed_pixels,
        "passed": only_red_added,
    }


def write_report(path: Path | None, report: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def run_validate(args: argparse.Namespace) -> int:
    spec = load_json(args.spec)
    scene_size = None
    if args.scene:
        with Image.open(args.scene) as scene:
            scene_size = scene.size
    report = validate(spec, scene_size)
    report.update({"spec": str(args.spec), "scene": str(args.scene) if args.scene else None})
    write_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


def run_guide(args: argparse.Namespace) -> int:
    spec = load_json(args.spec)
    report = validate(spec)
    report.update({"spec": str(args.spec), "guide_output": str(args.output)})
    if not report["ok"]:
        write_report(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    guide = draw_layout_guide(spec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    guide.save(args.output, format="PNG")
    report["guide"] = {
        "width": guide.width,
        "height": guide.height,
        "contains_text_or_markers": False,
        "palette": {
            "exterior": list(GUIDE_EXTERIOR),
            "walkable": list(GUIDE_WALKABLE),
            "obstacle": list(GUIDE_OBSTACLE),
            "edge": list(GUIDE_EDGE),
        },
    }
    write_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def run_render(args: argparse.Namespace) -> int:
    spec = load_json(args.spec)
    with Image.open(args.scene) as source:
        scene = source.convert("RGBA")
    report = validate(spec, scene.size)
    report.update({"spec": str(args.spec), "scene": str(args.scene), "output": str(args.output)})
    if not report["ok"] and not args.allow_invalid:
        write_report(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    line_width = args.line_width or max(3, round(min(scene.size) * 0.004))
    output = Image.new("RGBA", scene.size, (0, 0, 0, 0)) if args.transparent else scene.copy()
    draw_collision_lines(output, spec, line_width)
    if args.transparent:
        report["alignment"] = {
            "checked": False,
            "reason": "transparent overlays are not the final paired-image deliverable",
            "same_dimensions": output.size == scene.size,
        }
    else:
        report["alignment"] = analyze_overlay(scene, output)
        if not report["alignment"]["passed"]:
            report["ok"] = False
            report["errors"].append("collision overlay changed pixels other than the specified red annotation")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.save(args.output, format="PNG")
    write_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate geometry and optional scene alignment")
    validate_parser.add_argument("--spec", type=Path, required=True)
    validate_parser.add_argument("--scene", type=Path)
    validate_parser.add_argument("--report", type=Path)
    validate_parser.set_defaults(func=run_validate)

    guide_parser = subparsers.add_parser("guide", help="render a neutral layout guide from collision geometry")
    guide_parser.add_argument("--spec", type=Path, required=True)
    guide_parser.add_argument("--output", type=Path, required=True)
    guide_parser.add_argument("--report", type=Path)
    guide_parser.set_defaults(func=run_guide)

    render_parser = subparsers.add_parser("render", help="render red collision boundaries over the clean scene")
    render_parser.add_argument("--scene", type=Path, required=True)
    render_parser.add_argument("--spec", type=Path, required=True)
    render_parser.add_argument("--output", type=Path, required=True)
    render_parser.add_argument("--report", type=Path)
    render_parser.add_argument("--line-width", type=int)
    render_parser.add_argument("--transparent", action="store_true")
    render_parser.add_argument("--allow-invalid", action="store_true")
    render_parser.set_defaults(func=run_render)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

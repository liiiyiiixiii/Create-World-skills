#!/usr/bin/env python3
"""Generate anonymous pixel-scene reference boards with no external assets."""

from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw


SCALE = 4
PANEL_W = 192
PANEL_H = 96
INK = (31, 25, 24)
WALL = (112, 105, 91)
WALL_LIGHT = (165, 151, 126)
STONE = (70, 72, 67)
WOOD = (103, 65, 39)
WOOD_LIGHT = (151, 101, 54)
IRON = (47, 49, 47)
DIRT = (129, 103, 55)
FLOOR = (97, 74, 51)
RED = (255, 24, 24)


def block(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = INK,
    width: int = 2,
) -> None:
    draw.rectangle(box, fill=fill, outline=outline, width=width)


def texture(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    seed: int,
    palette: list[tuple[int, int, int]],
    count: int,
) -> None:
    rng = random.Random(seed)
    left, top, right, bottom = box
    for _ in range(count):
        x = rng.randrange(left, right + 1)
        y = rng.randrange(top, bottom + 1)
        draw.point((x, y), fill=palette[rng.randrange(len(palette))])


def room_shell(
    draw: ImageDraw.ImageDraw,
    origin: tuple[int, int],
    floor: tuple[int, int, int] = FLOOR,
    bottom_gap: tuple[int, int] | None = None,
) -> None:
    ox, oy = origin
    block(draw, (ox + 7, oy + 7, ox + PANEL_W - 8, oy + PANEL_H - 8), WALL, width=1)
    block(draw, (ox + 13, oy + 13, ox + PANEL_W - 14, oy + PANEL_H - 14), floor, width=2)
    if bottom_gap:
        start, end = bottom_gap
        draw.rectangle((ox + start, oy + PANEL_H - 16, ox + end, oy + PANEL_H - 5), fill=(8, 9, 10))
        draw.line((ox + start, oy + PANEL_H - 17, ox + start, oy + PANEL_H - 5), fill=INK, width=2)
        draw.line((ox + end, oy + PANEL_H - 17, ox + end, oy + PANEL_H - 5), fill=INK, width=2)
    texture(
        draw,
        (ox + 15, oy + 15, ox + PANEL_W - 16, oy + PANEL_H - 16),
        ox + oy + 11,
        [(86, 64, 45), (116, 87, 56)],
        120,
    )


def draw_cell(draw: ImageDraw.ImageDraw, ox: int, oy: int) -> None:
    room_shell(draw, (ox, oy), floor=(86, 69, 50), bottom_gap=(34, 52))
    block(draw, (ox + 47, oy + 22, ox + 124, oy + 42), STONE)
    block(draw, (ox + 55, oy + 25, ox + 72, oy + 34), WALL_LIGHT, width=1)
    draw.ellipse((ox + 139, oy + 22, ox + 157, oy + 39), fill=STONE, outline=INK, width=2)
    block(draw, (ox + 67, oy + 51, ox + 119, oy + 70), WOOD)
    block(draw, (ox + 80, oy + 70, ox + 104, oy + 80), WOOD_LIGHT, width=1)


def draw_library(draw: ImageDraw.ImageDraw, ox: int, oy: int) -> None:
    room_shell(draw, (ox, oy), floor=(91, 69, 48), bottom_gap=(82, 110))
    for top in (27, 67):
        block(draw, (ox + 42, oy + top, ox + 151, oy + top + 11), WOOD)
        for x in range(47, 149, 9):
            draw.line((ox + x, oy + top + 3, ox + x, oy + top + 8), fill=(179, 137, 69))
    block(draw, (ox + 76, oy + 46, ox + 120, oy + 61), WOOD_LIGHT)
    draw.ellipse((ox + 129, oy + 48, ox + 143, oy + 61), fill=WOOD, outline=INK, width=2)


def draw_yard(draw: ImageDraw.ImageDraw, ox: int, oy: int) -> None:
    block(draw, (ox + 5, oy + 5, ox + PANEL_W - 6, oy + PANEL_H - 6), WALL, width=2)
    block(draw, (ox + 11, oy + 11, ox + PANEL_W - 12, oy + PANEL_H - 12), DIRT, width=1)
    texture(draw, (ox + 12, oy + 12, ox + PANEL_W - 13, oy + PANEL_H - 13), 24, [(113, 90, 50), (148, 118, 59)], 180)
    draw.rectangle((ox + 75, oy + 4, ox + 115, oy + 14), fill=IRON, outline=INK)
    block(draw, (ox + 12, oy + 15, ox + 52, oy + 47), STONE)
    block(draw, (ox + 12, oy + 60, ox + 45, oy + 84), STONE)
    block(draw, (ox + 151, oy + 35, ox + 180, oy + 75), STONE)
    draw.ellipse((ox + 89, oy + 30, ox + 154, oy + 74), fill=(83, 71, 52), outline=(100, 83, 55))
    for x, y in ((66, 35), (55, 64), (128, 78)):
        block(draw, (ox + x, oy + y, ox + x + 20, oy + y + 6), WOOD_LIGHT, width=1)
    draw.ellipse((ox + 72, oy + 50, ox + 81, oy + 59), fill=STONE, outline=INK)


def draw_office(draw: ImageDraw.ImageDraw, ox: int, oy: int) -> None:
    room_shell(draw, (ox, oy), floor=(114, 78, 51), bottom_gap=(82, 110))
    block(draw, (ox + 65, oy + 35, ox + 133, oy + 57), WOOD_LIGHT)
    block(draw, (ox + 74, oy + 55, ox + 87, oy + 66), WOOD, width=1)
    block(draw, (ox + 111, oy + 55, ox + 124, oy + 66), WOOD, width=1)
    block(draw, (ox + 91, oy + 21, ox + 108, oy + 33), (105, 45, 45), width=1)
    block(draw, (ox + 155, oy + 51, ox + 174, oy + 78), WOOD)
    for x, y in ((31, 65), (158, 27)):
        draw.ellipse((ox + x, oy + y, ox + x + 13, oy + y + 13), fill=(52, 90, 56), outline=INK)


def save_scaled(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.resize((image.width * SCALE, image.height * SCALE), Image.Resampling.NEAREST).save(path)


def create_style_board(path: Path) -> None:
    image = Image.new("RGB", (PANEL_W * 2, PANEL_H * 2), (8, 9, 10))
    draw = ImageDraw.Draw(image)
    draw_cell(draw, 0, 0)
    draw_library(draw, PANEL_W, 0)
    draw_yard(draw, 0, PANEL_H)
    draw_office(draw, PANEL_W, PANEL_H)
    draw.line((PANEL_W, 0, PANEL_W, PANEL_H * 2), fill=(221, 202, 151), width=2)
    draw.line((0, PANEL_H, PANEL_W * 2, PANEL_H), fill=(221, 202, 151), width=2)
    save_scaled(image, path)


def create_collision_board(path: Path) -> None:
    image = Image.new("RGB", (PANEL_W * 2, PANEL_H), (8, 9, 10))
    draw = ImageDraw.Draw(image)
    draw_office(draw, 0, 0)
    draw_office(draw, PANEL_W, 0)
    ox = PANEL_W
    outer = [
        (ox + 13, 13),
        (ox + 178, 13),
        (ox + 178, 82),
        (ox + 110, 82),
        (ox + 110, 91),
        (ox + 82, 91),
        (ox + 82, 82),
        (ox + 13, 82),
    ]
    draw.line(outer + [outer[0]], fill=RED, width=2)
    draw.rectangle((ox + 65, 35, ox + 133, 57), outline=RED, width=2)
    draw.ellipse((ox + 31, 65, ox + 44, 78), outline=RED, width=2)
    draw.ellipse((ox + 158, 27, ox + 171, 40), outline=RED, width=2)
    draw.rectangle((ox + 155, 51, ox + 174, 78), outline=RED, width=2)
    draw.line((PANEL_W, 0, PANEL_W, PANEL_H), fill=(221, 202, 151), width=2)
    save_scaled(image, path)


def generate_assets(output_dir: Path) -> tuple[Path, Path]:
    """Generate both anonymous reference boards in *output_dir*."""

    style_board = output_dir / "playable-scene-style-board.png"
    collision_board = output_dir / "collision-notation-board.png"
    create_style_board(style_board)
    create_collision_board(collision_board)
    return style_board, collision_board


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "assets",
        help="directory for the generated PNG reference boards",
    )
    args = parser.parse_args()
    outputs = generate_assets(args.output_dir)
    print("generated reference assets:")
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()

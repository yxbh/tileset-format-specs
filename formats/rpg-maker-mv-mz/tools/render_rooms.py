from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from render_previews import (
    CANVAS_COLOR,
    GRID_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    checkerboard,
    kind_layout,
    load_font,
    nonempty_kinds,
)


FLOOR_STATE_TO_TL_Q = {
    "solid": (2, 4),
    "inner": (2, 2),
    "vertical_edge": (0, 4),
    "horizontal_edge": (2, 0),
    "outer_corner": (0, 2),
    "isolated_corner": (0, 0),
}

WALL_STATE_TO_TL_Q = {
    "solid": (2, 2),
    "vertical_edge": (0, 2),
    "horizontal_edge": (2, 0),
    "outer_corner": (0, 0),
}

FLOOR_FILL = ImageColor.getrgb("#CBD5E1")


@dataclass(frozen=True)
class ParsedRoom:
    name: str
    width: int
    height: int
    rows: tuple[str, ...]
    wall_cells: frozenset[tuple[int, int]]
    floor_cells: frozenset[tuple[int, int]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render footprint-first sample rooms from an RPG Maker MV/MZ A4 sheet."
    )
    parser.add_argument("--image", type=Path, required=True, help="Path to an A4 sheet PNG.")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--room",
        type=Path,
        action="append",
        default=None,
        help="ASCII room file. Repeat this flag to render multiple rooms. Defaults to bundled samples.",
    )
    parser.add_argument("--top-kind", type=int, default=None, help="A4 wall-top local kind.")
    parser.add_argument("--side-kind", type=int, default=None, help="A4 wall-side local kind.")
    parser.add_argument("--wall-height", type=int, default=3, help="Visible wall-face height in tiles.")
    parser.add_argument(
        "--gallery-name",
        default="sample_rooms_gallery.png",
        help="Gallery filename when rendering multiple rooms.",
    )
    return parser.parse_args()


def bundled_sample_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "samples" / "ascii"


def default_room_paths() -> list[Path]:
    sample_dir = bundled_sample_dir()
    named = sorted(sample_dir.glob("room_*.txt"))
    if named:
        return named
    return sorted(sample_dir.glob("*.txt"))


def read_room(path: Path) -> ParsedRoom:
    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
    lines = [line for line in lines if line.strip()]
    if not lines:
        raise ValueError(f"{path} does not contain any room rows.")

    width = max(len(line) for line in lines)
    rows = tuple(line.ljust(width) for line in lines)
    wall_cells = {
        (x, y)
        for y, row in enumerate(rows)
        for x, char in enumerate(row)
        if char.upper() == "W"
    }
    floor_cells = {
        (x, y)
        for y, row in enumerate(rows)
        for x, char in enumerate(row)
        if char.upper() == "F"
    }
    return ParsedRoom(
        name=path.stem,
        width=width,
        height=len(rows),
        rows=rows,
        wall_cells=frozenset(wall_cells),
        floor_cells=frozenset(floor_cells),
    )


def mirror_tr(coord: tuple[int, int]) -> tuple[int, int]:
    x, y = coord
    return (1 if x == 0 else 3, y)


def mirror_bl(coord: tuple[int, int]) -> tuple[int, int]:
    x, y = coord
    return (x, y + 1)


def mirror_br(coord: tuple[int, int]) -> tuple[int, int]:
    x, y = coord
    return (1 if x == 0 else 3, y + 1)


def choose_kind(present_kinds: list[int], requested: int | None, candidates: list[int], label: str) -> int:
    if requested is not None:
        if requested not in present_kinds:
            raise ValueError(f"Requested {label} kind {requested} is not present in the supplied A4 sheet.")
        if requested not in candidates:
            raise ValueError(f"Requested {label} kind {requested} is not valid for {label}.")
        return requested
    chosen = next((kind for kind in candidates if kind in present_kinds), None)
    if chosen is None:
        raise ValueError(f"No non-empty {label} kind was found in the supplied A4 sheet.")
    return chosen


def crop_quarter(image: Image.Image, origin_qx: int, origin_qy: int, quarter_size: int) -> Image.Image:
    return image.crop(
        (
            origin_qx * quarter_size,
            origin_qy * quarter_size,
            (origin_qx + 1) * quarter_size,
            (origin_qy + 1) * quarter_size,
        )
    )


def compose_floor_tile(
    image: Image.Image,
    top_kind: int,
    quarter_size: int,
    states: tuple[str, str, str, str],
) -> Image.Image:
    layout = kind_layout("A4", top_kind)
    quarters = [
        FLOOR_STATE_TO_TL_Q[states[0]],
        mirror_tr(FLOOR_STATE_TO_TL_Q[states[1]]),
        mirror_bl(FLOOR_STATE_TO_TL_Q[states[2]]),
        mirror_br(FLOOR_STATE_TO_TL_Q[states[3]]),
    ]
    tile = Image.new("RGBA", (quarter_size * 2, quarter_size * 2), (0, 0, 0, 0))
    for index, (rel_qx, rel_qy) in enumerate(quarters):
        subtile = crop_quarter(image, layout.origin_qx + rel_qx, layout.origin_qy + rel_qy, quarter_size)
        tile.paste(subtile, ((index % 2) * quarter_size, (index // 2) * quarter_size))
    return tile


def compose_wall_tile(
    image: Image.Image,
    side_kind: int,
    quarter_size: int,
    states: tuple[str, str, str, str],
) -> Image.Image:
    layout = kind_layout("A4", side_kind)
    quarters = [
        WALL_STATE_TO_TL_Q[states[0]],
        mirror_tr(WALL_STATE_TO_TL_Q[states[1]]),
        mirror_bl(WALL_STATE_TO_TL_Q[states[2]]),
        mirror_br(WALL_STATE_TO_TL_Q[states[3]]),
    ]
    tile = Image.new("RGBA", (quarter_size * 2, quarter_size * 2), (0, 0, 0, 0))
    for index, (rel_qx, rel_qy) in enumerate(quarters):
        subtile = crop_quarter(image, layout.origin_qx + rel_qx, layout.origin_qy + rel_qy, quarter_size)
        tile.paste(subtile, ((index % 2) * quarter_size, (index // 2) * quarter_size))
    return tile


def solve_floor_signature(
    n: bool,
    e: bool,
    s: bool,
    w: bool,
    nw_raw: bool,
    ne_raw: bool,
    se_raw: bool,
    sw_raw: bool,
) -> tuple[str, str, str, str]:
    nw = nw_raw and n and w
    ne = ne_raw and n and e
    sw = sw_raw and s and w
    se = se_raw and s and e

    def solve(v: bool, h: bool, d: bool, opposite_v: bool, opposite_h: bool) -> str:
        if v and h and d:
            return "solid"
        if v and h and not d:
            return "inner"
        if v and not h:
            return "vertical_edge"
        if not v and h:
            return "horizontal_edge"
        return "outer_corner" if (opposite_v or opposite_h) else "isolated_corner"

    return (
        solve(n, w, nw, s, e),
        solve(n, e, ne, s, w),
        solve(s, w, sw, n, e),
        solve(s, e, se, n, w),
    )


def solve_wall_signature(n: bool, e: bool, s: bool, w: bool) -> tuple[str, str, str, str]:
    def solve(v: bool, h: bool) -> str:
        if v and h:
            return "solid"
        if v and not h:
            return "vertical_edge"
        if not v and h:
            return "horizontal_edge"
        return "outer_corner"

    return (
        solve(n, w),
        solve(n, e),
        solve(s, w),
        solve(s, e),
    )


def render_room(
    image: Image.Image,
    room: ParsedRoom,
    top_kind: int,
    side_kind: int,
    wall_height: int,
) -> Image.Image:
    tile_size = image.width // 16
    quarter_size = tile_size // 2
    canvas = checkerboard((room.width * tile_size, (room.height + wall_height) * tile_size), block=tile_size // 2)
    draw = ImageDraw.Draw(canvas)

    for x, y in room.floor_cells:
        draw.rectangle(
            (x * tile_size, y * tile_size, (x + 1) * tile_size - 1, (y + 1) * tile_size - 1),
            fill=FLOOR_FILL + (255,),
        )

    for x, y in sorted(room.wall_cells, key=lambda cell: (cell[1], cell[0])):
        n = (x, y - 1) in room.wall_cells
        e = (x + 1, y) in room.wall_cells
        s = (x, y + 1) in room.wall_cells
        w = (x - 1, y) in room.wall_cells
        nw = (x - 1, y - 1) in room.wall_cells
        ne = (x + 1, y - 1) in room.wall_cells
        se = (x + 1, y + 1) in room.wall_cells
        sw = (x - 1, y + 1) in room.wall_cells
        top_tile = compose_floor_tile(image, top_kind, quarter_size, solve_floor_signature(n, e, s, w, nw, ne, se, sw))
        canvas.alpha_composite(top_tile, (x * tile_size, y * tile_size))

    face_cells: list[tuple[int, int, int, int]] = []
    for x, y in room.wall_cells:
        if (x, y + 1) in room.wall_cells:
            continue
        for depth in range(wall_height):
            face_cells.append((x, y, depth, y + 1 + depth))

    face_set = {(x, strip_y, depth) for x, strip_y, depth, _ in face_cells}
    for x, strip_y, depth, screen_y in sorted(face_cells, key=lambda cell: (cell[3], cell[1], cell[2], cell[0])):
        n = (x, strip_y, depth - 1) in face_set
        e = (x + 1, strip_y, depth) in face_set
        s = (x, strip_y, depth + 1) in face_set
        w = (x - 1, strip_y, depth) in face_set
        side_tile = compose_wall_tile(image, side_kind, quarter_size, solve_wall_signature(n, e, s, w))
        canvas.alpha_composite(side_tile, (x * tile_size, screen_y * tile_size))

    return canvas


def save_gallery(images: list[tuple[str, Image.Image]], out_path: Path) -> None:
    font = load_font(18)
    small = load_font(12)
    padding = 24
    title_h = 48
    label_h = 24
    columns = 2 if len(images) > 1 else 1
    rows = (len(images) + columns - 1) // columns
    card_w = max(image.width for _, image in images)
    card_h = max(image.height for _, image in images)
    canvas_w = padding + columns * (card_w + padding)
    canvas_h = title_h + padding + rows * (card_h + label_h + padding)
    canvas = Image.new("RGBA", (canvas_w, canvas_h), CANVAS_COLOR + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((padding, 16), "RPG Maker A4 Room Samples", fill=TEXT_COLOR, font=font)
    draw.text(
        (padding, 34),
        "Footprint-first walls: top surfaces from wall footprint, visible faces from south-exposed strips.",
        fill=MUTED_COLOR,
        font=small,
    )

    for index, (name, image) in enumerate(images):
        row = index // columns
        col = index % columns
        x = padding + col * (card_w + padding)
        y = title_h + padding + row * (card_h + label_h + padding)
        canvas.alpha_composite(image, (x, y))
        draw.rectangle((x, y, x + image.width - 1, y + image.height - 1), outline=GRID_COLOR, width=1)
        draw.text((x, y + image.height + 6), name, fill=TEXT_COLOR, font=small)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    args = parse_args()
    image = Image.open(args.image).convert("RGBA")
    if image.width % 16 != 0:
        raise ValueError(f"{args.image} width {image.width} is not divisible by 16.")
    tile_size = image.width // 16
    if tile_size % 2 != 0:
        raise ValueError(f"{args.image} inferred tile size {tile_size} is not even.")
    if image.height < 15 * tile_size:
        raise ValueError(f"{args.image} height {image.height} is smaller than the canonical A4 height of {15 * tile_size}.")
    if args.wall_height < 1:
        raise ValueError("--wall-height must be at least 1.")

    quarter_size = tile_size // 2
    present_kinds = nonempty_kinds(image, "A4", quarter_size)
    top_kind = choose_kind(present_kinds, args.top_kind, [*range(0, 8), *range(16, 24), *range(32, 40)], "wall-top")
    side_kind = choose_kind(present_kinds, args.side_kind, [*range(8, 16), *range(24, 32), *range(40, 48)], "wall-side")

    room_paths = args.room or default_room_paths()
    if not room_paths:
        raise ValueError("No room files were supplied and no bundled samples were found.")

    rendered: list[tuple[str, Image.Image]] = []
    for room_path in room_paths:
        room = read_room(room_path)
        image_out = render_room(image, room, top_kind, side_kind, args.wall_height)
        out_path = args.out_dir / f"{room.name}.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image_out.save(out_path)
        rendered.append((room.name, image_out))
        print(f"Wrote: {out_path}")

    if len(rendered) > 1:
        gallery_path = args.out_dir / args.gallery_name
        save_gallery(rendered, gallery_path)
        print(f"Wrote: {gallery_path}")

    print(f"Using wall-top kind: {top_kind}")
    print(f"Using wall-side kind: {side_kind}")
    print(f"Wall height: {args.wall_height}")


if __name__ == "__main__":
    main()

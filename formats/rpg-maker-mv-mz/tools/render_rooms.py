from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw

from render_previews import (
    CANVAS_COLOR,
    FLOOR_AUTOTILE_TABLE,
    GRID_COLOR,
    MUTED_COLOR,
    TEXT_COLOR,
    WALL_AUTOTILE_TABLE,
    checkerboard,
    compose_tile,
    kind_layout,
    load_font,
    nonempty_kinds,
)


FLOOR_FILL = ImageColor.getrgb("#CBD5E1")
FLOOR_FALLBACK_SHAPE = 47
WALL_FALLBACK_SHAPE = 15


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


def solve_floor_quarter(v: bool, h: bool, d: bool) -> int:
    if v and h and d:
        return 4
    if v and h:
        return 3
    if v:
        return 1
    if h:
        return 2
    return 0


def solve_wall_quarter(v: bool, h: bool) -> int:
    # A4 wall faces use the official wall table, but the visual notion of a
    # "continuous horizontal run" is inverted relative to the source block's
    # quarter-state layout.
    h = not h
    if v and h:
        return 3
    if v:
        return 1
    if h:
        return 2
    return 0


def floor_state_to_qtile_tl(state: int) -> tuple[int, int]:
    return ((0, 2), (0, 4), (2, 2), (2, 0), (2, 4))[state]


def floor_state_to_qtile_tr(state: int) -> tuple[int, int]:
    return ((3, 2), (3, 4), (1, 2), (3, 0), (1, 4))[state]


def floor_state_to_qtile_bl(state: int) -> tuple[int, int]:
    return ((0, 5), (0, 3), (2, 5), (2, 1), (2, 3))[state]


def floor_state_to_qtile_br(state: int) -> tuple[int, int]:
    return ((3, 5), (3, 3), (1, 5), (3, 1), (1, 3))[state]


def wall_state_to_qtile_tl(state: int) -> tuple[int, int]:
    return ((2, 2), (2, 0), (0, 2), (0, 0))[state]


def wall_state_to_qtile_tr(state: int) -> tuple[int, int]:
    return ((1, 2), (1, 0), (3, 2), (3, 0))[state]


def wall_state_to_qtile_bl(state: int) -> tuple[int, int]:
    return ((2, 1), (2, 3), (0, 1), (0, 3))[state]


def wall_state_to_qtile_br(state: int) -> tuple[int, int]:
    return ((1, 1), (1, 3), (3, 1), (3, 3))[state]


def flatten_entry(entry: list[list[int]]) -> tuple[int, ...]:
    return tuple(value for quarter in entry for value in quarter)


def build_floor_code_to_shape() -> dict[int, int]:
    entry_to_shape = {flatten_entry(entry): shape for shape, entry in enumerate(FLOOR_AUTOTILE_TABLE)}
    out: dict[int, int] = {}
    for code in range(256):
        w = bool(code & 1)
        nw_raw = bool(code & 2)
        n = bool(code & 4)
        ne_raw = bool(code & 8)
        e = bool(code & 16)
        se_raw = bool(code & 32)
        s = bool(code & 64)
        sw_raw = bool(code & 128)

        nw = nw_raw and n and w
        ne = ne_raw and n and e
        se = se_raw and s and e
        sw = sw_raw and s and w

        tl = floor_state_to_qtile_tl(solve_floor_quarter(n, w, nw))
        tr = floor_state_to_qtile_tr(solve_floor_quarter(n, e, ne))
        bl = floor_state_to_qtile_bl(solve_floor_quarter(s, w, sw))
        br = floor_state_to_qtile_br(solve_floor_quarter(s, e, se))
        out[code] = entry_to_shape.get((*tl, *tr, *bl, *br), FLOOR_FALLBACK_SHAPE)
    return out


def build_wall_code_to_shape() -> dict[int, int]:
    entry_to_shape = {flatten_entry(entry): shape for shape, entry in enumerate(WALL_AUTOTILE_TABLE)}
    out: dict[int, int] = {}
    for code in range(16):
        w = bool(code & 1)
        n = bool(code & 2)
        e = bool(code & 4)
        s = bool(code & 8)

        tl = wall_state_to_qtile_tl(solve_wall_quarter(n, w))
        tr = wall_state_to_qtile_tr(solve_wall_quarter(n, e))
        bl = wall_state_to_qtile_bl(solve_wall_quarter(s, w))
        br = wall_state_to_qtile_br(solve_wall_quarter(s, e))
        out[code] = entry_to_shape.get((*tl, *tr, *bl, *br), WALL_FALLBACK_SHAPE)
    return out


FLOOR_CODE_TO_SHAPE = build_floor_code_to_shape()
WALL_CODE_TO_SHAPE = build_wall_code_to_shape()


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


def floor_neighbor_code(cells: frozenset[tuple[int, int]], x: int, y: int) -> int:
    code = 0
    if (x - 1, y) in cells:
        code |= 1
    if (x - 1, y - 1) in cells:
        code |= 2
    if (x, y - 1) in cells:
        code |= 4
    if (x + 1, y - 1) in cells:
        code |= 8
    if (x + 1, y) in cells:
        code |= 16
    if (x + 1, y + 1) in cells:
        code |= 32
    if (x, y + 1) in cells:
        code |= 64
    if (x - 1, y + 1) in cells:
        code |= 128
    return code


def face_neighbor_code(
    face_set: set[tuple[int, int, int]],
    x: int,
    strip_y: int,
    depth: int,
    max_depth: int,
) -> int:
    code = 0
    if (x - 1, strip_y, depth) in face_set:
        code |= 1
    if depth == 0 or (x, strip_y, depth - 1) in face_set:
        code |= 2
    if (x + 1, strip_y, depth) in face_set:
        code |= 4
    # Only the lowest visible row gets the wall-side "bottom/skirting" variant.
    if depth == max_depth:
        code |= 8
    return code


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
    top_layout = kind_layout("A4", top_kind)
    side_layout = kind_layout("A4", side_kind)
    top_tile_cache: dict[int, Image.Image] = {}
    side_tile_cache: dict[int, Image.Image] = {}
    draw_ops: list[tuple[int, int, int, int, Image.Image]] = []

    for x, y in room.floor_cells:
        draw.rectangle(
            (x * tile_size, y * tile_size, (x + 1) * tile_size - 1, (y + 1) * tile_size - 1),
            fill=FLOOR_FILL + (255,),
        )

    for x, y in sorted(room.wall_cells, key=lambda cell: (cell[1], cell[0])):
        shape = FLOOR_CODE_TO_SHAPE.get(floor_neighbor_code(room.wall_cells, x, y), FLOOR_FALLBACK_SHAPE)
        top_tile = top_tile_cache.get(shape)
        if top_tile is None:
            top_tile = compose_tile(image, top_layout, shape, quarter_size)
            top_tile_cache[shape] = top_tile
        draw_ops.append((y * tile_size, 1, y, x, top_tile))

    face_cells: list[tuple[int, int, int, int]] = []
    for x, y in room.wall_cells:
        if (x, y + 1) in room.wall_cells:
            continue
        for depth in range(wall_height):
            face_cells.append((x, y, depth, y + 1 + depth))

    face_set = {(x, strip_y, depth) for x, strip_y, depth, _ in face_cells}
    for x, strip_y, depth, screen_y in sorted(face_cells, key=lambda cell: (cell[3], cell[1], cell[2], cell[0])):
        shape = WALL_CODE_TO_SHAPE.get(
            face_neighbor_code(face_set, x, strip_y, depth, wall_height - 1),
            WALL_FALLBACK_SHAPE,
        )
        side_tile = side_tile_cache.get(shape)
        if side_tile is None:
            side_tile = compose_tile(image, side_layout, shape, quarter_size)
            side_tile_cache[shape] = side_tile
        draw_ops.append((screen_y * tile_size, 0, strip_y, x, side_tile))

    for screen_px, priority, source_y, x, tile in sorted(draw_ops, key=lambda item: (item[0], item[1], item[2], item[3])):
        canvas.alpha_composite(tile, (x * tile_size, screen_px))

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

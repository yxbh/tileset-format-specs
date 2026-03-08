from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont


FLOOR_AUTOTILE_TABLE = [
    [[2, 4], [1, 4], [2, 3], [1, 3]],
    [[2, 0], [1, 4], [2, 3], [1, 3]],
    [[2, 4], [3, 0], [2, 3], [1, 3]],
    [[2, 0], [3, 0], [2, 3], [1, 3]],
    [[2, 4], [1, 4], [2, 3], [3, 1]],
    [[2, 0], [1, 4], [2, 3], [3, 1]],
    [[2, 4], [3, 0], [2, 3], [3, 1]],
    [[2, 0], [3, 0], [2, 3], [3, 1]],
    [[2, 4], [1, 4], [2, 1], [1, 3]],
    [[2, 0], [1, 4], [2, 1], [1, 3]],
    [[2, 4], [3, 0], [2, 1], [1, 3]],
    [[2, 0], [3, 0], [2, 1], [1, 3]],
    [[2, 4], [1, 4], [2, 1], [3, 1]],
    [[2, 0], [1, 4], [2, 1], [3, 1]],
    [[2, 4], [3, 0], [2, 1], [3, 1]],
    [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 4], [1, 4], [0, 3], [1, 3]],
    [[0, 4], [3, 0], [0, 3], [1, 3]],
    [[0, 4], [1, 4], [0, 3], [3, 1]],
    [[0, 4], [3, 0], [0, 3], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]],
    [[2, 2], [1, 2], [2, 3], [3, 1]],
    [[2, 2], [1, 2], [2, 1], [1, 3]],
    [[2, 2], [1, 2], [2, 1], [3, 1]],
    [[2, 4], [3, 4], [2, 3], [3, 3]],
    [[2, 4], [3, 4], [2, 1], [3, 3]],
    [[2, 0], [3, 4], [2, 3], [3, 3]],
    [[2, 0], [3, 4], [2, 1], [3, 3]],
    [[2, 4], [1, 4], [2, 5], [1, 5]],
    [[2, 0], [1, 4], [2, 5], [1, 5]],
    [[2, 4], [3, 0], [2, 5], [1, 5]],
    [[2, 0], [3, 0], [2, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 3], [3, 3]],
    [[2, 2], [1, 2], [2, 5], [1, 5]],
    [[0, 2], [1, 2], [0, 3], [1, 3]],
    [[0, 2], [1, 2], [0, 3], [3, 1]],
    [[2, 2], [3, 2], [2, 3], [3, 3]],
    [[2, 2], [3, 2], [2, 1], [3, 3]],
    [[2, 4], [3, 4], [2, 5], [3, 5]],
    [[2, 0], [3, 4], [2, 5], [3, 5]],
    [[0, 4], [1, 4], [0, 5], [1, 5]],
    [[0, 4], [3, 0], [0, 5], [1, 5]],
    [[0, 2], [3, 2], [0, 3], [3, 3]],
    [[0, 2], [1, 2], [0, 5], [1, 5]],
    [[0, 4], [3, 4], [0, 5], [3, 5]],
    [[2, 2], [3, 2], [2, 5], [3, 5]],
    [[0, 2], [3, 2], [0, 5], [3, 5]],
    [[0, 0], [1, 0], [0, 1], [1, 1]],
]

WALL_AUTOTILE_TABLE = [
    [[2, 2], [1, 2], [2, 1], [1, 1]],
    [[0, 2], [1, 2], [0, 1], [1, 1]],
    [[2, 0], [1, 0], [2, 1], [1, 1]],
    [[0, 0], [1, 0], [0, 1], [1, 1]],
    [[2, 2], [3, 2], [2, 1], [3, 1]],
    [[0, 2], [3, 2], [0, 1], [3, 1]],
    [[2, 0], [3, 0], [2, 1], [3, 1]],
    [[0, 0], [3, 0], [0, 1], [3, 1]],
    [[2, 2], [1, 2], [2, 3], [1, 3]],
    [[0, 2], [1, 2], [0, 3], [1, 3]],
    [[2, 0], [1, 0], [2, 3], [1, 3]],
    [[0, 0], [1, 0], [0, 3], [1, 3]],
    [[2, 2], [3, 2], [2, 3], [3, 3]],
    [[0, 2], [3, 2], [0, 3], [3, 3]],
    [[2, 0], [3, 0], [2, 3], [3, 3]],
    [[0, 0], [3, 0], [0, 3], [3, 3]],
]

TEXT_COLOR = ImageColor.getrgb("#111827")
MUTED_COLOR = ImageColor.getrgb("#6B7280")
CANVAS_COLOR = ImageColor.getrgb("#F8FAFC")
GRID_COLOR = ImageColor.getrgb("#CBD5E1")
CHECK_A = ImageColor.getrgb("#D7DCE5")
CHECK_B = ImageColor.getrgb("#EEF2F7")
FLOOR_COLOR = ImageColor.getrgb("#10B981")
TOP_COLOR = ImageColor.getrgb("#F59E0B")
SIDE_COLOR = ImageColor.getrgb("#06B6D4")


@dataclass(frozen=True)
class KindLayout:
    local_kind: int
    family: str
    origin_qx: int
    origin_qy: int
    size_qw: int
    size_qh: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render RPG Maker MV/MZ A2 or A4 diagnostic preview images from a supplied sheet."
    )
    parser.add_argument("--sheet-type", choices=["A2", "A4"], required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--prefix",
        default=None,
        help="Output file prefix. Defaults to the lowercase sheet type, e.g. a2 or a4.",
    )
    parser.add_argument(
        "--representative-kind",
        type=int,
        default=None,
        help="Optional local kind to use for the shape sweep panel.",
    )
    return parser.parse_args()


def load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def checkerboard(size: tuple[int, int], block: int = 16) -> Image.Image:
    image = Image.new("RGBA", size, CHECK_A + (255,))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], block):
        for x in range(0, size[0], block):
            if ((x // block) + (y // block)) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill=CHECK_B + (255,))
    return image


def family_color(family: str) -> tuple[int, int, int]:
    return {
        "floor": FLOOR_COLOR,
        "wall_top": TOP_COLOR,
        "wall_side": SIDE_COLOR,
    }[family]


def expected_size(sheet_type: str, tile_size: int) -> tuple[int, int]:
    if sheet_type == "A2":
        return 16 * tile_size, 12 * tile_size
    return 16 * tile_size, 15 * tile_size


def kind_count(sheet_type: str) -> int:
    return 32 if sheet_type == "A2" else 48


def kind_layout(sheet_type: str, local_kind: int) -> KindLayout:
    if sheet_type == "A2":
        row = local_kind // 8
        column = local_kind % 8
        return KindLayout(local_kind, "floor", 4 * column, 6 * row, 4, 6)

    band = local_kind // 16
    in_band = local_kind % 16
    column = local_kind % 8
    is_top = in_band < 8
    return KindLayout(
        local_kind=local_kind,
        family="wall_top" if is_top else "wall_side",
        origin_qx=4 * column,
        origin_qy=10 * band + (0 if is_top else 6),
        size_qw=4,
        size_qh=6 if is_top else 4,
    )


def crop_kind(image: Image.Image, layout: KindLayout, quarter_size: int) -> Image.Image:
    x = layout.origin_qx * quarter_size
    y = layout.origin_qy * quarter_size
    w = layout.size_qw * quarter_size
    h = layout.size_qh * quarter_size
    return image.crop((x, y, x + w, y + h))


def compose_tile(
    image: Image.Image,
    layout: KindLayout,
    shape: int,
    quarter_size: int,
) -> Image.Image:
    table = FLOOR_AUTOTILE_TABLE if layout.family in {"floor", "wall_top"} else WALL_AUTOTILE_TABLE
    entry = table[shape]
    tile = Image.new("RGBA", (quarter_size * 2, quarter_size * 2), (0, 0, 0, 0))
    for index, (qsx, qsy) in enumerate(entry):
        src_x = (layout.origin_qx + qsx) * quarter_size
        src_y = (layout.origin_qy + qsy) * quarter_size
        subtile = image.crop((src_x, src_y, src_x + quarter_size, src_y + quarter_size))
        dst_x = (index % 2) * quarter_size
        dst_y = (index // 2) * quarter_size
        tile.paste(subtile, (dst_x, dst_y))
    return tile


def nonempty_kinds(image: Image.Image, sheet_type: str, quarter_size: int) -> list[int]:
    kinds: list[int] = []
    for local_kind in range(kind_count(sheet_type)):
        layout = kind_layout(sheet_type, local_kind)
        if crop_kind(image, layout, quarter_size).getbbox():
            kinds.append(local_kind)
    return kinds


def draw_pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, font: ImageFont.ImageFont) -> None:
    bbox = draw.textbbox((x, y), text, font=font)
    draw.rounded_rectangle(
        (bbox[0] - 4, bbox[1] - 2, bbox[2] + 4, bbox[3] + 2),
        radius=4,
        fill=(255, 255, 255, 230),
        outline=(255, 255, 255, 255),
    )
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)


def annotate_sheet(
    image: Image.Image,
    sheet_type: str,
    tile_size: int,
    quarter_size: int,
    out_path: Path,
) -> list[int]:
    scale = 2
    expected_width, expected_height = expected_size(sheet_type, tile_size)
    present_kinds = nonempty_kinds(image, sheet_type, quarter_size)
    canvas = Image.new("RGBA", (image.width * scale + 80, image.height * scale + 144), CANVAS_COLOR + (255,))
    panel = checkerboard((image.width * scale, image.height * scale), block=12 * scale)
    panel.alpha_composite(image.resize(panel.size, Image.Resampling.NEAREST))
    canvas.alpha_composite(panel, (40, 76))

    draw = ImageDraw.Draw(canvas)
    font = load_font(16)
    small = load_font(12)
    draw.text((40, 20), f"{sheet_type} Sheet Annotated Against Spec", fill=TEXT_COLOR, font=font)
    draw.text(
        (40, 42),
        f"Image: {image.width}x{image.height} px | Tile size: {tile_size}px | Quarter size: {quarter_size}px",
        fill=MUTED_COLOR,
        font=small,
    )
    draw.text(
        (40, 58),
        f"Spec content size: {expected_width}x{expected_height}px | Non-empty kinds: {', '.join(map(str, present_kinds)) or 'none'}",
        fill=MUTED_COLOR,
        font=small,
    )

    for local_kind in range(kind_count(sheet_type)):
        layout = kind_layout(sheet_type, local_kind)
        x0 = 40 + layout.origin_qx * quarter_size * scale
        y0 = 76 + layout.origin_qy * quarter_size * scale
        x1 = x0 + layout.size_qw * quarter_size * scale
        y1 = y0 + layout.size_qh * quarter_size * scale
        color = family_color(layout.family)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=6, outline=color, width=3)
        draw_pill(draw, x0 + 6, y0 + 4, str(local_kind), small)

    if image.height > expected_height:
        y0 = 76 + expected_height * scale
        draw.rectangle(
            (40, y0, 40 + image.width * scale, 76 + image.height * scale),
            fill=(220, 38, 38, 24),
            outline=(220, 38, 38),
            width=2,
        )
        draw_pill(draw, 48, y0 + 8, "Extra image area below canonical height", small)

    legend_y = 76 + image.height * scale + 20
    families = ["floor"] if sheet_type == "A2" else ["wall_top", "wall_side"]
    legend_x = 40
    for family in families:
        color = family_color(family)
        label = {
            "floor": "Ground autotile block (uses FLOOR table)",
            "wall_top": "Wall-top block (uses FLOOR table)",
            "wall_side": "Wall-side block (uses WALL table)",
        }[family]
        draw.rounded_rectangle(
            (legend_x, legend_y, legend_x + 40, legend_y + 20),
            radius=4,
            fill=color + (96,),
            outline=color,
        )
        draw.text((legend_x + 50, legend_y + 3), label, fill=TEXT_COLOR, font=small)
        legend_x += 310

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return present_kinds


def preview_canvas_size(sheet_type: str) -> tuple[int, int]:
    if sheet_type == "A2":
        return 1660, 1260
    return 1520, 1900


def choose_representative_kind(
    present_kinds: list[int],
    preferred_kind: int | None,
    candidates: list[int] | None = None,
) -> int | None:
    if preferred_kind is not None:
        if preferred_kind not in present_kinds:
            raise ValueError(f"Representative kind {preferred_kind} is not present in the supplied sheet.")
        if candidates is not None and preferred_kind not in candidates:
            raise ValueError(f"Representative kind {preferred_kind} is not valid for this preview section.")
        return preferred_kind
    if candidates is None:
        return present_kinds[0] if present_kinds else None
    return next((kind for kind in candidates if kind in present_kinds), None)


def render_preview(
    image: Image.Image,
    sheet_type: str,
    quarter_size: int,
    present_kinds: list[int],
    preferred_kind: int | None,
    out_path: Path,
) -> None:
    font = load_font(16)
    small = load_font(12)
    canvas = Image.new("RGBA", preview_canvas_size(sheet_type), CANVAS_COLOR + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.text((40, 20), f"{sheet_type} Autotile Extraction and Assembly Preview", fill=TEXT_COLOR, font=font)

    if sheet_type == "A2":
        draw.text(
            (40, 42),
            "A2 contains 32 floor/autotile kinds. All use the FLOOR table; runtime table metadata is out of scope here.",
            fill=MUTED_COLOR,
            font=small,
        )
        crop_w = quarter_size * 4
        crop_h = quarter_size * 6
        x0 = 40
        y0 = 86
        draw.text((x0, y0 - 24), "Raw A2 kind blocks", fill=TEXT_COLOR, font=font)
        for local_kind in range(kind_count(sheet_type)):
            row = local_kind // 8
            col = local_kind % 8
            crop = crop_kind(image, kind_layout(sheet_type, local_kind), quarter_size)
            x = x0 + col * (crop_w + 12)
            y = y0 + row * (crop_h + 24)
            canvas.alpha_composite(checkerboard(crop.size, block=8), (x, y))
            canvas.alpha_composite(crop, (x, y))
            draw.rectangle((x, y, x + crop.width - 1, y + crop.height - 1), outline=GRID_COLOR, width=1)
            draw.text((x, y + crop.height + 4), f"K{local_kind}", fill=TEXT_COLOR, font=small)

        sample_kind = choose_representative_kind(present_kinds, preferred_kind)
        if sample_kind is not None:
            layout = kind_layout(sheet_type, sample_kind)
            sweep_x = 940
            draw.text((sweep_x, 62), f"Shape sweep for kind {sample_kind}", fill=TEXT_COLOR, font=font)
            draw.text(
                (sweep_x, 82),
                "Representative full-tile compositions using the official FLOOR table.",
                fill=MUTED_COLOR,
                font=small,
            )
            tile_preview_size = quarter_size * 4
            for shape in range(len(FLOOR_AUTOTILE_TABLE)):
                row = shape // 6
                col = shape % 6
                tile = compose_tile(image, layout, shape, quarter_size)
                tile = tile.resize((tile_preview_size, tile_preview_size), Image.Resampling.NEAREST)
                x = sweep_x + col * (tile_preview_size + 12)
                y = 116 + row * (tile_preview_size + 26)
                canvas.alpha_composite(checkerboard(tile.size, block=8), (x, y))
                canvas.alpha_composite(tile, (x, y))
                draw.rectangle((x, y, x + tile.width - 1, y + tile.height - 1), outline=GRID_COLOR, width=1)
                draw.text((x, y + tile.height + 4), f"S{shape}", fill=TEXT_COLOR, font=small)
    else:
        draw.text(
            (40, 42),
            "A4 mixes wall-top and wall-side kinds. Wall tops use the FLOOR table; wall sides use the WALL table.",
            fill=MUTED_COLOR,
            font=small,
        )
        x_left = 40
        y = 86
        draw.text((x_left, y - 24), "Wall-top source blocks", fill=TEXT_COLOR, font=font)
        top_kinds = [*range(0, 8), *range(16, 24), *range(32, 40)]
        top_crop_w = quarter_size * 4
        top_crop_h = quarter_size * 6
        for index, local_kind in enumerate(top_kinds):
            row = index // 8
            col = index % 8
            crop = crop_kind(image, kind_layout(sheet_type, local_kind), quarter_size)
            x = x_left + col * (top_crop_w + 12)
            y_card = y + row * (top_crop_h + 26)
            canvas.alpha_composite(checkerboard(crop.size, block=8), (x, y_card))
            canvas.alpha_composite(crop, (x, y_card))
            draw.rectangle((x, y_card, x + crop.width - 1, y_card + crop.height - 1), outline=GRID_COLOR, width=1)
            draw.text((x, y_card + crop.height + 4), f"K{local_kind}", fill=TEXT_COLOR, font=small)

        y += 3 * (top_crop_h + 26) + 24
        draw.text((x_left, y - 24), "Wall-side source blocks", fill=TEXT_COLOR, font=font)
        side_kinds = [*range(8, 16), *range(24, 32), *range(40, 48)]
        side_crop_w = quarter_size * 4
        side_crop_h = quarter_size * 4
        for index, local_kind in enumerate(side_kinds):
            row = index // 8
            col = index % 8
            crop = crop_kind(image, kind_layout(sheet_type, local_kind), quarter_size)
            x = x_left + col * (side_crop_w + 12)
            y_card = y + row * (side_crop_h + 26)
            canvas.alpha_composite(checkerboard(crop.size, block=8), (x, y_card))
            canvas.alpha_composite(crop, (x, y_card))
            draw.rectangle((x, y_card, x + crop.width - 1, y_card + crop.height - 1), outline=GRID_COLOR, width=1)
            draw.text((x, y_card + crop.height + 4), f"K{local_kind}", fill=TEXT_COLOR, font=small)

        nonempty_top = choose_representative_kind(present_kinds, preferred_kind, top_kinds)
        nonempty_side = choose_representative_kind(present_kinds, preferred_kind, side_kinds)
        x_right = 940
        y_right = 86
        if nonempty_top is not None:
            draw.text((x_right, y_right - 24), f"Wall-top shape sweep (kind {nonempty_top})", fill=TEXT_COLOR, font=font)
            tile_preview_size = quarter_size * 4
            layout = kind_layout(sheet_type, nonempty_top)
            for shape in range(len(FLOOR_AUTOTILE_TABLE)):
                row = shape // 4
                col = shape % 4
                tile = compose_tile(image, layout, shape, quarter_size)
                tile = tile.resize((tile_preview_size, tile_preview_size), Image.Resampling.NEAREST)
                x = x_right + col * (tile_preview_size + 12)
                y = y_right + row * (tile_preview_size + 26)
                canvas.alpha_composite(checkerboard(tile.size, block=8), (x, y))
                canvas.alpha_composite(tile, (x, y))
                draw.rectangle((x, y, x + tile.width - 1, y + tile.height - 1), outline=GRID_COLOR, width=1)
                draw.text((x, y + tile.height + 4), f"S{shape}", fill=TEXT_COLOR, font=small)

        if nonempty_side is not None:
            tile_preview_size = quarter_size * 4
            layout = kind_layout(sheet_type, nonempty_side)
            y_right = 86 + 12 * (tile_preview_size + 26) + 24
            draw.text((x_right, y_right - 24), f"Wall-side shape sweep (kind {nonempty_side})", fill=TEXT_COLOR, font=font)
            for shape in range(len(WALL_AUTOTILE_TABLE)):
                row = shape // 4
                col = shape % 4
                tile = compose_tile(image, layout, shape, quarter_size)
                tile = tile.resize((tile_preview_size, tile_preview_size), Image.Resampling.NEAREST)
                x = x_right + col * (tile_preview_size + 12)
                y = y_right + row * (tile_preview_size + 26)
                canvas.alpha_composite(checkerboard(tile.size, block=8), (x, y))
                canvas.alpha_composite(tile, (x, y))
                draw.rectangle((x, y, x + tile.width - 1, y + tile.height - 1), outline=GRID_COLOR, width=1)
                draw.text((x, y + tile.height + 4), f"S{shape}", fill=TEXT_COLOR, font=small)

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

    quarter_size = tile_size // 2
    expected_width, expected_height = expected_size(args.sheet_type, tile_size)
    if image.width != expected_width:
        raise ValueError(
            f"{args.image} width {image.width} does not match expected {expected_width} for {args.sheet_type}."
        )
    if image.height < expected_height:
        raise ValueError(
            f"{args.image} height {image.height} is smaller than canonical {expected_height} for {args.sheet_type}."
        )

    prefix = args.prefix or args.sheet_type.lower()
    present_kinds = annotate_sheet(
        image=image,
        sheet_type=args.sheet_type,
        tile_size=tile_size,
        quarter_size=quarter_size,
        out_path=args.out_dir / f"{prefix}_sheet_annotated.png",
    )
    render_preview(
        image=image,
        sheet_type=args.sheet_type,
        quarter_size=quarter_size,
        present_kinds=present_kinds,
        preferred_kind=args.representative_kind,
        out_path=args.out_dir / f"{prefix}_autotile_preview.png",
    )

    print(f"Wrote: {args.out_dir / f'{prefix}_sheet_annotated.png'}")
    print(f"Wrote: {args.out_dir / f'{prefix}_autotile_preview.png'}")
    print(f"Non-empty kinds: {present_kinds}")
    print(
        f"Tile size: {tile_size}px | Quarter size: {quarter_size}px | Canonical size: {expected_width}x{expected_height}px"
    )


if __name__ == "__main__":
    main()

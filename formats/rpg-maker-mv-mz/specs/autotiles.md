# RPG Maker MV/MZ Autotile Spec

This document is a generic, implementation-oriented specification for decoding and assembling RPG Maker MV/MZ tileset sheet types that matter for static environment rendering:

- `A2`: ground autotiles
- `A4`: wall-top and wall-side autotiles
- `A5`, `B`, `C`, `D`, `E`: regular atlas tiles

This document is intentionally generic:

- no sample-pack observations
- no references to local validation images
- no assumptions about a particular game or room layout

It is written for two audiences at once:

- a human who wants an ELI5 explanation of what the sheet is doing
- an agent or programmer who needs exact formulas and tables to implement it

For canonical neighbor-mask solving, see [shape-solver.md](shape-solver.md).

## 1. Scope

This spec defines:

- the sheet geometry for `A2` and `A4`
- the exact quarter-based assembly model used by those sheet types
- the exact lookup tables needed to compose a final tile once a shape index is known
- the direct-slicing behavior for `A5` and `B` through `E`

This spec does not define:

- `A1` animated water / waterfall behavior
- `A3` wall autotile behavior
- the full neighbor-mask-to-shape-index solver
- tileset database metadata such as table/counter flags

Important separation of concerns:

- this spec tells you how to decode a sheet and assemble a tile
- it does not tell you how your game decides which shape index to request

That means an implementation can be correct and useful even if it only exposes:

- `compose_a2(local_kind, shape)`
- `compose_a4_top(local_kind, shape)`
- `compose_a4_side(local_kind, shape)`

and leaves shape selection to a separate system.

## 2. ELI5

RPG Maker autotiles are not stored as ready-to-use final tiles. They are stored as small reusable pieces.

Think of one final tile as being built from four mini-squares:

```text
+----+----+
| TL | TR |
+----+----+
| BL | BR |
+----+----+
```

Each mini-square is one quarter of the tile.

RPG Maker stores a small source block for each material, then uses a lookup table to say:

- take this quarter for `TL`
- take this quarter for `TR`
- take this quarter for `BL`
- take this quarter for `BR`

So:

- a `kind` means "which material block am I using?"
- a `shape` means "which recipe am I using for the four quarters?"

`A2` uses this for floors.

`A4` uses this for:

- wall tops
- wall sides

`A5` and `B/C/D/E` do not do this at all. They are ordinary tile atlases.

## 3. Terms And Units

Use these normalized units everywhere:

- `T = tile_size`
- `Q = quarter_size = T / 2`

Constraints:

- `T` must be even
- all formulas below are expressed in quarter coordinates unless stated otherwise

Definitions:

- `local_kind`: the material block index within one sheet type
- `family`: one of `floor`, `wall_top`, `wall_side`
- `shape`: the quarter-assembly recipe index
- `origin_qx`, `origin_qy`: top-left of a kind block in quarter coordinates
- `size_qw`, `size_qh`: width and height of a kind block in quarter coordinates

Quarter placement inside a final tile always uses this order:

1. `TL`
2. `TR`
3. `BL`
4. `BR`

Destination positions for those quarters are always:

- `TL -> (0, 0)`
- `TR -> (Q, 0)`
- `BL -> (0, Q)`
- `BR -> (Q, Q)`

## 4. Universal Composition Model

### ELI5

No matter whether you are reading `A2` or `A4`, the assembly step is the same:

1. find the right source block
2. pick the right quarter recipe
3. copy four `Q x Q` pieces
4. paste them into one `T x T` tile

### Normative Rule

A composed tile is always built from exactly four quarter samples.

For a table entry:

```text
[
  [q0x, q0y],
  [q1x, q1y],
  [q2x, q2y],
  [q3x, q3y]
]
```

the samples mean:

- quarter 0 -> `TL`
- quarter 1 -> `TR`
- quarter 2 -> `BL`
- quarter 3 -> `BR`

Each quarter coordinate is relative to the kind origin, not absolute within the sheet.

### Reference Pseudocode

```python
def compose_autotile(image, origin_qx, origin_qy, table, shape, quarter_size):
    entry = table[shape]
    tile_size = quarter_size * 2
    out = new_rgba_image(tile_size, tile_size)

    for index, (src_rel_qx, src_rel_qy) in enumerate(entry):
        src_x = (origin_qx + src_rel_qx) * quarter_size
        src_y = (origin_qy + src_rel_qy) * quarter_size
        subtile = crop(image, src_x, src_y, quarter_size, quarter_size)

        dst_x = (index % 2) * quarter_size
        dst_y = (index // 2) * quarter_size
        paste(out, subtile, dst_x, dst_y)

    return out
```

## 5. Quarter Lookup Tables

These tables are the core of the assembly process.

- `FLOOR_AUTOTILE_TABLE` is used by:
  - `A2` ground autotiles
  - `A4` wall-top autotiles
- `WALL_AUTOTILE_TABLE` is used by:
  - `A4` wall-side autotiles

Each entry is ordered as:

```text
[TL, TR, BL, BR]
```

Each `TL/TR/BL/BR` item is:

```text
[relative_qx, relative_qy]
```

### `FLOOR_AUTOTILE_TABLE`

Valid floor shape indices are `0..47`.

```python
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
```

### `WALL_AUTOTILE_TABLE`

Valid wall shape indices are `0..15`.

```python
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
```

## 6. `A2` Ground Autotiles

### ELI5

An `A2` sheet is a grid of ground materials.

Each material stores enough quarter pieces to rebuild the different edge and corner variants for one floor-like tile.

Every `A2` kind uses the same quarter table:

- `FLOOR_AUTOTILE_TABLE`

### Canonical Geometry

An `A2` sheet uses:

- width: `16 * T`
- height: `12 * T`

It contains `32` local kinds arranged as:

- `8` columns
- `4` rows

Each kind block is:

- width: `2 * T = 4 * Q`
- height: `3 * T = 6 * Q`

### Local Kind Numbering

Valid `A2` local kinds are `0..31`.

For a given `local_kind`:

```text
row    = floor(local_kind / 8)
column = local_kind % 8
```

### Source Block Origin

In quarter coordinates:

```text
origin_qx = 4 * column
origin_qy = 6 * row
size_qw   = 4
size_qh   = 6
family    = floor
```

### Composition Rule

For every `A2` kind:

- use `FLOOR_AUTOTILE_TABLE`
- require `shape in 0..47`

### Validation Rules

An `A2` decoder should validate at least:

- image width is divisible by `16`
- inferred `T = image_width / 16`
- `T` is even
- image height is exactly `12 * T`
- requested `local_kind` is in `0..31`
- requested `shape` is in `0..47`

### Metadata Caveat

`A2`-related runtime behavior such as table/counter semantics is not stored in the PNG layout itself.

That means:

- this spec is sufficient to decode the image and assemble tiles
- this spec is not sufficient to reproduce every database-driven runtime rule in RPG Maker

## 7. `A4` Wall Autotiles

### ELI5

An `A4` sheet is split into vertical bands.

Inside each band:

- the top half stores wall-top materials
- the bottom half stores wall-side materials

Wall tops and wall sides do not use the same quarter table:

- wall tops use the floor-style table
- wall sides use the wall-style table

### Canonical Geometry

An `A4` sheet uses:

- width: `16 * T`
- height: `15 * T`

It contains `48` local kinds arranged as `3` vertical bands.

Each band contains:

- `8` wall-top kinds
- `8` wall-side kinds

Per band:

- wall-top block height: `3 * T = 6 * Q`
- wall-side block height: `2 * T = 4 * Q`
- total band height: `5 * T = 10 * Q`

### Local Kind Numbering

Valid `A4` local kinds are `0..47`.

Numbering order:

- `0..7`   = band 0 wall tops
- `8..15`  = band 0 wall sides
- `16..23` = band 1 wall tops
- `24..31` = band 1 wall sides
- `32..39` = band 2 wall tops
- `40..47` = band 2 wall sides

Equivalent formulas:

```text
band    = floor(local_kind / 16)
in_band = local_kind % 16
column  = local_kind % 8
is_top  = in_band < 8
```

### Source Block Origin

In quarter coordinates:

```text
origin_qx = 4 * column
origin_qy = 10 * band + (0 if is_top else 6)
```

Block size depends on family:

```text
if is_top:
    size_qw = 4
    size_qh = 6
    family  = wall_top
else:
    size_qw = 4
    size_qh = 4
    family  = wall_side
```

### Composition Rule

For `A4` wall tops:

- use `FLOOR_AUTOTILE_TABLE`
- require `shape in 0..47`

For `A4` wall sides:

- use `WALL_AUTOTILE_TABLE`
- require `shape in 0..15`

### Validation Rules

An `A4` decoder should validate at least:

- image width is divisible by `16`
- inferred `T = image_width / 16`
- `T` is even
- image height is at least `15 * T`
- requested `local_kind` is in `0..47`
- requested `shape` is valid for the chosen family

If the image is taller than `15 * T`, rows below the canonical `A4` content area should be ignored by default unless a tool explicitly chooses to preserve non-canonical extra content.

### Common 3/4 View Usage Note

This is not a sheet-decoding rule, but it matters in practice.

In a typical top-down 3/4 view game, a wall is often modeled as wall volume, not just a visible face.

One common interpretation is:

- wall footprint cells produce `wall_top`
- south-exposed wall boundaries produce visible `wall_side`
- west/east walls still have top surfaces because those top surfaces come from the footprint, not from the vertical side strip

This distinction is outside the sheet format itself, but it explains why an `A4` implementation may need two stages:

1. determine wall-top placement from wall footprint
2. determine wall-side placement from exposed south boundaries

## 8. `A5` And `B/C/D/E` Sheets

### ELI5

These are ordinary tile atlases.

You do not rebuild them from quarters.

You just slice them on the tile grid and pick the tile you want.

### Rule

For `A5`, `B`, `C`, `D`, and `E`:

- no autotile lookup tables
- no quarter recomposition
- no neighbor-dependent shape selection

Each tile is a direct `T x T` atlas cell.

The implementation model is simply:

```text
tile_x = column * T
tile_y = row * T
rect   = (tile_x, tile_y, T, T)
```

## 9. Recommended Decoder Structure

An implementation should separate these responsibilities:

### 1. Sheet Decoder

Responsible for:

- validating image dimensions
- computing `T` and `Q`
- mapping `local_kind -> origin_qx/origin_qy/family`
- composing a tile from `local_kind + shape`

### 2. Shape Solver

Responsible for:

- reading neighboring logical cells
- converting those neighbors into a compatible shape index

This is deliberately a separate concern because different engines or games may:

- reuse RPG Maker shape numbers directly
- remap them into their own internal mask format
- avoid shape solving entirely for offline baking

### 3. World Semantics

Responsible for decisions such as:

- which cells are floor vs wall
- whether walls are footprint-first or face-first
- how many vertical tiles a wall face should extrude
- how non-autotile sheets map to gameplay zones

## 10. Recommended API Surface

The following API shape is sufficient for a robust implementation:

```python
class SheetInfo:
    sheet_type: str
    tile_size: int
    quarter_size: int

class KindLayout:
    local_kind: int
    family: str
    origin_qx: int
    origin_qy: int
    size_qw: int
    size_qh: int

def parse_sheet_info(sheet_type, image) -> SheetInfo: ...
def get_kind_layout(sheet_type, local_kind) -> KindLayout: ...
def crop_kind_block(image, layout, quarter_size): ...
def compose_autotile(image, layout, shape, quarter_size): ...
def slice_regular_tile(image, row, column, tile_size): ...
```

## 11. Acceptance Checklist

A decoder implementing this spec should satisfy all of the following:

- `A2` kinds decode as `32` blocks arranged in `8 x 4`
- every `A2` kind uses the floor table and supports `48` shapes
- `A4` kinds decode as `48` blocks arranged in `3` bands of `16`
- `A4` top kinds use the floor table
- `A4` side kinds use the wall table
- a composed tile is always exactly `T x T`
- each composed tile is assembled from four `Q x Q` samples
- `A5` and `B/C/D/E` require only direct atlas slicing
- extra rows below canonical `A4` height are ignored by default

## 12. References

Primary references for the geometry and engine behavior:

- [RPG Maker MZ Help: Asset Standards](https://rpgmakerofficial.com/product/MZ_help-en/01_11_01.html)
- [RPG Maker MZ Tilemap.js Reference](https://developer.rpgmakerweb.com/rpg-maker-mz/Tilemap.js.html)

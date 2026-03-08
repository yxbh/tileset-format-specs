# RPG Maker MV/MZ A4 Room Visualization Spec

This document specifies the repository's footprint-first room visualization model for RPG Maker MV/MZ `A4` wall sheets.

It is intentionally separate from the generic sheet and solver specs:

- [autotiles.md](autotiles.md) defines `A4` sheet geometry and quarter assembly
- [shape-solver.md](shape-solver.md) defines the canonical logical neighbor solver
- this document defines how an abstract wall footprint becomes a rendered 3/4 top-down room preview

Scope:

- synthetic room visualization from ASCII or equivalent logical grids
- `A4` wall-top usage
- `A4` wall-side usage
- draw order for mixed top and face tiles

Out of scope:

- generic RPG Maker sheet decoding
- `A2` floor materials beyond simple room-fill visualization
- editor metadata
- `A1` or `A3`
- non-native side-cap synthesis for west/east wall faces

## 1. ELI5

The key idea is:

- `W` means "this cell is part of the wall mass"
- `F` means "this cell is walkable floor"

So a wall is treated like a solid ring or block, not like already-rendered face pixels.

From that wall mass:

- the top surface is drawn directly on the `W` cells
- the visible wall face is drawn only where the wall mass is exposed to the south

That gives a classic 3/4 top-down look:

```text
wall top footprint
vvvvvvvvvvvvvvvvvv
WWWWWW
WFFFFW
WFFFFW
WWWFWW

visible wall faces appear below south-exposed W cells
```

This model is why west and east perimeter walls still have top surfaces:

- they are part of the wall footprint
- they just do not emit south-facing wall faces unless their south edge is exposed

## 2. Inputs

The minimal logical input is a rectangular grid of cells.

Recommended symbols:

- `W` = wall footprint or wall volume
- `F` = floor

Example:

```text
WWWWWW
WFFFFW
WFFFFW
WFFFFW
WWFWWW
```

Required implementation outputs:

- a wall-footprint set
- a floor set

Suggested normalized representation:

```text
wall_cells  = {(x, y), ...}
floor_cells = {(x, y), ...}
```

## 3. Semantic Model

### 3.1 Wall Tops

Every `W` cell produces one wall-top tile.

Those wall-top tiles:

- use the `A4` wall-top family
- use the floor-style autotile table
- solve adjacency against the full connected wall footprint

So:

- all `W` cells participate in top connectivity
- west and east walls keep their top surfaces

### 3.2 Visible Wall Faces

Visible wall faces are emitted only by south-exposed wall footprint cells.

A wall footprint cell `(x, y)` is south-exposed when:

```text
(x, y + 1) not in wall_cells
```

These cells are the face emitters.

## 4. Face Extrusion

Given:

- south-exposed emitter `(x, y)`
- `wall_height >= 1`

Generate one visible face tile for each depth row:

```text
for depth in 0 .. wall_height - 1:
    face_cell = (x, y, depth)
    screen_y = y + 1 + depth
```

Interpretation:

- `x` stays fixed
- `y` is the source wall-footprint row
- `depth` is the vertical face row below that footprint edge
- `screen_y` is the final rendered tile row

This spec uses the term `strip_y` for the source wall row of a face strip.

So a face cell may be represented as:

```text
(x, strip_y, depth)
```

with render position:

```text
(x, strip_y + 1 + depth)
```

## 5. Wall-Top Shape Solving

Wall-top tiles use the `floor` family from [shape-solver.md](shape-solver.md).

For each wall-top cell `(x, y)`:

1. inspect neighboring `W` cells in all 8 directions
2. build the floor-family neighbor code or equivalent booleans
3. solve the canonical floor signature
4. map that signature to an `A4` wall-top shape
5. compose the tile with `FLOOR_AUTOTILE_TABLE`

Important:

- the connectivity domain is `wall_cells`
- not `face_cells`
- not `floor_cells`

## 6. Wall-Face Shape Solving

Wall faces use the `wall` family from [shape-solver.md](shape-solver.md), but the connectivity domain is the extruded face strip space, not raw grid projection space.

That detail matters because two unrelated face strips can land on the same final screen row while still being logically disconnected.

### 6.1 Face Connectivity Domain

Build:

```text
face_set = {(x, strip_y, depth), ...}
```

Do not solve connectivity from projected `(x, screen_y)` positions alone.

### 6.2 Neighbor Rules

For a face cell `(x, strip_y, depth)`:

- `W` is true when `(x - 1, strip_y, depth)` exists in `face_set`
- `E` is true when `(x + 1, strip_y, depth)` exists in `face_set`
- `N` is true when:
  - `depth == 0`, because the top face row visually connects upward into the wall cap
  - or `(x, strip_y, depth - 1)` exists in `face_set`
- `S` is true only for the bottom-most visible face row:

```text
depth == wall_height - 1
```

This last rule is deliberate:

- only the bottom-most visible face row gets the wall-side lower-edge or skirting treatment
- upper rows remain continuous wall body

### 6.3 Why Strip Space Matters

Two wall strips must not connect merely because they project to the same rendered row.

Incorrect approach:

- connect faces by `(x, screen_y)` only

Correct approach:

- connect faces by `(x, strip_y, depth)`

This prevents disconnected walls from borrowing the wrong side subtiles at apparent joins.

## 7. Shape Mapping

This visualization spec assumes a renderer that can derive official `A4` shape indices from the canonical quarter solver and published quarter tables.

Expected behavior:

- wall tops resolve through the floor-family shape table
- wall faces resolve through the wall-family shape table

Equivalent implementation strategies are acceptable:

- canonical signature -> official shape index -> table composition
- direct canonical signature -> quarter coordinate composition

As long as the final assembled tile matches the same `A4` source block semantics.

## 8. Draw Order

Draw order is not an optional detail. It materially affects stepped wall footprints.

### 8.1 Problem

If all tops are drawn first and all faces afterward, a farther wall face can incorrectly cover a nearer step-top when both land on the same rendered row.

### 8.2 Required Ordering

Wall tops and wall faces must be depth-sorted together.

Recommended draw-op model:

```text
top draw op:
    screen_y = y
    priority = 1

face draw op:
    screen_y = strip_y + 1 + depth
    priority = 0
```

Then sort by:

```text
(screen_y, priority, source_y, x)
```

with lower priority drawing first.

This means:

- faces draw before tops on the same screen row
- nearer tops can overpaint farther faces where needed

That is the behavior required by this repository's sample renderer.

## 9. Native Limitation

This visualization model is intentionally native to south-facing `A4` wall faces.

It does not synthesize dedicated west-facing or east-facing side-cap art for footprint steps.

So if a wall footprint contains lateral recesses or protrusions:

- the top surface is still rendered correctly
- south-facing faces are still rendered correctly
- but the visualization does not invent non-native side-face geometry that is not present in a standard `A4` wall-side family

This is a renderer boundary, not a sheet-decoding bug.

## 10. Reference Pseudocode

```python
def render_a4_room(room, top_kind, side_kind, wall_height):
    wall_cells = room.wall_cells
    floor_cells = room.floor_cells

    draw_ops = []

    for (x, y) in wall_cells:
        top_shape = solve_wall_top_shape_from_wall_footprint(x, y, wall_cells)
        draw_ops.append(
            ("top", y, 1, y, x, compose_a4_top(top_kind, top_shape))
        )

    face_cells = []
    for (x, y) in wall_cells:
        if (x, y + 1) in wall_cells:
            continue
        for depth in range(wall_height):
            face_cells.append((x, y, depth))

    face_set = set(face_cells)
    for (x, strip_y, depth) in face_cells:
        screen_y = strip_y + 1 + depth
        n = (depth == 0) or ((x, strip_y, depth - 1) in face_set)
        w = (x - 1, strip_y, depth) in face_set
        e = (x + 1, strip_y, depth) in face_set
        s = (depth == wall_height - 1)
        face_shape = solve_wall_face_shape(n, e, s, w)
        draw_ops.append(
            ("face", screen_y, 0, strip_y, x, compose_a4_side(side_kind, face_shape))
        )

    draw_ops.sort(key=lambda item: (item[1], item[2], item[3], item[4]))

    draw_floor_background(floor_cells)
    for _, screen_y, _, _, x, tile in draw_ops:
        draw_tile(tile, x, screen_y)
```

## 11. Acceptance Checklist

An implementation of this spec should satisfy all of the following:

- every `W` cell renders one wall-top tile
- only south-exposed `W` cells emit visible wall faces
- wall tops solve adjacency against the full `W` footprint
- wall faces solve adjacency in strip/depth space, not just projected screen space
- disconnected walls do not connect merely because they share a rendered row
- the top face row visually connects into the wall cap
- only the bottom face row gets the wall-side lower-edge treatment
- tops and faces are depth-sorted together

## 12. Relationship To The Room Tool

This is the intended behavioral contract for:

- [render_rooms.py](../tools/render_rooms.py)

If the tool behavior changes materially, this document should be updated in the same change.

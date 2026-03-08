# RPG Maker MV/MZ Canonical Shape-Solver Spec

This document defines a canonical neighbor-based solver for RPG Maker-style autotiles.

It is intentionally separate from the sheet-layout spec:

- [autotiles.md](autotiles.md) explains where quarter pieces live on the sheet
- this document explains how to turn neighboring cells into a canonical quarter signature

Important scope note:

- the official RPG Maker runtime exposes autotile shape extraction from tile IDs and the quarter lookup tables used to draw those shapes
- the official public docs do not publish the editor's full neighbor-to-shape algorithm

So this document is a repository-defined canonical solver derived from the official table model, not a claim about hidden editor internals.

## 1. ELI5

The sheet spec answers:

- "where do the quarter pieces come from?"

The shape-solver answers:

- "which kind of corners and edges does this tile need?"

You can think of it as the step that looks at neighboring cells and decides whether each corner of the tile should be:

- filled
- an edge
- an outer corner
- an inner corner

For a floor-like tile, all four quarters can differ.

For a wall-side tile, the same idea applies, but the rules are simpler.

## 2. Purpose

This spec gives you a stable logical layer between:

1. world connectivity
2. sheet decoding

That lets an implementation:

- solve a canonical neighborhood signature from logical neighbors
- then either:
  - map that signature to RPG Maker shape indices
  - or bypass shape indices and map the quarter states directly to source art

## 3. Families

This solver defines two logical families:

- `floor`
  - used for `A2`
  - used for `A4` wall tops
- `wall`
  - used for `A4` wall sides

## 4. Inputs

The solver works on a target cell plus boolean information about whether the eight neighboring cells should connect to it.

Use this naming:

```text
NW  N  NE
 W  C   E
SW  S  SE
```

Each boolean means:

- `true`: that neighbor belongs to the same logical connected region for this family
- `false`: it does not

The matching rule is up to the caller.

Examples:

- for a floor solver, "same logical region" may mean "same floor material"
- for a wall-top solver, it may mean "same wall footprint region"
- for a wall-side solver, it may mean "same visible wall-face strip"

## 5. Normalization

### ELI5

Diagonal neighbors only matter when the two cardinals that lead to them already connect.

So:

- `NW` only matters if `N` and `W` are both connected
- `NE` only matters if `N` and `E` are both connected
- `SW` only matters if `S` and `W` are both connected
- `SE` only matters if `S` and `E` are both connected

### Normative Rule

Before any floor-family corner solving, normalize diagonals like this:

```text
nw = raw_nw and n and w
ne = raw_ne and n and e
sw = raw_sw and s and w
se = raw_se and s and e
```

If a diagonal is not reachable through its adjacent cardinals, it must be treated as `false`.

This is the standard blob-autotile normalization rule.

## 6. Canonical Quarter States

This repository uses canonical logical quarter states, not source-sheet coordinates, as the output of the solver.

### 6.1 Floor Family Quarter States

Valid floor-quarter states are:

- `solid`
- `inner_corner`
- `vertical_edge`
- `horizontal_edge`
- `outer_corner`

Interpretation:

- `solid`: both side neighbors and the diagonal are connected
- `inner_corner`: both side neighbors are connected, but the diagonal is missing
- `vertical_edge`: the quarter continues vertically but not horizontally
- `horizontal_edge`: the quarter continues horizontally but not vertically
- `outer_corner`: neither side neighbor is connected

These states are local to one quarter.

### 6.2 Wall Family Quarter States

Valid wall-quarter states are:

- `solid`
- `vertical_edge`
- `horizontal_edge`
- `outer_corner`

Wall-family solving does not use diagonals.

## 7. Floor Family Solver

### ELI5

For each corner, you only ask:

1. does this tile connect on the two sides touching that corner?
2. if both sides connect, does the diagonal also connect?

Example for the top-left quarter:

- look at `N`
- look at `W`
- look at `NW`

### Quarter Rules

For each floor-family quarter, define:

- `v`: the vertical-side neighbor relevant to that quarter
- `h`: the horizontal-side neighbor relevant to that quarter
- `d`: the diagonal relevant to that quarter after normalization

Then solve:

```text
if v and h and d:
    state = solid
elif v and h and not d:
    state = inner_corner
elif v and not h:
    state = vertical_edge
elif not v and h:
    state = horizontal_edge
else:
    state = outer_corner
```

### Corner Inputs

Use these inputs for each quarter:

- `TL` uses `v = N`, `h = W`, `d = NW`
- `TR` uses `v = N`, `h = E`, `d = NE`
- `BL` uses `v = S`, `h = W`, `d = SW`
- `BR` uses `v = S`, `h = E`, `d = SE`

### Output

The canonical floor signature is:

```text
(TL, TR, BL, BR)
```

where each item is one of:

- `solid`
- `inner_corner`
- `vertical_edge`
- `horizontal_edge`
- `outer_corner`

### Reference Pseudocode

```python
def solve_floor_signature(n, e, s, w, nw_raw, ne_raw, se_raw, sw_raw):
    nw = nw_raw and n and w
    ne = ne_raw and n and e
    sw = sw_raw and s and w
    se = se_raw and s and e

    def solve(v, h, d):
        if v and h and d:
            return "solid"
        if v and h and not d:
            return "inner_corner"
        if v and not h:
            return "vertical_edge"
        if not v and h:
            return "horizontal_edge"
        return "outer_corner"

    tl = solve(n, w, nw)
    tr = solve(n, e, ne)
    bl = solve(s, w, sw)
    br = solve(s, e, se)
    return (tl, tr, bl, br)
```

## 8. Wall Family Solver

### ELI5

Wall-side solving is simpler.

Each quarter only cares about the two side neighbors that meet at that corner.

No diagonal gating step is used.

### Quarter Rules

For each wall-family quarter, define:

- `v`: the vertical-side neighbor relevant to that quarter
- `h`: the horizontal-side neighbor relevant to that quarter

Then solve:

```text
if v and h:
    state = solid
elif v and not h:
    state = vertical_edge
elif not v and h:
    state = horizontal_edge
else:
    state = outer_corner
```

### Corner Inputs

Use these inputs for each quarter:

- `TL` uses `v = N`, `h = W`
- `TR` uses `v = N`, `h = E`
- `BL` uses `v = S`, `h = W`
- `BR` uses `v = S`, `h = E`

### Output

The canonical wall signature is:

```text
(TL, TR, BL, BR)
```

where each item is one of:

- `solid`
- `vertical_edge`
- `horizontal_edge`
- `outer_corner`

### Reference Pseudocode

```python
def solve_wall_signature(n, e, s, w):
    def solve(v, h):
        if v and h:
            return "solid"
        if v and not h:
            return "vertical_edge"
        if not v and h:
            return "horizontal_edge"
        return "outer_corner"

    tl = solve(n, w)
    tr = solve(n, e)
    bl = solve(s, w)
    br = solve(s, e)
    return (tl, tr, bl, br)
```

## 9. Practical Usage

The expected implementation split is:

1. determine connectivity booleans from world data
2. solve a canonical signature with this document
3. hand that signature to a renderer-specific mapping layer

The renderer-specific layer may do one of two things:

- map canonical signatures to source quarter pieces directly
- map canonical signatures to stable shape IDs used by a specific runtime

## 10. Relationship To The Sheet Spec

Use the families like this:

- `A2` -> floor solver
- `A4` wall top -> floor solver
- `A4` wall side -> wall solver

This is why the sheet spec and the shape-solver spec are separate:

- sheet spec = storage format
- shape-solver spec = logical neighborhood reduction

## 11. Important Boundary

This document does not assign official RPG Maker shape numbers to the canonical signatures.

Reason:

- the official public runtime references expose shape extraction from tile IDs and the quarter draw tables
- they do not publish the editor's full neighbor-to-shape-number algorithm

So the stable contract here is:

- input: normalized neighbor connectivity
- output: canonical quarter signature

If a future repository document needs a fixed `signature -> RPG Maker shape index` map, that should be written as a separate compatibility layer and labeled as a derived mapping.

## 12. Acceptance Checklist

A solver implementing this spec should satisfy all of the following:

- floor-family diagonals are gated by their adjacent cardinals
- floor-family quarter states come only from the five canonical states in this doc
- wall-family quarter states come only from the four canonical states in this doc
- the solver returns one quarter state for each of `TL`, `TR`, `BL`, `BR`
- `A2` and `A4` wall-top consumers use the floor solver
- `A4` wall-side consumers use the wall solver

## 13. References

Primary references that justify the separation between shape extraction and drawing:

- [RPG Maker MZ Tilemap.js Reference](https://developer.rpgmakerweb.com/rpg-maker-mz/Tilemap.js.html)
- [RPG Maker MZ Help: Asset Standards](https://rpgmakerofficial.com/product/MZ_help-en/01_11_01.html)

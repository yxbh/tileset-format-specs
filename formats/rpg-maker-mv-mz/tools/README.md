# Tools

Utilities in this folder are optional helpers for exploring or validating documented formats.

They should be:

- generic
- safe to run on user-supplied assets
- usable without committing third-party art into the repository

## `render_previews.py`

Renders diagnostic preview images for RPG Maker MV/MZ `A2` and `A4` sheets.

Outputs:

- `<prefix>_sheet_annotated.png`
- `<prefix>_autotile_preview.png`

Dependency:

- `Pillow`

Example:

```bash
python formats/rpg-maker-mv-mz/tools/render_previews.py \
  --sheet-type A4 \
  --image /path/to/A4.png \
  --out-dir /path/to/output
```

Optional representative kind override:

```bash
python formats/rpg-maker-mv-mz/tools/render_previews.py \
  --sheet-type A2 \
  --image /path/to/A2.png \
  --out-dir /path/to/output \
  --representative-kind 2 \
  --prefix my_a2
```

Notes:

- The script validates canonical `A2` and `A4` geometry.
- It allows extra height below canonical `A4` content and marks that area in the annotated output.
- It does not implement `A1` or `A3`.
- It does not commit or depend on any sample art.

## `render_rooms.py`

Renders footprint-first sample rooms from an RPG Maker MV/MZ `A4` sheet and ASCII room definitions.

Outputs:

- one PNG per room file
- a gallery PNG when rendering multiple rooms

Example using bundled samples:

```bash
python formats/rpg-maker-mv-mz/tools/render_rooms.py \
  --image /path/to/A4.png \
  --out-dir /path/to/output
```

Example using an explicit room file:

```bash
python formats/rpg-maker-mv-mz/tools/render_rooms.py \
  --image /path/to/A4.png \
  --out-dir /path/to/output \
  --room formats/rpg-maker-mv-mz/samples/ascii/room_01_rect_ring.txt \
  --wall-height 3
```

Notes:

- This renderer uses the repo's canonical footprint-first wall interpretation.
- Wall-top tiles are solved from wall footprint connectivity.
- Visible wall-side strips are generated from south-exposed wall boundaries.
- Side-strip connectivity is solved in strip/depth space so unrelated strips do not merge just because they land on the same screen row.
- The renderer derives official floor and wall shape indices from the published quarter tables, then composes tiles with the same A4 tables used by the preview tool.
- Topmost wall-face cells connect upward into the wall cap so the face does not render with an exposed top edge.
- Only the bottom-most visible face row gets the wall-side lower-edge or skirting variant; upper rows stay as continuous wall body.
- Tops and faces are depth-sorted together so closer step-tops can draw over farther wall faces on the same screen row.

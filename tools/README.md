# Tools

Utilities in this folder are optional helpers for exploring or validating documented formats.

They should be:

- generic
- safe to run on user-supplied assets
- usable without committing third-party art into the repository

## `render_rpgmaker_previews.py`

Renders diagnostic preview images for RPG Maker MV/MZ `A2` and `A4` sheets.

Outputs:

- `<prefix>_sheet_annotated.png`
- `<prefix>_autotile_preview.png`

Dependency:

- `Pillow`

Example:

```bash
python tools/render_rpgmaker_previews.py \
  --sheet-type A4 \
  --image /path/to/A4.png \
  --out-dir /path/to/output
```

Optional representative kind override:

```bash
python tools/render_rpgmaker_previews.py \
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

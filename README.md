# Tileset Format Specs

Reference repository for documenting autotile and tileset formats in a way that is:

- implementation-friendly
- format-oriented rather than engine-project-specific
- safe to share without bundling third-party art by default

## Purpose

This repo exists to store:

- format specs
- lookup tables
- sheet geometry rules
- synthetic or redistributable samples
- optional helper utilities
- debugging notes that help another agent or programmer implement a decoder

## Repository Layout

```text
formats/
  <format-family>/
    README.md
    specs/
    samples/
    tools/
```

Current families:

- `rpg-maker-mv-mz`

## Content Rules

- Specs should be generic and reusable.
- Samples should be synthetic, hand-authored, public-domain, or otherwise clearly redistributable.
- Do not commit proprietary or ambiguously licensed tileset art by default.
- If a spec depends on external runtime metadata that is not present in the PNG, call that out explicitly.

## Current Coverage

- RPG Maker MV/MZ:
  - `A2` autotiles
  - `A4` autotiles
  - canonical floor/wall shape-solver spec
  - `A5`, `B`, `C`, `D`, `E` direct atlas slicing
  - [preview utility](formats/rpg-maker-mv-mz/tools/README.md)

Not covered yet:

- RPG Maker `A1`
- RPG Maker `A3`
- other engines / editors

## Suggested Next Additions

- `A1` animated water and waterfall notes
- `A3` wall autotile notes
- side-by-side sample sheets built from synthetic art

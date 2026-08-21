# Character Pack Contract

## Resumable staging

Initialize a job before image generation:

```powershell
python scripts/character_job.py init `
  --photo <photo.png> `
  --output-dir <output-root> `
  --generation-mode balanced `
  --cell-size 48x64 `
  --frame-duration 170
```

Copy every built-in image result immediately, leaving the original in place:

```powershell
python scripts/character_job.py record `
  --job-dir <job-dir> `
  --artifact production-sheet `
  --source <generated.png>
```

The state stores the photo filename and SHA-256, never the photo or its absolute path. An incomplete job with the same photo hash, style profile, mode, cell, and duration is resumed. Mark it complete only after the pack passes QA.

## Default builder command

```powershell
python scripts/build_character_pack.py `
  --character-id <id> `
  --production-sheet <production-sheet.png> `
  --output-dir <output-root> `
  --cell-size 48x64 `
  --frame-duration 170
```

The production sheet contains three rows ordered `down`, `up`, `right` and four columns ordered `neutral`, `gait-A`, `neutral`, `gait-B`. The schema retains `left-step`/`right-step` as compatibility labels only. The builder derives views from the first column and makes column three an exact copy of column one.

When only a direction row failed, pass its replacement without discarding valid production rows:

```powershell
python scripts/build_character_pack.py `
  --character-id <id> `
  --production-sheet <production-sheet.png> `
  --walk-up <replacement-up.png> `
  --output-dir <output-root>
```

`--walk-down`, `--walk-up`, `--walk-right`, and `--turnaround` are optional overrides with `--production-sheet`.

## Legacy builder command

The v1 interface remains supported for quality mode and existing callers:

```powershell
python scripts/build_character_pack.py `
  --character-id <id> `
  --turnaround <turnaround.png> `
  --walk-down <down.png> `
  --walk-up <up.png> `
  --walk-right <right.png> `
  --output-dir <output-root>
```

`character-id` uses lowercase ASCII letters or digits separated by `-`, `_`, or `.`. Existing pack directories receive `-v2`, `-v3`, and later siblings.

## Accepted generated backgrounds

- Genuine RGBA transparency is thresholded to binary alpha; low-alpha halos are removed.
- Opaque RGB or RGBA masters may use a flat white or light neutral checkerboard canvas. The builder removes only light-neutral pixels connected to the canvas edge, preserving enclosed white clothing and eye details.
- Complex, dark, colored, low-confidence, or subject-touching backgrounds are rejected rather than destructively guessed.
- A production sheet must resolve to three rows and each retained row to four separated figures. Direction overrides may replace invalid rows.

## Output layout and normalization

The output layout remains compatible with schema version 1:

```text
<character-id>/
|-- masters/                cleaned high-resolution turnaround and direction masters
|-- sprites/png/            views plus down/up/right/left PNG sheets
|-- sprites/webp/           lossless WebP equivalents
|-- animations/             four APNG files plus overview GIF
|-- character.json
`-- qa-report.json
```

- Default cell: `48x64`; views sheet: `144x64`; direction sheet: `192x64`; foot anchor: `(24, 61)`.
- Poses are fitted without stretching, centered, and aligned to one foot baseline.
- Final alpha is `0` or `255`; one shared non-dithered palette contains at most 64 opaque colors.
- Left is a per-frame horizontal mirror of right without reversing frame order.
- PNG/WebP are lossless; APNG has four native frames; the overview GIF is a nearest-neighbor `2x2` direction grid.

## Metadata and QA

`character.json` remains `schema_version: 1` and uses `style_profile: create-world-bright-chibi-v1`. All artifact paths are relative. This profile change intentionally prevents unfinished jobs created for an older visual profile from being resumed.

`qa-report.json` adds backward-compatible records for master preprocessing, background confidence, production-grid rows, segmentation boxes, motion differences, dominant-foot offsets, side-phase classifications, confidence margins, and `leg_alternation_passed`. Front/back gait frames must place the dominant shoe on opposite screen sides; the right-facing gait must classify as bundled side template A then B with at least 5% confidence margin. A pack passes only when dimensions, binary alpha, palette, clipping, baseline, animations, exact neutral repetition, and deterministic leg alternation all pass. Neither JSON file stores the source photo or an absolute path.

The builder runs motion-phase QA before creating a final output directory. A failure is reported as `MOTION_PHASE_FAILED directions=down,up` (directions vary), allowing `balanced` callers to supplement only those rows and `fast` callers to stop immediately.

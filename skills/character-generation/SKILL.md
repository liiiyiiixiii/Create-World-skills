---
name: character-generation
description: Convert one front-facing person photo into a Create World bright-chibi 2D pixel character pack with three views, transparent four-direction walk sheets, and animations. Use when a user wants to game-ify a photographed person or create reusable pixel-character walking assets; do not use for 3D rigs, vector characters, or non-character images.
---

# Character Generation

Create a standalone asset pack. Do not register the character in a game, edit game code, or copy the source photo into the result unless the user separately asks.

## Inputs and defaults

- Require one image containing one recognizable, front-facing person. Accept a headshot or full-body photo.
- Preserve identity, approximate age, hairstyle, skin tone, glasses, and visible clothing. Conservatively complete unseen body and clothing details.
- Accept optional `character_id`, `output_dir`, `cell_size`, `frame_duration`, and `generation_mode`.
- Default to `48x64`, four frames, `170ms`, `./output/character-generation/`, and `generation_mode=balanced`.
- Modes: `balanced` uses one production sheet and repairs only failed directions; `fast` never supplements a failed sheet; `quality` uses separate masters and generates the three walk directions concurrently.

## Workflow

1. Inspect the photo. Stop for multiple people, an unusable face, or severe obstruction.
2. Read [references/generation-workflow.md](references/generation-workflow.md). Inspect both [assets/beyond-walls-style-board.png](assets/beyond-walls-style-board.png) and [assets/walk-layout-template.png](assets/walk-layout-template.png) with `view_image` before prompting. These references are anonymous, programmatically generated assets; reproduce them with `scripts/generate_reference_assets.py` when auditing or updating the Skill.
3. Initialize or resume staging with `scripts/character_job.py init`. It derives a readable ID, fingerprints the photo without copying it, and reports any reusable artifacts.
4. Use built-in `image_gen`. In `balanced` or `fast` mode, generate one plain-white `3x4` production sheet: rows `down, up, right`; columns `neutral, gait-A, neutral, gait-B`. Treat the manifest's legacy `left-step`/`right-step` names as compatibility labels, not anatomical instructions. The photo is the identity reference, the bright board is the primary style reference, and the layout template controls only poses and arrangement.
5. Immediately copy each built-in result into staging with `scripts/character_job.py record`. Never leave a deliverable only under the default generated-images location.
6. Read [references/pack-contract.md](references/pack-contract.md), then run `scripts/build_character_pack.py --production-sheet ...`. The builder removes supported white/checkerboard backgrounds, strips low-alpha halos, derives the turnaround from neutral frames, duplicates the neutral frame deterministically, mirrors left, and packs all outputs.
7. Do not spend image-generation retries on background or alpha defects. If the builder reports `MOTION_PHASE_FAILED directions=...` or another row-scoped failure in `balanced` mode, preserve accepted rows, generate only the named four-frame rows concurrently, and pass them back as direction overrides. If the full grid is unusable, allow one targeted full-sheet retry. Stop after that supplement or retry round and preserve valid staging artifacts. In `fast` mode, stop on the first failure.
8. In `quality` mode, use the separate-master prompts in the workflow reference, request a plain white canvas, run the three direction calls concurrently, and use the legacy builder arguments. Retry only the master named by content, layout, or motion-phase QA; never retry accepted masters.
9. Inspect the final views sheet, all direction sheets, and overview GIF at nearest-neighbor scale. Confirm bright chibi style, identity and clothing consistency, correct directions, readable motion, and clean transparency. Mark staging complete with `scripts/character_job.py complete` only after QA passes.
10. Report the pack path, generation mode and call count, final prompt set, inferred appearance details, resumed/reused work, and remaining QA warnings.

## Image input handling

- With local paths, pass the photo, style board, and layout template through `referenced_image_paths`, labeling their roles in the prompt.
- Without a local photo path, show both bundled assets with `view_image`, then use the smallest `num_last_images_to_include` containing the photo and both references. Never mix the two image-input mechanisms.
- If built-in image generation is unavailable, explain that the CLI/API fallback requires `OPENAI_API_KEY`; continue only if the user explicitly chooses it.

## Boundaries

- Never overwrite a pack; create `-v2`, `-v3`, and later siblings.
- Never store the source photo or absolute paths in the final pack.
- Never add the source photo to this Skill, its bundled references, tests, or an open-source repository. Only pass it to the active image-generation request and hash it for resumable local staging.
- Do not add network calls, runtime dependencies beyond Pillow, external assets, or engine integration.
- Left-facing art mirrors asymmetric clothing details; disclose that when relevant.

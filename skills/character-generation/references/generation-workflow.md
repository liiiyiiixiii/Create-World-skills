# Create World Bright Chibi Character Generation Profile

Use this profile for prompting and visual acceptance. The final pack is engine-agnostic and defaults to a compact `48x64` gameplay cell.

## Reference roles

- Input photo: identity, age, hair, skin tone, glasses, and clothing evidence only.
- `assets/beyond-walls-style-board.png`: primary visual reference. It contains six anonymous, programmatically generated figures. Follow its large eyes, bright controlled palette, blocky highlights, compact anatomy, and friendly readable faces; do not treat any figure as an identity reference.
- `assets/walk-layout-template.png`: anonymous grayscale pose, direction, spacing, and gameplay-scale reference only. It contains no source-person identity, hair, face, or uniform to copy.
- `scripts/generate_reference_assets.py`: deterministic source for both bundled PNGs. It reads no photos, game projects, or external assets.

## Visual language

- Approximately `2.5–3` heads tall with a large square-rounded head, large simple eyes, compact torso, and short limbs.
- At final size, the figure normally occupies about `17–28` pixels in width and `54–58` pixels in height inside a `48x64` cell.
- Use a one- or two-native-pixel dark outline, hard pixel clusters, a small number of deliberate highlight/shadow blocks, and a bright but controlled palette.
- Preserve recognizable photographic cues while simplifying them. Glasses, fringe, hair silhouette, and dominant clothing colors matter more than small facial anatomy.
- Avoid realistic adult proportions, skin texture, wrinkles, tiny facial rendering, smooth airbrushed gradients, painterly detail, anime line art, 3D dolls, CRT effects, and high-resolution pixel-painted portraits.
- Use a flat pure-white intermediate canvas. The builder creates final transparency. No checkerboard, gradient backdrop, floor, shadow, glow, text, labels, dividers, watermark, props, or extra people.

## Default production-sheet prompt

Use this scaffold and add only appearance details visible in the photo:

```text
Use case: stylized-concept
Asset type: one production-ready 3x4 pixel-character walk-cycle master
Primary request: transform the person in Image 1 into one consistent bright chibi 2D pixel game character while preserving recognizable identity
Input images: Image 1 is the identity and clothing reference; Image 2 is the primary bright-chibi visual style reference; Image 3 controls only the 3x4 pose layout, directions, spacing, and gait
Scene/backdrop: one completely flat pure-white canvas
Subject: exactly the same character in all twelve cells; preserve face cues, hair silhouette, age, skin tone, glasses, outfit, and palette; conservatively complete unseen clothing
Style/medium: low-resolution game-sprite art shown enlarged with hard nearest-neighbor pixels; 2.5-3 heads tall; large simple eyes; compact body; short limbs; one- or two-pixel dark outline; blocky highlights and shadows; bright controlled colors
Composition/framing: exactly three horizontal rows and four columns with generous white gutters; no drawn grid; equal character scale; full bodies visible; aligned feet
Row order: top row front-facing and walking down toward the viewer; middle row back-facing and walking up away from the viewer with no face visible; bottom row strict right-facing profiles walking to screen right
Column order: column 1 neutral standing; column 2 gait phase A; column 3 neutral standing; column 4 gait phase B
Front/back leg phase: in column 2 the lowest and most forward shoe must be on the RIGHT side of the image; in column 4 it must be on the LEFT side of the image; these screen positions are mandatory even for the back view
Right-profile leg phase: in column 2 the visually foreground leg steps toward screen RIGHT; in column 4 that foreground leg retracts while the far leg steps toward screen RIGHT; make the foreground leg slightly lighter/thicker and the far leg darker/partly occluded, so the lighter foreground shoe is rightmost in column 2 and leftmost in column 4; columns 2 and 4 must show opposite leg depth and must not reuse one pose
Arm phase: swing the arms opposite to the legs in both gait phases; leg alternation is the mandatory acceptance criterion
Constraints: exactly twelve figures; no overlap or clipping; consistent identity and clothing; pure white background; no text, labels, lines, borders, shadow, floor, glow, props, watermark, or extra figures
Avoid: realistic anatomy; detailed portrait rendering; smooth gradients; semi-realistic skin; checkerboard transparency; black or gray background
```

The builder replaces column three with an exact copy of column one, so minor neutral-frame drift does not require a retry.

## Balanced validation and repair

- Accept supported white/checkerboard/alpha cleanup without an image-generation retry.
- Reject content when the grid cannot resolve to three rows, a row cannot resolve to four separated figures, a figure is clipped or touches a neighbor, the middle row shows a face, the bottom row faces left, identity/outfit drifts, or step frames show no readable motion.
- The builder validates leg phase before writing a pack. `MOTION_PHASE_FAILED directions=down,up` means only those named rows need replacement; ordinary pixel or arm differences do not prove leg alternation.
- If one or two rows fail but the grid is otherwise usable, keep the production sheet and generate only those direction rows in one parallel supplement round. Use the same photo and style board plus the corresponding row from the layout template, and repeat the screen-space leg rules above verbatim.
- If the full grid is unusable, make one targeted full-sheet retry repeating all layout and style invariants. Stop after that retry.

## Separate-master prompts for quality mode

For a turnaround, request exactly three full-body figures ordered front, back, right on flat white. For each walk direction, request exactly four figures ordered neutral, gait A, neutral, gait B on flat white and repeat the direction-specific screen-space leg rule above. Use the same bright-chibi style language. Generate `down`, `up`, and `right` concurrently after accepting the turnaround; never generate left.

## Final visual acceptance

- The result reads as a small bright Q-version game sprite, not a shrunken realistic portrait.
- Hair, glasses, face shape, and outfit remain recognizable at `48x64`.
- Front, back, and right directions are unmistakable; the up row contains no face.
- The cycle reads `neutral → gait A → neutral → gait B`; front/back action shoes occupy opposite screen sides, right-profile foreground/far legs exchange phase, feet share one baseline, and no frame crosses a cell boundary.
- Final assets have binary alpha, at most 64 opaque colors, no background residue, and no text, shadow, floor, glow, or watermark.

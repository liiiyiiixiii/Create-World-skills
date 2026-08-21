# Character Generation Skill / 角色游戏化 Skill

Convert one recognizable front-facing person photo into a reusable Create World bright-chibi 2D pixel-character pack. The Skill generates three views, four-direction walk sheets, transparent animations, portable metadata, and deterministic QA results without modifying game code.

将一张清晰可辨的单人正面照片转换为可复用的 Create World 明亮 Q 版 2D 像素角色素材包。Skill 会生成三视图、四方向行走精灵表、透明动画、可移植元数据和确定性 QA 报告，不修改游戏代码。

## What it produces / 输出内容

The default package uses `48x64` cells, four frames per direction, and `170ms` per frame:

```text
<character-id>/
|-- masters/                 cleaned high-resolution source sheets
|-- sprites/png/             three-view and four-direction PNG sheets
|-- sprites/webp/            lossless WebP direction sheets
|-- animations/              down/up/right/left APNG and overview GIF
|-- character.json           portable schema-versioned manifest
`-- qa-report.json           background, layout, palette, motion, and animation QA
```

默认素材包使用 `48x64` 单元格、每方向 4 帧、每帧 `170ms`。左向动作由右向逐帧镜像生成，三视图顺序为正面、背面、右侧面。

## Requirements / 依赖

- Codex with built-in image generation
- Python 3.10 or newer
- `Pillow>=10,<13`

Install the runtime dependency from the repository root:

```shell
python -m pip install -r skills/character-generation/requirements.txt
```

## Install / 安装 Skill

Copy or link this directory to the Codex Skills directory while keeping the folder name `character-generation`:

```text
$CODEX_HOME/skills/character-generation
```

When `CODEX_HOME` is unset, the usual location is `~/.codex/skills/character-generation`.

将本目录复制或链接到 Codex Skills 目录，并保持文件夹名称为 `character-generation`。未设置 `CODEX_HOME` 时，常见路径是 `~/.codex/skills/character-generation`。

## Usage / 调用

Attach or provide one front-facing photo, then invoke:

```text
$character-generation <front-facing photo>
```

```text
$character-generation <正面人物照片>
```

Optional parameters:

| Parameter | Default | Purpose |
|---|---:|---|
| `character_id` | derived from filename | Portable output identifier |
| `output_dir` | `./output/character-generation/` | Package destination root |
| `cell_size` | `48x64` | Target sprite cell size |
| `frame_duration` | `170` | Animation frame duration in milliseconds |
| `generation_mode` | `balanced` | Speed/retry strategy: `balanced`, `fast`, or `quality` |

`balanced` normally requests one `3x4` production sheet and regenerates only failed directions. `fast` stops after the first invalid generation. `quality` uses separate masters and generates direction sheets concurrently.

## Generation and QA / 生成与验收

The production sheet has three rows (`down`, `up`, `right`) and four columns (`neutral`, `gait-A`, `neutral`, `gait-B`). The builder then:

- removes supported white, checkerboard, or alpha backgrounds;
- separates and normalizes figures to a shared foot baseline;
- makes the first and third frames exactly identical;
- verifies that front/back action shoes switch screen sides;
- verifies that right-profile foreground and far legs exchange gait phase;
- mirrors the accepted right-facing frames to produce left-facing art;
- exports binary transparency, a shared palette of at most 64 colors, animations, metadata, and QA.

If the grid, identity, direction, clipping, background confidence, or leg phase cannot be validated, the workflow stops rather than silently publishing damaged assets. In `balanced` mode, valid rows remain available for one targeted supplement round.

## Privacy and reference assets / 隐私与参考素材

- The input photo is never copied into the final package or this repository.
- Final JSON files contain only relative artifact paths, never the photo's absolute path.
- Resumable local staging stores the photo filename and SHA-256 fingerprint, not the photo itself.
- The two bundled PNG references are anonymous and generated deterministically by `scripts/generate_reference_assets.py` without photos, private game assets, network access, or model training.
- “Learning the style” means reference-board and prompt conditioning; it is not model fine-tuning.

- 输入照片不会被复制到最终素材包或本仓库。
- 最终 JSON 只记录相对素材路径，不记录照片绝对路径。
- 本地断点续跑仅保存照片文件名和 SHA-256 指纹，不保存照片本身。
- 两张 PNG 参考图由 `scripts/generate_reference_assets.py` 匿名、确定性生成，不读取照片、私有游戏素材或网络资源，也不涉及模型微调。

## Development and tests / 开发与测试

Run the complete regression suite from the repository root:

```shell
python -m unittest discover -s skills/character-generation/scripts -p "test_*.py" -v
```

Rebuild the anonymous references in a temporary directory and compare them with the bundled assets:

```shell
python skills/character-generation/scripts/generate_reference_assets.py --output-dir <temporary-directory>
```

Validate the Skill structure with Codex's `skill-creator/scripts/quick_validate.py` when that system utility is available.

Technical details are maintained in [the generation workflow](references/generation-workflow.md) and [the pack contract](references/pack-contract.md). Codex loads [SKILL.md](SKILL.md) as the actual Skill entrypoint.

## Known limitations / 已知限制

- Image generation is nondeterministic and may require a targeted retry.
- A headshot requires conservative inference for unseen clothing and body shape.
- Left-facing frames mirror asymmetric clothing and accessories.
- The Skill produces an independent asset package; engine registration and game-code integration are outside its scope.

## License / 许可

The Skill's code, documentation, and programmatically generated images are licensed under the repository's [MIT License](../../LICENSE).

本 Skill 的代码、文档和程序化生成图片采用仓库根目录的 [MIT License](../../LICENSE)。

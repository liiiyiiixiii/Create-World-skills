# Create World Skills / 创世界 Skills

Reusable open-source Skills distilled from building 2D games and interactive worlds. The repository began with methods developed during *Beyond the Wall* and now publishes portable, engine-agnostic workflows.

从 2D 游戏与互动世界开发中沉淀的可复用开源 Skills。本仓库起源于《高墙之外》的制作方法，并将其整理为可移植、与具体引擎无关的工作流。

## Skills

### [Character Generation / 角色游戏化](skills/character-generation/README.md)

`skills/character-generation` converts one recognizable front-facing person photo into a bright chibi 2D pixel-character pack: a three-view turnaround, four-direction transparent walk sheets, APNG animations, an overview GIF, metadata, and QA results.

`skills/character-generation` 将一张清晰的单人正面照片转换为明亮 Q 版 2D 像素角色素材包，包括三视图、四方向透明行走精灵表、APNG 动画、总览 GIF、元数据和 QA 报告。

## Repository structure / 仓库结构

```text
Create-World-skills/
|-- README.md                         Skill 体系总览与目录
|-- LICENSE
`-- skills/
    |-- character-generation/
    |   |-- README.md                 面向使用者的独立说明
    |   |-- SKILL.md                  Codex Skill 入口与执行规范
    |   `-- agents, assets, references, scripts
    `-- <future-skill>/
        |-- README.md
        `-- SKILL.md
```

Each folder under `skills/` is an independently documented Skill. The root README is the catalog for the whole system; a Skill's own README explains installation, inputs, outputs, limits, and development, while `SKILL.md` remains the concise executable instruction entrypoint for Codex.

`skills/` 下的每个文件夹都是一个可独立理解的 Skill。根 README 是整个体系的目录；各 Skill 自己的 README 负责安装、输入输出、限制与开发说明，`SKILL.md` 则保持为供 Codex 加载的精简执行入口。

## Install / 安装

1. Install the only runtime dependency:

   ```shell
   python -m pip install -r skills/character-generation/requirements.txt
   ```

2. Copy or link `skills/character-generation` to your Codex Skills directory as `character-generation`. The usual destination is `$CODEX_HOME/skills/character-generation` or `~/.codex/skills/character-generation`.

1. 安装唯一的运行依赖：

   ```shell
   python -m pip install -r skills/character-generation/requirements.txt
   ```

2. 将 `skills/character-generation` 复制或链接到 Codex Skills 目录，并保持目录名为 `character-generation`。常用目标位置为 `$CODEX_HOME/skills/character-generation` 或 `~/.codex/skills/character-generation`。

## Usage / 调用

Attach or provide one front-facing photo, then invoke:

```text
$character-generation <front-facing photo>
```

Optional parameters are `character_id`, `output_dir`, `cell_size`, `frame_duration`, and `generation_mode` (`balanced`, `fast`, or `quality`). The default output cell is `48x64` with four frames at `170ms` each.

附加或提供一张正面照片后调用：

```text
$character-generation <正面照片>
```

可选参数为 `character_id`、`output_dir`、`cell_size`、`frame_duration` 和 `generation_mode`（`balanced`、`fast` 或 `quality`）。默认输出为 `48x64` 单元格、4 帧、每帧 `170ms`。

## Test / 测试

From the repository root:

```shell
python -m unittest discover -s skills/character-generation/scripts -p "test_*.py" -v
python skills/character-generation/scripts/generate_reference_assets.py --output-dir <temporary-directory>
```

The tests cover transparent/background cleanup, `3x4` segmentation, four-direction packing, resumable local jobs, deterministic leg alternation, and pixel-exact reproducibility of the anonymous reference assets.

测试覆盖透明与背景清理、`3x4` 分割、四方向打包、本地断点续跑、确定性的左右腿交替，以及匿名参考素材的逐像素可复现性。

## Privacy and references / 隐私与参考素材

- The Skill does not bundle a user photo, copy it into the final pack, or store its absolute path in final metadata.
- Resumable staging stores a local SHA-256 fingerprint and the source filename, but not the image itself or its absolute path.
- Both bundled PNG references are anonymous and generated deterministically by `generate_reference_assets.py`; they do not read photos, private game assets, or network resources.

- Skill 不内置用户照片，不将照片复制进最终素材包，也不会在最终元数据中保存照片绝对路径。
- 断点续跑暂存仅记录本地 SHA-256 指纹和源文件名，不保存图片本身或绝对路径。
- 两张随附 PNG 参考图均由 `generate_reference_assets.py` 确定性生成，不读取照片、私有游戏素材或网络资源。

## License / 许可

The code, documentation, and programmatically generated images in this repository are licensed under the [MIT License](LICENSE).

本仓库中的代码、文档和程序化生成图片均采用 [MIT License](LICENSE)。

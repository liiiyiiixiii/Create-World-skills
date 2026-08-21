# Character Generation Skill / 角色游戏化 Skill

[← 返回 Create World Skills 总目录](../../README.md)

**状态：可用 / Status: Available**

将一张清晰可辨的单人正面照片转换为可复用的 Create World 明亮 Q 版 2D 像素角色素材包。Skill 会生成三视图、四方向行走精灵表、透明动画、可移植元数据和确定性 QA 报告，不修改游戏代码。

Convert one recognizable front-facing person photo into a reusable Create World bright-chibi 2D pixel-character pack with three views, four-direction walk sheets, transparent animations, portable metadata, and deterministic QA results.

## 输入要求 / Input

- 一张只包含一个清晰人物的正面照片；支持头像或全身照。
- 人脸应可辨认，不能严重遮挡；多人物或无法判断身份时停止生成。
- 缺失的体型与服装信息会根据照片中可见内容保守补全。

Provide one recognizable front-facing person photo. Headshots and full-body photos are supported; ambiguous, severely obstructed, or multi-person images are rejected.

## 输出内容 / Output

默认素材包使用 `48x64` 单元格、每方向 4 帧、每帧 `170ms`。左向动作由右向逐帧镜像生成，三视图顺序为正面、背面、右侧面。

```text
<character-id>/
|-- masters/                 清理后的高清母版
|-- sprites/png/             三视图与四方向 PNG 精灵表
|-- sprites/webp/            无损 WebP 方向精灵表
|-- animations/              down/up/right/left APNG 与总览 GIF
|-- character.json           版本化、可移植素材清单
`-- qa-report.json           背景、布局、色板、动作与动画 QA
```

The default package uses `48x64` cells, four frames per direction, and `170ms` per frame.

## 依赖与安装 / Requirements and Installation

- 支持内置图像生成能力的 Codex
- Python 3.10 或更高版本
- `Pillow>=10,<13`

从仓库根目录安装运行依赖：

```shell
python -m pip install -r skills/character-generation/requirements.txt
```

将本目录复制或链接到 Codex Skills 目录，并保持文件夹名为 `character-generation`：

```text
$CODEX_HOME/skills/character-generation
```

未设置 `CODEX_HOME` 时，常见位置为 `~/.codex/skills/character-generation`。

Install Pillow from the repository requirements file, then copy or link this directory into the Codex Skills directory as `character-generation`.

## 调用方法 / Usage

附加或提供一张正面人物照片，然后调用：

```text
$character-generation <正面人物照片>
```

可选参数：

| 参数 | 默认值 | 用途 |
|---|---:|---|
| `character_id` | 从文件名推导 | 可移植的输出标识符 |
| `output_dir` | `./output/character-generation/` | 素材包输出根目录 |
| `cell_size` | `48x64` | 目标精灵单元格尺寸 |
| `frame_duration` | `170` | 动画每帧时长，单位为毫秒 |
| `generation_mode` | `balanced` | 速度与补生成策略 |

生成模式：

- `balanced`：默认只请求一张 `3x4` 生产总表，仅补生成校验失败的方向。
- `fast`：只生成一次，首次校验失败即停止。
- `quality`：三视图与动作母版分开生成，三个动作方向并行执行。

Optional parameters are `character_id`, `output_dir`, `cell_size`, `frame_duration`, and `generation_mode` (`balanced`, `fast`, or `quality`).

## 生成与 QA / Generation and QA

生产总表包含三行 `down`、`up`、`right` 和四列 `neutral`、`gait-A`、`neutral`、`gait-B`。构建器会确定性地：

- 清理支持的白底、棋盘格或 Alpha 背景；
- 分离人物，并按统一脚底基线归一化；
- 将第一帧精确复制为第三帧；
- 检查正面与背面的动作鞋是否在画面左右两侧交替；
- 检查右侧面的前景腿与远景腿是否交换步态相位；
- 镜像已通过的右向帧生成左向素材；
- 输出二值透明、最多 64 色的共享色板、动画、元数据和 QA 报告。

如果网格、身份、方向、裁切、背景置信度或腿部相位无法通过验收，流程会停止，而不会静默发布损坏素材。`balanced` 模式会保留有效行，并允许一轮定向补生成。

The builder validates layout, transparency, identity consistency, palette limits, animation structure, and deterministic alternating-leg phases before publishing a pack.

## 隐私与参考素材 / Privacy and Reference Assets

- 输入照片不会被复制到最终素材包或本仓库。
- 最终 JSON 只记录相对素材路径，不记录照片绝对路径。
- 本地断点续跑仅保存照片文件名和 SHA-256 指纹，不保存照片本身。
- 两张随附 PNG 参考图由 `scripts/generate_reference_assets.py` 匿名、确定性生成，不读取照片、私有游戏素材或网络资源，也不涉及模型微调。
- 本仓库的 MIT License 不会自动应用于用户照片或基于用户材料生成的输出。

Input photos are not bundled with the Skill or copied into final packs. The bundled visual references are anonymous, reproducible, and generated without private assets or network access.

## 开发与测试 / Development and Tests

从仓库根目录运行完整回归测试：

```shell
python -m unittest discover -s skills/character-generation/scripts -p "test_*.py" -v
```

在临时目录重新生成匿名参考素材：

```shell
python skills/character-generation/scripts/generate_reference_assets.py --output-dir <temporary-directory>
```

系统中存在 `skill-creator/scripts/quick_validate.py` 时，使用它验证 Skill 结构。

技术细节见[生成工作流](references/generation-workflow.md)和[素材包契约](references/pack-contract.md)。Codex 实际加载的入口是 [SKILL.md](SKILL.md)。

## 已知限制 / Known Limitations

- 图像生成具有非确定性，可能需要一次定向重试。
- 头像照片需要保守推断不可见的服装和体型。
- 左向帧会镜像不对称服装与配饰。
- Skill 只生成独立素材包，不负责游戏引擎注册或代码集成。

Image generation is nondeterministic, headshots require conservative inference, asymmetric details are mirrored for left-facing frames, and engine integration remains outside this Skill's scope.

## 许可 / License

本 Skill 的代码、文档和匿名程序化参考素材采用仓库根目录的 [MIT License](../../LICENSE)。用户提供的材料及基于其生成的输出不自动纳入该许可。

The Skill's repository code, documentation, and anonymous programmatic reference assets are licensed under the [MIT License](../../LICENSE); user-provided materials and derived outputs are not automatically relicensed.

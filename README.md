# Create-World-skills
A methodology developed during the creation of the 2D game *Beyond the Wall*, designed to transform linear content into 2D-style games and continuously evolve the process into reusable Skills.
在2D游戏《高墙之外》开发时整理出的一套方法，用于把线性内容转化为 2D 风格游戏，并持续沉淀为可复用的 Skills

## 什么是 Create World Skills？ / What is Create World Skills?

Create World Skills 是一套面向创作者与开发者的开源 Codex Skills，源自真实的 2D 游戏制作实践。项目把人物、叙事和世界构建过程中反复出现的方法，整理为可独立安装、调用、阅读和测试的创作工具。

Create World Skills is an open-source collection of Codex Skills distilled from real 2D game production. Each Skill packages one reusable creative workflow and can be installed, used, documented, and tested independently.

## Skill 体系 / Skill System

Create World Skills 按照从原作理解、改编设计、资产生成，到游戏组装、状态管理与最终验收的顺序组织。每个 Skill 保持模块化，可以独立开发和使用；未来可以连接为完整工作流。目前 Content Understanding、Art Direction 与 Dialogue 以 Beta 形式发布，Scene Generation 与 Character Generation 已正式可用；它们尚未形成完整自动化流水线。

| 序号 | Skill | 状态 | 主要职责 |
|---:|---|---|---|
| 1 | [Content Understanding](skills/content-understanding/README.md) | **Beta** | 原作整体结构化 |
| 2 | `Game Adaptation` | **即将上线 / Coming soon** | 确定游戏类型、玩家身份、核心体验 |
| 3 | [Art Direction](skills/art-direction/README.md) | **Beta** | 确定整体视觉风格 |
| 4 | `Main Flow` | **开发中 / In development** | 确定完整游戏主流程 |
| 5 | `Narrative Branch` | **开发中 / In development** | 设计支线、选择与结局 |
| 6 | `Easter Egg` | **即将上线 / Coming soon** | 设计彩蛋与隐藏内容 |
| 7 | `Gameplay Design` | **开发中 / In development** | 设计核心玩法与玩法循环 |
| 8 | [Scene Generation](skills/scene-generation/README.md) | **可用 / Available** | 生成游戏场景和空间 |
| 9 | [Character Generation](skills/character-generation/README.md) | **可用 / Available** | 角色游戏化并生成角色动作 |
| 10 | `Interaction Generation` | **开发中 / In development** | 把剧情事件转成可操作行为 |
| 11 | [Dialogue](skills/narrative-npc-dialogue/README.md) | **Beta** | 生成 NPC 对话 |
| 12 | `Game Assembly` | **开发中 / In development** | 组合场景、角色与玩法 |
| 13 | `Game State` | **开发中 / In development** | 管理世界状态 |
| 14 | `Reviewer` | **开发中 / In development** | 自动测试与一致性检查 |

The roadmap runs from source understanding and adaptation design through asset creation, assembly, state management, and review. Content Understanding, Art Direction, and Dialogue are published as betas; Scene Generation and Character Generation are available. The Skills remain modular and do not yet form a complete automated pipeline.
## Character Generation Skill

<p align="center">
  <img src="skills/character-generation/assets/character-generation-preview.gif" width="320" alt="Character Generation 匿名四向像素角色动画预览">
</p>

**单人正面照片 → 三视图、四向精灵表、动画和 QA 报告。** Character Generation 把角色设计约束、动作生成、透明背景处理、精灵打包和质量检查收拢到一个可复用 Skill 中。

```text
$character-generation <正面人物照片>
```

预览使用 Character Generation 输出的示例精灵表，并由公开脚本确定性生成前、后、左、右四个 GIF 和四方向总览。仓库不包含真人照片；实际角色会依据用户提供的照片生成。查看 [Character Generation 独立说明](skills/character-generation/README.md)了解输入要求、参数、输出和限制。

**One front-facing photo → turnaround views, four-direction sprite sheets, animations, and QA.** The preview is deterministically packed from a showcase sprite sheet; generated characters are based on the user's own photo.

## 快速开始 / Quick Start

1. 克隆仓库：

   ```shell
   git clone https://github.com/liiiyiiixiii/Create-World-skills.git
   cd Create-World-skills
   ```

2. 安装目标 Skill 的依赖。例如 Character Generation：

   ```shell
   python -m pip install -r skills/character-generation/requirements.txt
   ```

3. 将目标 Skill 文件夹复制或链接到 Codex Skills 目录，并保留原文件夹名称：

   ```text
   $CODEX_HOME/skills/character-generation
   ```

   未设置 `CODEX_HOME` 时，常见位置是 `~/.codex/skills/character-generation`。

4. 在 Codex 中提供所需材料并调用 Skill：

   ```text
   $character-generation <正面人物照片>
   ```

具体依赖、参数、输出和限制以各 Skill 文件夹内的 README 为准。

Clone the repository, install the selected Skill's dependencies, copy or link its folder into the Codex Skills directory, and invoke it with `$skill-name`. See each Skill's README for its complete contract.

## 项目起源 / Origin

Create World Skills 起源于 2D 游戏《高墙之外》的开发实践。制作过程中，叙事整理、角色游戏化、素材规范和质量检查不断重复出现；这个仓库把其中可复用的部分沉淀为边界清晰、能够独立安装和测试的 Skills。它们从一款游戏中生长出来，但不只服务于这一款游戏。

Create World Skills grew out of recurring production problems in *Beyond the Wall*: structuring narrative material, turning people into playable characters, normalizing assets, and checking quality. The resulting Skills are reusable beyond the original game.

## 设计原则 / Principles

- **模块化 / Modular**：每个 Skill 解决一个边界明确的问题，不依赖未发布的工作流。
- **可移植 / Portable**：输出使用清晰的文件结构、相对路径和可复用格式，不绑定具体游戏工程。
- **可测试 / Testable**：关键转换尽量交给确定性脚本，并为重要约束提供自动化 QA。
- **隐私明确 / Privacy-aware**：输入材料、暂存数据、最终产物和开源参考素材之间保持清晰边界。

## 仓库结构 / Repository Structure

```text
Create-World-skills/
|-- README.md                         Skill 体系总览与目录
|-- LICENSE
`-- skills/
    |-- content-understanding/
    |   |-- README.md
    |   |-- SKILL.md
    |   `-- agents, references, scripts, tests
    |-- art-direction/
    |   |-- README.md
    |   |-- SKILL.md
    |   `-- agents, references, scripts, tests
    |-- scene-generation/
    |   |-- README.md
    |   |-- SKILL.md
    |   `-- agents, assets, references, scripts, tests
    |-- character-generation/
    |   |-- README.md
    |   |-- SKILL.md
    |   `-- agents, assets, references, scripts
    `-- narrative-npc-dialogue/
        |-- README.md
        |-- SKILL.md
        `-- agents, references, tests
```
## ⭐ Support / 支持

如果你喜欢这个项目，欢迎点一个 **Star ⭐**。

也欢迎通过 [GitHub Issues](https://github.com/liiiyiiixiii/Create-World-skills/issues) 提交 Bug、建议或体验反馈。

If you find this project useful, please consider giving it a **Star ⭐**. Bug reports, suggestions, and experience feedback are welcome through [GitHub Issues](https://github.com/liiiyiiixiii/Create-World-skills/issues).

## 许可与内容边界 / License and Content Boundaries

本仓库中的代码、文档和匿名程序化参考素材采用 [MIT License](LICENSE)。用户提供的照片、叙事材料以及基于这些材料生成的输出，不会因为使用本仓库而自动采用 MIT License。贡献者只应提交自己有权按 MIT License 发布的仓库内容。

Code, documentation, and anonymous programmatically generated reference assets in this repository are licensed under the [MIT License](LICENSE). User-provided materials and outputs derived from them are not automatically relicensed under MIT by using these Skills.

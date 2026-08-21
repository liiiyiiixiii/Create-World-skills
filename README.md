# Create-World-skills
A methodology developed during the creation of the 2D game *Beyond the Wall*, designed to transform linear content into 2D-style games and continuously evolve the process into reusable Skills.
在2D游戏《高墙之外》开发时整理出的一套方法，用于把线性内容转化为 2D 风格游戏，并持续沉淀为可复用的 Skills

## 什么是 Create World Skills？ / What is Create World Skills?

Create World Skills 是一套面向创作者与开发者的开源 Codex Skills，源自真实的 2D 游戏制作实践。项目把人物、叙事和世界构建过程中反复出现的方法，整理为可独立安装、调用、阅读和测试的创作工具。

Create World Skills is an open-source collection of Codex Skills distilled from real 2D game production. Each Skill packages one reusable creative workflow and can be installed, used, documented, and tested independently.

## Skill 目录 / Skill Catalog

| Skill | 状态 | 输入 | 输出 |
|---|---|---|---|
| [Character Generation](skills/character-generation/README.md) | **可用 / Available** | 单人正面照片 | 三视图、四向像素角色精灵表、动画与 QA 报告 |
| `Content Understanding` | **开发中 / In development** | 剧本、字幕、小说等叙事材料 | 可追溯的因果主干、精选片段以及 Markdown/YAML 结构稿 |

当前两条能力线相互独立：Character Generation 负责角色素材，Content Understanding 负责叙事结构。本仓库暂不宣称它们已经组成自动化游戏生成流水线，也不承诺开发中 Skill 的发布日期。

The two capability tracks are currently independent. Character Generation produces character assets; Content Understanding structures narrative material and is not yet published in this repository.

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
    |-- character-generation/
    |   |-- README.md                 面向使用者的独立说明
    |   |-- SKILL.md                  Codex Skill 入口与执行规范
    |   `-- agents, assets, references, scripts
    `-- <future-skill>/
        |-- README.md
        `-- SKILL.md
```

## 许可与内容边界 / License and Content Boundaries

本仓库中的代码、文档和匿名程序化参考素材采用 [MIT License](LICENSE)。用户提供的照片、叙事材料以及基于这些材料生成的输出，不会因为使用本仓库而自动采用 MIT License。贡献者只应提交自己有权按 MIT License 发布的仓库内容。

Code, documentation, and anonymous programmatically generated reference assets in this repository are licensed under the [MIT License](LICENSE). User-provided materials and outputs derived from them are not automatically relicensed under MIT by using these Skills.

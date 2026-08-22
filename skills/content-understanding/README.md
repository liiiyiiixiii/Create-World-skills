# Content Understanding Skill

**先把故事读明白，再决定玩家怎样走进去。**  
**Understand the story first. Then decide how the player steps into it.**

`Beta` · `Schema 2.0` · `$content-understanding`

## 为什么做这个 / Why This Exists

把电影、小说或剧本改成游戏时，很容易一上来就谈机制，却还没有真正理清故事：哪些事件互为因果，人物为什么改变，哪些物件一路传递，哪些片段虽然不推动主线，却让人记了很多年。

Content Understanding 先做这一步。它把线性叙事整理成一份有出处、能修改、方便讨论的结构稿，再在每个事件旁留下一条简短的玩法提示。结果不是一篇泛泛的剧情摘要，而是一份创作者可以逐条核对、质疑和调整的工作底稿。

When adapting a film, novel, or screenplay into a game, it is tempting to jump straight to mechanics. But first you need a firm grasp of the story: what causes what, why a character changes, how an object or a piece of information travels, and which memorable moments deserve to survive even when they do not move the main plot forward.

Content Understanding handles that first pass. It turns a linear narrative into a sourced, editable structure, then adds one small interaction idea beside each event. The result is not a generic plot summary. It is a working document that creators can inspect, challenge, and revise together.

## 它会整理什么 / What It Captures

- 故事脊柱与支撑事件；
- 值得保留的经典、有趣或用户指定片段；
- 人物目标、关系和状态的变化；
- 关键物件、地点、信息与意象的流转；
- 铺垫、回收、因果边和材料缺口；
- 每个事件的轻量玩法提示：玩家做什么，这段体验要保留什么。

The Skill records:

- the causal spine and its supporting events;
- memorable, unusual, or user-marked moments worth keeping;
- changes in character goals, relationships, and state;
- the movement of important objects, places, information, and motifs;
- setups, payoffs, causal links, and gaps in the source material;
- a lightweight interaction hint for every event: what the player might do, and what the moment must preserve.

普通节点只给一句简明建议。只有同时具备信息发现、关系冲突、时间压力、风险变化、情绪峰值等多项价值的节点，才会得到稍完整的 2–4 步交互构想。

Ordinary nodes receive one concise suggestion. A node gets a fuller two-to-four-step interaction sketch only when it carries several kinds of value, such as discovery, conflict, pressure, changing risk, or an emotional peak.

## 它不做什么 / What It Does Not Do

它不会替你设计整部游戏，也不会擅自改写原作结局。核心循环、数值、关卡结构、剧情分支和玩法平衡，应该留给后续的 Gameplay Design 或改编设计工作。

It does not design the whole game, and it does not quietly rewrite the ending. Core loops, numbers, level structure, branching storylines, and balance belong to a later gameplay or adaptation design stage.

## 输入与材料边界 / Inputs and Source Boundaries

可用材料包括剧本、字幕、小说章节、漫画文字稿、戏剧、PDF/DOCX 提取文本、网页文本、梗概和场景笔记。只有作品名时，Skill 会先请求材料或联网授权，不会靠模型记忆补完未知剧情。

Supported inputs include screenplays, subtitles, novel chapters, comic transcripts, plays, extracted PDF/DOCX text, web text, synopses, and scene notes. If you provide only a title, the Skill asks for source material or permission to research it instead of filling gaps from memory.

电影和音频需要字幕、剧本或场景笔记。本 Skill 不直接观看完整电影，也不直接分析原始音频。材料不完整没有关系：结果会明确写成部分分析，并把缺失范围留下来。

Film and audio work requires subtitles, a screenplay, or scene notes. The Skill does not directly watch a full film or analyse raw audio. Incomplete material is fine: the output is marked as partial, with the missing range recorded openly.

## 输出 / Output

```text
structured-narrative/<work-slug>/
|-- overview.md       一页概览 / one-page overview
|-- structure.md      完整审阅稿 / full review document
`-- structure.yaml    唯一数据源 / canonical source
```

`structure.yaml` 是唯一规范数据源；两个 Markdown 文件都由它确定性生成。明确修订旧结果时，还会写入 `CHANGELOG.md` 和 `revisions/r####.yaml`。

`structure.yaml` is the canonical source. Both Markdown files are rendered from it deterministically. An explicit revision also writes `CHANGELOG.md` and `revisions/r####.yaml`.

字段说明见 [references/schema.md](references/schema.md)，机器可读规则见 [references/structure-v2.schema.json](references/structure-v2.schema.json)。  
See [references/schema.md](references/schema.md) for the field guide and [references/structure-v2.schema.json](references/structure-v2.schema.json) for the machine-readable rules.

## 快速开始 / Quick Start

在 Create World Skills 仓库根目录运行：  
Run these commands from the root of the Create World Skills repository:

```shell
python -m pip install -r skills/content-understanding/requirements.txt
python -m unittest discover -s skills/content-understanding/tests -v
python skills/content-understanding/scripts/install_skill.py --dry-run
python skills/content-understanding/scripts/install_skill.py --update
```

安装脚本默认同步到 `$CODEX_HOME/skills/content-understanding`；如果没有设置 `CODEX_HOME`，则使用 `~/.codex/skills/content-understanding`。它只添加或更新文件，不会删除目标目录里的额外内容。

By default, the installer syncs to `$CODEX_HOME/skills/content-understanding`, or `~/.codex/skills/content-understanding` when `CODEX_HOME` is not set. It adds and updates files, but never deletes extra files from the target directory.

安装后，在 Codex 中这样调用：  
After installation, invoke it in Codex like this:

```text
$content-understanding 请整理我提供的剧本，并为每个事件补充简短玩法提示。
```

需要联网时，请明确授权。某个片段一定要保留时，也可以直接说出来。  
Say so explicitly if web research is allowed, and mark any scene that must be kept.

## 审阅与修改 / Review and Revision

每个节点和片段都有稳定 ID。你可以按 ID 锁定、排除、恢复、合并或拆分内容，也可以调整主干层级、玩法优先级和来源。锁定项不会被自动删除；排除项仍会留在 YAML 的审计记录里。

Every node and fragment has a stable ID. You can lock, exclude, restore, merge, or split items by ID, as well as change spine status, interaction priority, or sources. Locked items are never removed automatically, and excluded items remain in the YAML audit trail.

## 校验与开发 / Validation and Development

```shell
python skills/content-understanding/scripts/validate_structure.py path/to/structure.yaml
python skills/content-understanding/scripts/render_structure.py path/to/structure.yaml --output-dir path/to/output
python skills/content-understanding/scripts/archive_revision.py path/to/structure.yaml
```

提交修改前，请运行测试和严格校验：  
Before submitting a change, run the tests and strict validation:

```shell
python -m unittest discover -s skills/content-understanding/tests -v
python skills/content-understanding/scripts/validate_structure.py skills/content-understanding/tests/fixtures/fog-harbor-v2.yaml --warnings-as-errors
```

新测试材料必须是原创、公共领域或已获授权内容。请勿提交用户剧本、字幕、小说正文、抓取的版权材料、分析产物、缓存或本机路径。

New fixtures must be original, public-domain, or properly licensed. Do not commit user scripts, subtitles, novel text, scraped copyrighted material, generated analyses, caches, or local machine paths.

## 项目结构 / Project Structure

```text
content-understanding/
|-- SKILL.md                       Codex instructions
|-- README.md                      project guide
|-- agents/openai.yaml             Codex UI metadata
|-- references/                    method, schema, and original example
|-- scripts/                       validation, rendering, revision, install
`-- tests/                         unittest suite and original fixture
```

## Beta 范围 / Beta Scope

当前版本已经覆盖叙事拆解、逐节点玩法提示、确定性渲染、修订记录和自动校验。关系图可视化、多人协作、完整影音理解和完整玩法设计暂不在范围内。Schema 2.0 不会自动迁移 1.x 产物。

The current Beta covers narrative breakdown, per-node interaction hints, deterministic rendering, revision history, and automated validation. Relationship visualisation, multi-user collaboration, full audiovisual understanding, and full gameplay design are out of scope for now. Schema 2.0 does not automatically migrate 1.x outputs.

## 许可与内容边界 / License and Content Boundaries

代码、文档和原创测试材料遵循仓库根目录的 [MIT License](../../LICENSE)。用户提供的材料和基于这些材料生成的结果，不会因为使用本 Skill 而自动采用 MIT License。

Code, documentation, and original test material follow the repository's [MIT License](../../LICENSE). User-provided source material and outputs derived from it do not become MIT-licensed simply because this Skill was used.


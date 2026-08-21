# Content Understanding Skill

> 面向游戏改编创作者的线性叙事拆解工具。把剧本、字幕、小说、漫画等材料转成可追溯的叙事档案，并在每个事件节点旁附上克制、忠于原作功能的玩法提示。

**Status: Beta · Schema: 2.0 · Codex invocation: `$content-understanding`**

Content Understanding is a Codex Skill for creators adapting linear stories into games. It produces a traceable narrative record—rather than a loose summary—and adds lightweight, local interaction ideas without designing an entire game system.

## 项目定位

改编前期最难的不是立刻想玩法，而是先回答三个问题：原作发生了什么、为什么发生、哪些体验值得在游戏里保留。本 Skill 位于“读懂原作”和“完整玩法设计”之间，交付一个可供创作者审阅、修改并继续加工的结构化中间层。

- **面向谁**：正在把电影、剧本、小说、漫画或戏剧改编成游戏的个人创作者和小团队。
- **解决什么**：把线性材料整理为故事脊柱、支撑事件、精选片段、人物变化、物件/信息流、铺垫回收和因果关系。
- **额外价值**：每个事件节点回答“玩家可以做什么”和“必须保留什么体验”；高价值节点才给出稍详细的 2–4 步交互形态。
- **不是什么**：不是普通摘要器，也不是自动生成完整游戏的流水线。它不负责核心循环、数值、完整关卡、分支剧情或玩法平衡。

## 核心原则

- **可追溯**：原作事实必须引用页码、章节、文本行或字幕时间戳。
- **事实分栏**：原作事实、分析推断和玩法提案分别记录，避免把设计想法伪装成原作内容。
- **覆盖诚实**：材料覆盖与目标版本可信度分别标记；读完剧本不等于核验最终成片。
- **保留精彩**：关键剧情、经典片段、有趣片段和用户锁定片段可以并存，非因果片段不会仅因“不推动剧情”而被过滤。
- **玩法克制**：玩法提示默认保持原节点的结果、状态变化和因果功能，不主动改写剧情。
- **YAML 优先**：`structure.yaml` 是唯一规范数据源，两个 Markdown 文件由脚本确定性生成。

## 输入

可处理剧本、字幕、小说章节、漫画文字稿、戏剧、PDF/DOCX 提取文本、网页文本、梗概和场景笔记。只有作品名时，Skill 会请求材料或联网授权，不凭模型记忆补齐剧情。

电影和音频任务需要字幕、剧本或场景笔记；本 Skill 不直接理解完整原始影音。材料不完整时会输出部分分析并登记缺口。

## 输出

```text
structured-narrative/<作品-slug>/
|-- overview.md       一页式入口：故事脊柱、高价值候选、精选片段和缺口
|-- structure.md      完整、适合人工审阅的叙事结构
`-- structure.yaml    唯一规范数据源
```

明确修订既有结果时，还会追加：

```text
|-- CHANGELOG.md
`-- revisions/
    `-- r####.yaml
```

Schema 2.0 的完整字段说明见 [references/schema.md](references/schema.md)，JSON Schema 位于 [references/structure-v2.schema.json](references/structure-v2.schema.json)。

## 快速开始

从 Create World Skills 仓库根目录运行：

```shell
python -m pip install -r skills/content-understanding/requirements.txt
python -m unittest discover -s skills/content-understanding/tests -v
python skills/content-understanding/scripts/install_skill.py --dry-run
python skills/content-understanding/scripts/install_skill.py --update
```

安装脚本默认同步到 `$CODEX_HOME/skills/content-understanding`；未设置 `CODEX_HOME` 时使用 `~/.codex/skills/content-understanding`。它只添加或更新源码中存在的文件，不会删除目标目录中的额外文件。

安装后在 Codex 中调用：

```text
$content-understanding 请整理我提供的剧本，并为每个事件节点补充简短玩法提示。
```

如果允许联网，请在请求中明确说明；如果某个片段必须保留，也请直接标记。

## 校验与渲染

```shell
python skills/content-understanding/scripts/validate_structure.py path/to/structure.yaml
python skills/content-understanding/scripts/render_structure.py path/to/structure.yaml --output-dir path/to/output
python skills/content-understanding/scripts/archive_revision.py path/to/structure.yaml
```

校验器检查 Schema、稳定 ID、外键、覆盖状态、主干连通性、锁定项、外部评价来源和玩法提示完整性。未通过校验的 YAML 不应渲染或交付。

## 人工审阅

用户可以直接按稳定 ID：

- 锁定、排除或恢复精选片段；
- 合并、拆分节点，或切换 `spine/support`；
- 提升或降低玩法候选优先级；
- 接受、修改或删除玩法提示；
- 补充材料、来源定位或目标版本核验。

锁定项不会被自动删除；被排除的内容仍保留在 YAML 审计记录中。

## 仓库结构

```text
content-understanding/
|-- SKILL.md                         Codex 入口与执行约束
|-- README.md                        产品定位、使用和维护说明
|-- agents/openai.yaml               Codex UI 元数据
|-- references/
|   |-- method.md                    内容筛选与分析方法
|   |-- schema.md                    Schema 2.0 字段契约
|   |-- structure-v2.schema.json     机器可读 JSON Schema
|   `-- example.md                   原创短篇示例说明
|-- scripts/
|   |-- validate_structure.py        结构与语义校验
|   |-- render_structure.py          YAML → Markdown
|   |-- archive_revision.py          修订快照与变更记录
|   `-- install_skill.py             Codex Skills 单向同步
`-- tests/                           unittest 与原创 fixture
```

## Beta 范围与后续边界

当前 Beta 已覆盖叙事结构化、逐节点轻量玩法提示、确定性渲染、修订审计和自动校验。可视化关系图、多人协作、原始影音分析，以及完整的 Gameplay Design 不在当前版本范围内。

Schema 2.0 不自动迁移 1.x 历史产物。升级旧分析时，请保留原目录并创建新的 2.0 结果。

## 参与贡献

提交修改前请运行：

```shell
python -m unittest discover -s skills/content-understanding/tests -v
python skills/content-understanding/scripts/validate_structure.py skills/content-understanding/tests/fixtures/fog-harbor-v2.yaml --warnings-as-errors
```

新案例和测试材料必须是原创、公共领域或已获授权内容。请勿提交用户剧本、字幕、小说正文、联网抓取的受版权保护内容、分析产物、缓存或本机路径。

## 许可与内容边界

本 Skill 的代码、文档与原创测试材料遵循仓库根目录的 [MIT License](../../LICENSE)。用户提供的叙事材料及其派生分析结果不会因为使用本 Skill 而自动采用 MIT License。


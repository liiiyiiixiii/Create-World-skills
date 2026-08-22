# Narrative NPC Dialogue Skill / 叙事 NPC 对话 Skill

[← 返回 Create World Skills 总目录](../../README.md)

**状态：Beta / Status: Beta**

将电影改编游戏中的 NPC 对玩家、NPC 对 NPC、任务对白、环境闲谈和响应式短句，写成忠于角色、自然可演、能够推动游戏状态且可直接接入现有项目格式的对白。

Write, revise, or audit character-faithful and playable dialogue for film-adapted games while preserving selected continuity, game canon, scene state, and the host project's native format.

## 适用范围 / When to Use

- 为已有场景生成 NPC 对玩家或 NPC 对 NPC 对话；
- 扩写电影未展示的间隙场景、支线、环境对白和响应式短句；
- 修订生硬、同质化、过度说明或不符合人物知识边界的对白；
- 审核对白与任务、证据、关系、分支和保存状态是否一致。

不用于电影剧情摘要、完整剧情改写、运行时 LLM 聊天系统、配音或音频制作。

Use it for playable dialogue generation, revision, and audits—not film summaries, full-plot rewrites, runtime chat architecture, or voice production.

## 输入 / Input

最小输入是场景目标、参与者和当前剧情位置。为了提高准确性，建议同时提供：

- 明确的电影版本、剪辑版或语言版本；
- 游戏已有 canon、角色设定、任务与状态文件；
- 场景触发条件、玩家身份、关系状态和对话后的变化；
- 项目实际使用的对白格式与 UI 字数限制。

如果缺失信息会改变 canon、角色知识或分支结果，Skill 会先询问；其他缺口采用范围有限且明确标注的假设。

## 输出 / Output

默认交付一套最强、可直接使用的对白，而不是多个只有措辞差异的版本：

```text
1. canon 与必要假设
2. 仓库原生格式的对白
3. 触发条件与状态变化
4. voice、自然度、知识、因果、格式和 UI QA
```

只有信任度、线索状态、成功/失败或中断条件真正改变互动时才提供分支。大量生成或代码/数据接入会先检查项目 schema、调用点、保存标志和本地化约定。

## 调用 / Usage

```text
$narrative-npc-dialogue 根据这个场景、人物资料和任务状态，写一段 NPC 与玩家的可接入对白。
```

也可以用于修订和审阅：

```text
$narrative-npc-dialogue 审核这批环境对白的角色区分、知识边界、重复策略和状态一致性。
```

## 工作方式 / Workflow

1. 确定电影版本、游戏分歧、角色知识和场景前后状态。
2. 从本地项目与合法来源建立简洁 voice card，不混合不同版本 canon。
3. 先定义 `state before → conversational action → state after`，再写对白。
4. 内部比较不同会话策略，执行自然口语与删减检查，只交付最强版本。
5. 使用项目原生字符串、tuple、对象、分支、本地化和事件格式。

影视改编流程见 [film-adaptation-workflow.md](references/film-adaptation-workflow.md)，自然对话方法见 [conversation-craft.md](references/conversation-craft.md)，复杂接入见 [output-contract.md](references/output-contract.md)。

## QA 与边界 / QA and Boundaries

- 不混合院线版、导演剪辑版、重拍版、原著或游戏分支，除非用户明确授权。
- 不复制源台词，不用同义词重写电影场景，也不模仿在世作者的独特风格。
- 每个事实必须符合说话者在当前时间点的知识与确定性。
- 对白必须产生叙事、关系、气氛或游戏状态上的作用，同时符合展示预算。
- 任务、奖励、线索与分支必须记录明确状态变化，不能藏在对白字符串里。

The Skill checks continuity, character distinction, knowledge, causality, performability, UI fit, and repository integration before delivery.

## 安装与依赖 / Installation and Dependencies

本 Skill 没有第三方运行依赖。将目录复制或链接到 Codex Skills 目录，并保留文件夹名 `narrative-npc-dialogue`：

```text
$CODEX_HOME/skills/narrative-npc-dialogue
```

未设置 `CODEX_HOME` 时，常见位置为 `~/.codex/skills/narrative-npc-dialogue`。Codex 实际加载入口是 [SKILL.md](SKILL.md)。

This is a documentation-only Skill with no third-party runtime dependency.

## 隐私与版权 / Privacy and Copyright

- 不在 Skill 目录中保存用户剧本、字幕、项目对白、生成结果或研究缓存。
- 研究只补充会改变对白的缺口，并以释义证据支持决策，不收集大段版权文本。
- 《高墙之外》参考仅是基于公开开源版的可选案例，不是默认模板，也不包含电影源台词或私人开发内容。
- 用户材料、第三方作品及生成输出不会因使用本 Skill 自动采用 MIT License。

User-provided scripts, subtitles, project dialogue, and generated outputs are not bundled or automatically relicensed.

## 开发与验证 / Development and Validation

系统中存在 `skill-creator/scripts/quick_validate.py` 时，使用它验证 Skill 结构。触发与非触发边界记录在 [tests/forward-evals.yaml](tests/forward-evals.yaml)，并应在修改入口描述或工作流后重新审阅。

## 已知限制 / Known Limitations

- 只有作品名称而没有本地材料或联网授权时，不能可靠还原角色和剧情细节。
- Skill 输出文本与集成建议，不负责配音、口型、自动本地化或运行时聊天服务。
- Beta 阶段的 forward eval 用于检查边界和不变量，不代表对所有作品与语言完成自动质量证明。

## 许可 / License

本 Skill 的原创代码、文档、通用示例和测试材料采用仓库根目录的 [MIT License](../../LICENSE)。第三方角色、作品和用户材料的权利仍归其各自权利人。

Original Skill documentation, generic examples, and test material follow the repository's [MIT License](../../LICENSE). Rights in third-party works and user materials remain with their respective owners.

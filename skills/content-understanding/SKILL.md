---
name: content-understanding
description: 将剧本、字幕、小说、漫画、戏剧等线性叙事材料整理为可追溯的因果主干、精选片段与关系档案，并为每个事件节点补充忠于原叙事功能的轻量玩法提示。用于游戏改编前的内容拆解与审阅；不用于普通摘要、完整影音理解、剧情改写或完整玩法系统设计。
---

# Content Understanding Skill

把线性叙事转成面向游戏改编创作者的可追溯结构档案。产物同时保留因果主干、非主干精彩片段和轻量玩法转化提示；玩法提示是独立设计提案，不能污染原作事实或分析推断。

## 边界

- 处理用户提供或明确要求读取的剧本、字幕、小说章节、梗概、漫画、PDF、DOCX、网页文本和场景笔记。
- 只有作品名时请求材料或联网授权；未经授权不检索，也不把模型记忆当作原作材料。
- 不直接分析完整电影或音频。电影任务以字幕、剧本或场景笔记为材料，并明确标示是否核验了最终成片。
- 可以给逐节点的简短玩法提示，但不设计核心循环、数值、完整关卡、分支改写或平衡方案。
- 默认用中文分析，YAML 键使用英文；用户指定其他语言时遵从。

## 工作流

1. **材料盘点**：登记目标作品与版本、材料、来源角色、定位方式、联网授权和用户锁定片段。
2. **覆盖建账**：按章节、页段、字幕时间段或文件建立 `pending/analyzed/failed` 单元；分别判断材料覆盖和目标版本可信度。
3. **顺序提取**：按原顺序识别状态变化事件、精选片段、人物关系、关键物件/信息和未决问题。
4. **结构连接**：将事件分为 `spine/support`，建立因果边、分段、人物变化、元素流与铺垫回收。
5. **轻量玩法提示**：每个节点写玩家行动、体验目标与不可破坏的叙事结果；高价值节点才补充2–4步交互形态与压力反馈。
6. **规范化交付**：先写 `structure.yaml`，运行校验器，再由渲染器生成 `overview.md` 和 `structure.md`。

执行结构提取和玩法提示前阅读 [references/method.md](references/method.md)。生成、修订或解释字段时必须阅读 [references/schema.md](references/schema.md)。需要完整示例时阅读 [references/example.md](references/example.md)。

## 玩法提示规则

- 所有有效 `spine/support` 节点都必须有 `adaptation_hint`。
- `normal` 只写 `player_action`、`experience_goal` 和 `narrative_invariant`；其余扩展字段保持空值。
- `high` 通常至少具备两项：玩家选择、信息发现、关系冲突、时间/资源压力、风险变化、情绪峰值、独特视听或动作表现。
- `high` 额外写明提名理由、2–4步 `interaction_shape` 与 `pressure_or_feedback`，但仍不展开完整系统。
- `narrative_invariant` 必须与节点 `outcome`、`state_changes` 和因果作用一致。若建议会改变原作结果，删除或改写建议。
- 每个精选片段都有 `presentation_hint`。已由关联节点完整覆盖时填写 `covered_by_node_id`，避免重复展开。
- 玩法建议只出现在专用字段和Markdown的“轻量玩法提示”区，不得进入 `facts` 或 `inferences`。

## 输出与修订

默认写入：

```text
structured-narrative/<作品slug>/
|-- overview.md
|-- structure.md
`-- structure.yaml
```

首次分析直接交付完整草案。非修订请求遇到同名目录时创建 `-2`、`-3` 等新目录，不覆盖旧结果。

明确修订时：

- 保留现有稳定ID与锁定项；新增条目使用新ID，不批量重编号。
- 递增 `metadata.revision`，把更新后的规范数据快照写入 `revisions/r####.yaml`，并追加 `CHANGELOG.md`。
- 合并节点保留排序最早的ID，其余节点记录 `superseded_by`；拆分保留原节点为父记录，新节点获得新ID。
- 排除片段保留在YAML审计记录中，但不显示在概览推荐中。

## 确定性工具

在技能目录安装依赖后执行：

```text
python scripts/validate_structure.py <structure.yaml>
python scripts/render_structure.py <structure.yaml> --output-dir <目录>
python scripts/archive_revision.py <structure.yaml>
```

校验失败时不得交付或手写Markdown绕过。警告需要在 `review.validation_notes` 中说明或通过结构压缩解决。

## 完成检查

- 材料单元状态真实；“材料完整”没有被写成“目标成片已核验”。
- 每个事实有来源定位，每个推断单列依据与置信度。
- 主干形成可解释路径；超过12个或占节点65%以上时记录压缩理由。
- 每个节点和精选片段都有合规提示，高价值节点不超过全部有效节点40%，否则说明原因。
- 锁定、外部评价、外键、修订号和历史记录通过校验。
- 两个Markdown均由YAML渲染生成，不能分别自由发挥。


# Structure Schema 2.0

`structure.yaml` 是唯一规范数据源。`overview.md` 和 `structure.md` 必须由 `scripts/render_structure.py` 生成。完整机器约束见 [structure-v2.schema.json](structure-v2.schema.json)。

## 文件布局

```text
structured-narrative/<作品slug>/
|-- overview.md
|-- structure.md
|-- structure.yaml
|-- CHANGELOG.md          # 首次修订后出现
`-- revisions/            # 首次修订后出现
    `-- r0002.yaml
```

## 顶层字段

```yaml
schema_version: "2.0"
metadata:
  skill_version: "2.0.0-beta.1"
  generated_at: "2026-08-22T12:00:00+08:00"
  revision: 1
  generation_method: "codex-analysis+deterministic-render"
  revision_history: []
work: {}
sources: []
coverage:
  material_coverage: {}
  target_fidelity: {}
overview: {}
segments: []
nodes: []
causal_links: []
notable_fragments: []
characters: []
story_elements: []
setup_payoffs: []
gaps: []
review: {}
```

所有顶层键必须存在。YAML键使用英文，内容默认中文。

## 覆盖

```yaml
coverage:
  material_coverage:
    status: "complete | partial"
    units:
      - id: "UNIT-001"
        source_id: "SRC-001"
        label: "pages 1-20"
        status: "pending | analyzed | failed"
        notes: ""
    notes: []
  target_fidelity:
    target_medium: "film | screenplay | novel | short_story | comic | play | mixed | other"
    target_version: "目标版本说明"
    status: "verified | partial | unverified"
    basis_source_ids: ["SRC-001"]
    caveats: []
```

材料完整只表示声明单元均已分析。以剧本分析电影时，材料可以 `complete`，但目标成片必须为 `unverified` 或 `partial`。

## 节点玩法提示

每个有效节点必须有：

```yaml
adaptation_hint:
  priority: "normal | high"
  player_action: ""
  experience_goal: ""
  narrative_invariant: ""
  selection_reason: ""
  interaction_shape: []
  pressure_or_feedback: ""
```

`normal` 的后三个扩展字段必须为空；`high` 的扩展字段必须完整，且 `interaction_shape` 为2–4项。

节点可增加 `superseded_by` 和 `parent_node_id`。`superseded_by` 非空的节点是历史记录，不计入比例，也不显示为有效节点。

## 精选片段提示

```yaml
presentation_hint:
  player_involvement: ""
  experience_goal: ""
  covered_by_node_id: ""
```

若 `covered_by_node_id` 非空，必须指向 `related_node_ids` 中的有效节点。排除项保留在YAML，但不进入 `overview.md` 的推荐片段。

## 稳定ID与引用

沿用：`SRC-###`、`SEG-###`、`N-###`、`CL-###`、`NF-###`、`CHR-###`、`EL-###`、`SP-###`、`GAP-###`；分析单元使用 `UNIT-###`。初稿按出现顺序编号，`order` 使用10的间隔，修订不批量重编号。

来源引用格式：

```yaml
- source_id: "SRC-001"
  locator: "00:12:30.000 --> 00:13:08.500"
  note: "回查提示，不复制长段原文"
```

事实优先引用 `primary`。`external_reception` 必须有指向 `secondary` 来源的 `external_support_refs`。

## Markdown映射

`overview.md` 依次呈现：范围和版本可信度、故事概览、脊柱、高价值玩法候选、未排除片段、主要缺口、审阅入口。

`structure.md` 依次呈现：范围与来源、故事概览、故事脊柱、分段节点及逐节点玩法提示、精选片段及表现提示、人物、元素流、铺垫回收、缺口、审阅与验证说明。

## 修订与校验

`metadata.revision` 从1开始。每次明确修订递增，并在 `revision_history` 记录版本、时间、操作和受影响ID。合并节点保留最早ID；被合并节点写 `superseded_by`。拆分节点的新项写 `parent_node_id`。锁定片段必须出现在 `review.user_locked_fragment_ids`。

```text
python scripts/validate_structure.py path/to/structure.yaml
python scripts/render_structure.py path/to/structure.yaml --output-dir path/to/output
```

Schema错误或语义错误会阻止渲染。主干或高价值比例过高属于警告；交付前应压缩，或在对应 `review` 理由字段中解释。


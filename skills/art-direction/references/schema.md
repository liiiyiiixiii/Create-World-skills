# Art Direction Schema 1.0（生产规范兼容接口）

`art-direction.yaml` 是规范源，`art-direction.md` 必须由渲染器生成。字段细节由 [art-direction-v1.schema.json](art-direction-v1.schema.json) 强制校验。

该接口继续用于完整 Art Bible，不承担视觉候选盲测。新项目默认先使用 [visual-decision-schema.md](visual-decision-schema.md)；这里的 `approved` 不等于 `player_supported`。

## 顶层结构

```text
schema_version
metadata
project
sources
observations
constraints
territories
selection
style_kernel
translation_rules
visual_system
asset_families
prompt_capsule
pilot_plan
qa
review
```

## ID

- 来源：`SRC-001`
- 观察：`OBS-001`
- 候选方向：`T-001`
- 支柱：`P-001`
- 转译规则：`TR-001`
- 资产族：`AF-001`
- Pilot：`PT-001`
- QA：`QA-001`

同一文件内所有 ID 唯一。修订时保留稳定 ID，不因排序变化批量重编号。

## 证据与观察

`sources[].evidence_status`：

- `verified`：直接审阅了目标材料；
- `partial`：只覆盖部分章节、镜头、图片或项目文件；
- `unverified`：只有梗概、二手描述或待确认信息。

`observations` 只存可观察现象。每项至少一个 `source_ref`：

```yaml
- id: OBS-001
  category: lighting
  statement: "多数室内镜头处于低明度，出口场景出现暖色边缘光。"
  confidence: high
  source_refs:
    - source_id: SRC-001
      locator: "00:42:10–00:44:03"
```

不要在 `statement` 中写“所以游戏应该……”，游戏规则写入 `translation_rules` 或 `visual_system`。

## Territories 与 selection

`territories` 允许 1–3 项。方向开放时使用 3 项；用户已锁定时允许 1 项。每项五个 1–5 分评分，`status` 中恰好一个为 `selected`。

`selection.selected_territory_id`、`style_kernel.selected_territory_id` 和该 `selected` territory 必须一致。若选择不是总分最高项，校验器会警告，`selection.selection_rationale` 应解释关键取舍。

## Style kernel

- `direction_sentence`：一句能约束画面的总方向；
- `emotional_contract`：常态情绪与允许突破的时刻；
- `pillars`：3–5 项，每项含规则和 proof；
- `anti_pillars`：2–5 项；
- `identity_tokens`：5–12 个跨资产重复 token。

## Translation rules

每项把来源线索连接到叙事功能和游戏规则：

```yaml
- id: TR-001
  source_cue: "狭窄门框和暗角反复包围人物"
  narrative_function: "持续制造被制度包围的感受"
  treatment: abstract
  game_rule: "房间外围保持深色墙体与暗角，但交互路径至少高出背景一个明度层级。"
  source_observation_ids: [OBS-002]
  asset_family_ids: [AF-001, AF-003]
```

`treatment`：`retain`、`abstract`、`replace`。每条规则至少关联一个观察和一个资产族。

## Pixel policy

`visual_system.pixel_policy.mode`：`strict_pixel`、`hybrid_pixel`、`pixel_influenced`、`non_pixel_2d`。

- `strict_pixel` 必须使用 `nearest_neighbor` 和 `integer_only`。
- `hybrid_pixel` 必须在 `exception_rules` 说明哪些资产族允许脱离严格网格。
- `native_canvas` 写参考画布或资产基准，例如 `320x180 gameplay base; 48x64 character cell`。

## Palette

每个颜色含唯一 `name`、`hex`、`role` 和 `usage`。`role` 可为：

`background`、`shadow`、`midtone`、`highlight`、`accent`、`ui_text`、`semantic`、`custom`。

至少 5 色，并至少包含一个 `accent` 和一个 `ui_text`。这里记录的是角色色，不要求所有资产只使用这几种 RGB；若为严格受限调色板，应在 `strategy` 明确。

## Asset families

每个资产族都必须写：

- `function` 和 `visual_mode`；
- `camera`、`native_spec`、`scale_rule`；
- `palette_rule`、`shape_rule`、`lighting_rule`、`detail_budget`；
- `motion_rule` 和 `readability_test`；
- `do` / `avoid`。

至少 3 个资产族。`visual_mode` 不必全部相同；它们通过 `style_kernel.identity_tokens` 和 visual system 统一。

## Pilot 与 QA

`pilot_plan.tests` 至少 3 项。每项只验证一个明确假设，并列出至少两个通过条件。Pilot 没有生成时 `generation_status` 使用 `not_requested` 或 `planned`，不要伪写 `completed`。

`qa.gates` 至少 6 项，并至少覆盖：

- `readability`
- `consistency`
- `technical`

其他类别可用 `source_fidelity`、`production`、`accessibility`、`rights`、`motion`。`review.approval_status` 为 `draft`、`provisional` 或 `approved`。

## 修订

`metadata.revision` 从 1 开始。用户明确锁定的字段路径写入 `review.locked_fields`，例如：

```yaml
review:
  locked_fields:
    - style_kernel.direction_sentence
    - visual_system.pixel_policy.mode
```

警告的解释或暂不处理原因写入 `review.validation_notes`。

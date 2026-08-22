# Visual Decision 1.0 接口

`visual-decision.yaml` 是视觉选型记录源。字段由 [visual-decision-v1.schema.json](visual-decision-v1.schema.json) 强制校验；玩家分析与风格契约分别由 [player-analysis-v1.schema.json](player-analysis-v1.schema.json) 和 [style-contract-v1.schema.json](style-contract-v1.schema.json) 校验。

## 顶层结构

```text
schema_version
metadata
status
decision_brief
source_functions
benchmark
candidates
craft_gates
player_tests
recommendation
creator_decision
provenance
```

可运行示例见 `tests/fixtures/visual-decision/visual-decision.yaml`。它的 SVG 只用于测试数据链，不是推荐风格或生产样板。

## 关键不变量

- 正式流程固定 `C-A`、`C-B`、`C-C` 三套候选和盲测 ID A/B/C。
- 三套必须引用同一个 benchmark，覆盖 `gameplay_scene`、`native_character`、`ui_hud`、`narrative_frame`。
- `generation_attempts` 不得超过 2；第二轮最多修订两个候选。
- 每个候选分别有且只有一项 `source_function`、`craft`、`readability`、`technical`、`production` 门槛。
- 路径必须相对且不能包含 `..`；样板登记 SHA-256，`--check-files` 会检查文件与哈希一致。
- `test_ready` 要求三套全部通过门槛；后续形成比较结论时至少两个候选仍合格。
- 最多两轮玩家测试；每轮阈值固定为至少 8 份、推荐不超过 12 份有效答卷。
- `player_supported` 必须与确定性分析的玩家领先者及创作者接受记录一致。
- `creator_override` 必须选择非玩家领先者并填写理由。

## 匿名答卷

离线页面每位参与者导出一个 JSON，包含：Schema/test ID、匿名参与者 ID、候选呈现顺序、目标玩家与注意力检查结果、完整排序，以及三套候选各自的 1–7 评分、三项可读性答案和开放反馈。

分析器拒绝其他 test ID、无效评分、不完整/重复排序、非目标玩家、注意力失败和重复匿名 ID。测试页不嵌入正确答案，正确答案只保留在决策源中供分析器使用。

## 统一 CLI

```text
python scripts/visual_decision.py validate visual-decision.yaml --check-files
python scripts/visual_decision.py build-test visual-decision.yaml --test-id TEST-001 --output-dir player-test
python scripts/visual_decision.py analyze visual-decision.yaml --test-id TEST-001 --responses-dir player-test/responses --output player-analysis.json
python scripts/visual_decision.py render visual-decision.yaml --analysis player-analysis.json --output-dir .
python scripts/visual_decision.py export-contract visual-decision.yaml --analysis player-analysis.json --output style-contract.yaml
```

`analyze` 不修改决策源。分析完成后，根据 `player-analysis.json` 更新 `recommendation`、`creator_decision`、玩家测试路径和顶层状态，再校验、渲染和导出契约。这样真实反馈与创作者裁决不会被分析脚本混写。

`creator_selected_unvalidated` 可以在没有玩家分析时导出契约；`player_supported` 与 `creator_override` 导出时必须同时提供支持它们的分析文件。

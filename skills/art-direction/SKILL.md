---
name: art-direction
description: 帮助缺少专职美术总监的独立游戏创作者，把电影、剧本、小说、漫画或现有项目转成三套公平可比的 2D 视觉候选，并通过制作质量门槛和真实目标玩家盲测完成可追溯选型。用于改编前确定或修订整体视觉方向；不用于普通图片风格点评、单角色设计、批量资产生产或 3D 美术。
---

# Art Direction

核心任务是帮助创作者做出可信的整体视觉选择，而不是先生成一份很长的 Art Bible。默认交付可见候选、真实玩家证据、决策报告和紧凑 style contract。

## 模式

- **视觉决策（默认）**：方向尚未锁定，或用户希望比较、验证、选择整体风格。阅读 [references/decision-method.md](references/decision-method.md) 与 [references/visual-decision-schema.md](references/visual-decision-schema.md)。
- **生产规范（显式可选）**：用户已有明确方向并要求完整 Art Bible，或需要维护现有 `art-direction.yaml`。此时阅读 [references/method.md](references/method.md) 与 [references/schema.md](references/schema.md)，使用原有 v1 校验器和渲染器。
- 需要了解本方法如何从真实游戏项目提炼时，再阅读 [references/beyond-walls-case-study.md](references/beyond-walls-case-study.md)。案例不是默认风格模板。

不要因为用户只给出一个风格词，就自动进入生产规范模式。方向未被可见证据证明时，先走视觉决策。

## 默认工作流

1. **建立决策简报**：登记目标玩家、平台与原生分辨率、镜头、玩法可读性目标、产能、创作者偏好和红线。提取原作必须保留的情绪、人物/权力关系和叙事功能，并附可定位来源。缺失项写入 `assumptions`；存在未决假设时不得标记玩家支持。
2. **锁定同题 benchmark**：固定一套内容、构图、画幅和四类面板：代表性玩法场景、原生尺寸角色、UI/HUD、关键叙事镜头。为主角、出口和可交互物定义三项五秒可读性题。
3. **提出三套视觉假设**：A/B/C 必须在表现制度或视觉语法上真正不同。不要给候选做主观总分，也不要先选赢家。
4. **制作综合样板**：优先使用内置图像生成；也接受用户自制样板。三套使用相同 benchmark、尺寸、信息量和生成成本，只改变视觉假设。每套最多两次生成尝试，第二次只能修复可描述的生成硬伤。记录相对路径与 SHA-256；没有实际样板不能进入测试。
5. **执行工艺硬门槛**：在原生尺寸及放大检查下，分别记录 `source_function`、`craft`、`readability`、`technical`、`production` 的 pass/fail/pending、检查方法和可见证据。`test_ready` 要求三套候选全部通过；不得用“整体感觉不错”代替证据。
6. **生成离线盲测页**：先校验 `visual-decision.yaml`，再运行统一 CLI 的 `build-test`。页面必须随机顺序、隐藏候选名称、不联网、不收集姓名/邮箱，并导出单个匿名 JSON 答卷。
7. **等待真实反馈**：把测试页交给创作者招募的目标玩家。不得模拟、编造、复制或补齐玩家答卷；少于 8 份有效答卷只能得到 `tested_inconclusive`。
8. **确定性分析**：用 CLI 的 `analyze` 读取答卷。只在至少两个候选通过全部工艺门槛和 75% 玩家可读性、且领先候选对每个合格对手达到 60% 两两偏好、吸引力中位数达到 5/7 时，给出 `player_leader`。
9. **处理不确定性**：首轮不明确时，依据门槛和原始反馈最多修订两个候选并重新盲测一次。第二轮要形成 `player_supported` 必须使用新参与者；复用参与者仅作参考。第二轮仍不明确时，由创作者选择并标记 `creator_selected_unvalidated`。
10. **创作者裁决与交付**：接受玩家领先者标记 `player_supported`；选择其他候选标记 `creator_override` 并保留理由。随后确定性渲染 `decision-report.md` 并导出 `style-contract.yaml`。只有用户明确要求，才继续生成完整 v1 Art Bible。

## 视觉样板规则

- 从来源材料提取可描述的色彩、明度、构图、材质、轮廓和节奏规律；不复制具体镜头、标志、演员肖像或某位在世艺术家的独特风格。
- 用户材料是内容与空间证据；同题 benchmark 控制内容、构图和信息密度；候选 prompt 只控制视觉制度。
- 图像生成出现缺面板、内容错位、明显肢体/文字伪影、尺寸或采样错误时，可进行一次定向重试。偏好不构成重试理由。
- 每张样板同时展示四类资产，不能用三张漂亮海报代替跨资产一致性 proof。

## 输出与命令

```text
art-direction/<项目-slug>/
|-- visual-decision.yaml
|-- candidates/
|   |-- candidate-A.png
|   |-- candidate-B.png
|   `-- candidate-C.png
|-- player-test/
|   |-- index.html
|   `-- responses/
|-- player-analysis.json
|-- decision-report.md
|-- style-contract.yaml
|-- art-direction.yaml       # 仅显式要求完整 Art Bible 时
`-- art-direction.md         # 仅显式要求完整 Art Bible 时
```

```text
python scripts/visual_decision.py validate <visual-decision.yaml> --check-files
python scripts/visual_decision.py build-test <visual-decision.yaml> --test-id <TEST-ID> --output-dir <player-test>
python scripts/visual_decision.py analyze <visual-decision.yaml> --test-id <TEST-ID> --responses-dir <responses> --output <player-analysis.json>
python scripts/visual_decision.py render <visual-decision.yaml> --analysis <player-analysis.json> --output-dir <目录>
python scripts/visual_decision.py export-contract <visual-decision.yaml> --analysis <player-analysis.json> --output <style-contract.yaml>
```

同名项目目录已存在且用户没有明确要求修订时，创建带递增后缀的新目录，不覆盖旧证据。修订时保留项目 slug 和稳定 ID，递增 revision，并保存旧测试轮次。

## 证据边界

- “美观”只表示候选通过制作质量硬门槛，并获得目标玩家的主观吸引力证据；不要声称绝对美感。
- 8–12 人是方向性小样本，不代表统计性市场结论、销量或商业成功概率。
- 玩家招募、画像真实性和知情同意由创作者负责；测试页面只做本地匿名收集。
- v1 `art-direction.yaml` 中的 `approved` 只表示生产规范获批，不等于 `player_supported`。

## 完成检查

- 三套候选共享 benchmark、四面板、尺寸、信息量和尝试上限，只改变视觉假设。
- 原作叙事功能是硬门槛；工艺检查逐候选有可见证据，没有主观总分。
- 玩家结果来自真实匿名答卷，分析产物可由相同输入确定性复现。
- 推荐、创作者最终选择和 override 理由没有混写；证据不足时状态诚实。
- style contract 只在创作者完成选型后导出，使用相对路径和来源哈希。

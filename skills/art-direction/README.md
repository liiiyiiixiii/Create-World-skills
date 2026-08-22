# Art Direction Skill

[← 返回 Create World Skills 总目录](../../README.md)

**状态：Beta / Status: Beta**

**叙事材料 + 游戏约束 → 三套可见候选 + 真实玩家证据 + 可追溯视觉选择。**

这个 Skill 面向没有专职美术总监的独立游戏创作者。它把“好看”拆成制作质量门槛与目标玩家吸引力：先用同题综合样板证明方向能落地，再用离线匿名盲测判断玩家偏好，最后由创作者裁决并导出机器可读的 style contract。

它源自《高墙之外》把电影气质转成 2D 像素游戏的实践，但不会把监狱题材、黑金配色或 Q 版角色变成其他项目的默认答案。

## 适用与边界

适合：

- 将电影、剧本、小说、漫画等叙事材料改编为 2D 游戏；
- 在正式制作前比较三个真正不同的整体视觉方向；
- 用真实目标玩家反馈检验吸引力、叙事契合和玩法可读性；
- 记录创作者为什么接受或覆盖玩家建议；
- 为后续角色、场景、UI 和图像生成流程导出紧凑风格契约。

不适合普通图片风格点评、单角色设计、批量最终资产、3D 建模/绑定或商业销量预测。Skill 不招募玩家，也不会模拟或补齐玩家反馈。

## 默认流程

```text
决策简报与原作叙事功能
              ↓
固定同题 benchmark
              ↓
三套 A/B/C 跨资产综合样板
              ↓
原作 / 工艺 / 可读性 / 技术 / 生产硬门槛
              ↓
离线匿名盲测（至少 8 份有效目标玩家答卷）
              ↓
Borda + 两两偏好 + 评分中位数 + 可读性正确率
              ↓
证据建议，创作者最终裁决
              ↓
decision-report.md + style-contract.yaml
```

没有实际样板不能进入玩家测试；没有真实有效答卷不能标记 `player_supported`。首轮无明确结果时最多修订两个候选并复测一次。

## 关键阈值

- 三套候选使用相同内容、构图、尺寸、面板和最多两次生成尝试；
- `test_ready` 前三套均须通过五类制作质量门槛；
- 玩家可读性至少 75%；
- 至少 8 份有效答卷，推荐 8–12 份；
- 玩家领先者对每个合格对手的两两偏好率至少 60%；
- 玩家领先者的视觉吸引力中位数至少 5/7；
- 第二轮要形成玩家支持，必须使用新的参与者。

这些阈值提供方向性证据，不构成统计性市场结论。

## 默认产物

```text
art-direction/<project-slug>/
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
`-- style-contract.yaml
```

`visual-decision.yaml` 是决策记录源。字段说明见 [references/visual-decision-schema.md](references/visual-decision-schema.md)，方法见 [references/decision-method.md](references/decision-method.md)。完整可运行 fixture 位于 `tests/fixtures/visual-decision/`。

`style-contract.yaml` 只在创作者完成选型后导出，并保留三种证据状态：

- `player_supported`：玩家领先者达到阈值且创作者接受；
- `creator_selected_unvalidated`：证据不足，由创作者自行选择；
- `creator_override`：存在玩家领先者，但创作者选择另一方向并记录理由。

## 调用

```text
$art-direction 根据这些剧本、项目截图和移动端约束，制作三套公平可比的整体视觉候选，并准备目标玩家盲测。
```

当用户已经完成选型并明确要求完整生产规范时，Skill 才进入兼容的 Art Bible 模式：

```text
$art-direction 使用已选 style-contract.yaml 展开完整 Art Bible。
```

旧版 `art-direction.yaml` 与 `art-direction.md` 仍受支持。v1 中的 `approved` 只表示生产规范获批，不等于经过玩家验证。

## 安装与命令

```shell
python -m pip install -r skills/art-direction/requirements.txt
```

将 `art-direction` 文件夹复制或链接到 `$CODEX_HOME/skills/art-direction`。未设置 `CODEX_HOME` 时，常见位置为 `~/.codex/skills/art-direction`。

统一视觉决策 CLI：

```shell
python skills/art-direction/scripts/visual_decision.py validate path/to/visual-decision.yaml --check-files
python skills/art-direction/scripts/visual_decision.py build-test path/to/visual-decision.yaml --test-id TEST-001 --output-dir path/to/player-test
python skills/art-direction/scripts/visual_decision.py analyze path/to/visual-decision.yaml --test-id TEST-001 --responses-dir path/to/responses --output path/to/player-analysis.json
python skills/art-direction/scripts/visual_decision.py render path/to/visual-decision.yaml --analysis path/to/player-analysis.json --output-dir path/to/output
python skills/art-direction/scripts/visual_decision.py export-contract path/to/visual-decision.yaml --analysis path/to/player-analysis.json --output path/to/style-contract.yaml
```

兼容的 v1 Art Bible 命令：

```shell
python skills/art-direction/scripts/validate_art_direction.py path/to/art-direction.yaml
python skills/art-direction/scripts/render_art_direction.py path/to/art-direction.yaml --output-dir path/to/output
```

测试：

```shell
python -m unittest discover -s skills/art-direction/tests -p "test_*.py" -v
```

## 已知限制 / Known Limitations

- 真实玩家招募、画像核实与知情同意需要由创作者完成；Skill 不会生成或补齐答卷。
- 8–12 人的小样本只能提供方向性证据，不能预测销量或市场成功。
- 图像候选生成具有非确定性；确定性脚本只保证校验、盲测打包、分析与报告可复现。
- 本 Skill 决定整体方向，不负责批量制作最终角色、场景、UI 或 3D 资产。

Real-player recruitment remains the creator's responsibility. Small-sample results are directional rather than market predictions, generated candidates remain nondeterministic, and final asset production is outside this Skill's scope.

## 隐私与版权

- 离线测试页不联网，只生成匿名 JSON；招募、画像核实和知情同意由创作者负责。
- 用户提供的原作、截图和项目素材不会因使用本 Skill 自动采用本仓库许可证。
- 公开仓库不打包用户原始材料、电影帧、演员肖像或无权再分发的参考图。
- 候选提取可描述的构图、色值、材质、轮廓和节奏规律，不复制具体帧、标志或在世艺术家的独特风格。

---

## English summary

Art Direction helps independent game creators compare three equal-cost, cross-asset 2D visual candidates, screen them through observable craft gates, and test them with real target players in an offline randomized survey. It produces reproducible evidence, a creator-owned final decision, and a compact machine-readable style contract. The legacy production Art Bible remains available only when explicitly requested.

## 许可 / License

本 Skill 的代码、文档、原创测试夹具和程序化候选素材采用仓库根目录的 [MIT License](../../LICENSE)。用户材料、第三方作品及基于其生成的输出不会因使用本 Skill 自动转为 MIT。

The Skill's code, documentation, original fixtures, and programmatic candidate assets follow the repository's [MIT License](../../LICENSE). User materials, third-party works, and derived outputs are not automatically relicensed.

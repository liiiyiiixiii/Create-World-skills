# Scene Generation Skill / 可玩场景生成 Skill

[← 返回 Create World Skills 总目录](../../README.md)

**状态：可用 / Status: Available**

`$scene-generation` 把影视截图、现实空间、场景名称或文字描述，转译成一个可游玩的俯视 2D 游戏场景，并交付与画面严格对齐的碰撞数据。它解决的是单个空间从“看起来像场景”到“可以走、可以碰撞”的转换，不负责制定整体美术方向、生成角色、设计完整关卡机制、拆分瓦片或接入游戏引擎。

`$scene-generation` turns a film still, real place, location name, or written brief into a playable top-down 2D scene with aligned collision geometry and deterministic QA. It creates an engine-neutral scene pack and does not modify the host game.

## 输入与输出

输入可以是文字、场景名称、一张或多张空间参考图，以及可选的入口、出口、关键地标、交互站位、画幅、玩家尺度和 `art-direction.yaml`。只有名称时会给出保守的解释性布局；精确还原应提供可定位的视觉材料。

正式交付固定为四个文件：

```text
output/scene-generation/<scene-id>/
|-- scene.png
|-- collision-overlay.png
|-- collision.json
`-- qa-report.json
```

`layout-guide.png` 仅作为暂存输入。碰撞图不由图像模型重画，而是从最终几何确定性叠加，因此两张 PNG 尺寸一致，未标注区域逐像素保持不变。

## 生成模式

| 模式 | 行为 | 图像调用上限 |
|---|---|---:|
| `fast` | 一次生成，不重试 | 1 |
| `balanced` | 默认；只在硬性空间失败时定向重试一次 | 2 |
| `quality` | 可做一次风格或细节修订 | 2 |

正常的 `balanced` 运行只生成一次。错误投影、缺失必需地标、入口堵塞、空间断裂、画面裁切或意外角色/UI 才触发重试；小范围画面漂移只修正碰撞几何。

## 工作方式

1. 先定义入口、出口、可行走多边形、实体障碍和交互站位。
2. 校验 `collision.json`，并从同一几何生成中性的 `layout-guide.png`。
3. 只生成干净场景；布局引导控制几何，用户素材控制空间证据，Art Direction 控制风格。
4. 接受场景后，从最终几何生成红色覆盖图和 QA 报告。

风格优先级为：用户明确要求的单场景偏离 > 已提供且批准的 `art-direction.yaml` > 内置精简默认规则。已有 Art Direction 时，参考照片不会自动成为风格参考。

```text
$scene-generation 一间老旧监狱图书馆，南侧入口，两排书架，中间登记桌，保留可绕行通路
```

## 确定性工具

只依赖 Pillow：

```shell
python -m pip install -r skills/scene-generation/requirements.txt
```

将 `scene-generation` 目录复制或链接到 Codex Skills 目录，并保持文件夹名不变：

```text
$CODEX_HOME/skills/scene-generation
```

未设置 `CODEX_HOME` 时，常见位置为 `~/.codex/skills/scene-generation`。

```shell
python skills/scene-generation/scripts/scene_collision.py validate --spec collision.json
python skills/scene-generation/scripts/scene_collision.py guide --spec collision.json --output layout-guide.png
python skills/scene-generation/scripts/scene_collision.py render --scene scene.png --spec collision.json --output collision-overlay.png --report qa-report.json
```

普通单房间或院落直接使用 Skill 主说明即可；多区域、复杂多边形障碍、特殊通道或校验失败时再读 [碰撞几何规范](references/collision-spec.md)，复杂影视透视转译时再读 [设计工作流](references/design-workflow.md)。

## 边界

- 默认方形、近正交俯视、脚点碰撞；其他画幅使用同比例坐标空间。
- 场景图不烘焙角色、NPC、UI、文字、红线或调试标记。
- 输出是引擎无关的空间资产与脚点几何，不等于任何引擎的完整物理配置。
- 用户素材与生成结果不会因使用本仓库而自动采用仓库许可证。

## QA 与失败条件 / QA and Failure Conditions

- `collision.json` 必须通过几何、锚点、连通性、生成模式和图像调用次数校验。
- `collision-overlay.png` 必须与 `scene.png` 尺寸一致，且只允许增加规范指定的红色边界像素。
- 入口堵塞、必需地标缺失、空间断裂、错误投影、画面裁切或意外角色/UI 属于硬失败。
- 无法可靠确定拓扑时停止并请求更明确材料，不用隐形墙或强行推断掩盖问题。

The pack is accepted only when geometry, reachability, dimensions, overlay alignment, and generation-call limits pass deterministic validation.

## 隐私与公开参考素材 / Privacy and Public Reference Assets

- 用户参考图不会写入公开 Skill 或默认复制到正式资产包。
- 两张随附参考板由 `scripts/generate_reference_assets.py` 使用 Pillow 确定性绘制，不读取电影帧、真人照片、私有游戏资产或网络资源。
- 匿名 courtyard 测试夹具只验证几何和碰撞规则，不复刻《高墙之外》的地图或命名。
- JSON 与报告使用相对素材关系，不要求记录用户材料的绝对路径。

The bundled boards and fixtures are anonymous, deterministic, and independent of private project assets.

## 开发与测试 / Development and Tests

```shell
python -m unittest discover -s skills/scene-generation/tests -p "test_*.py" -v
python skills/scene-generation/scripts/generate_reference_assets.py --output-dir <temporary-directory>
```

系统中存在 `skill-creator/scripts/quick_validate.py` 时，使用它验证 Skill 结构。碰撞字段见[碰撞几何规范](references/collision-spec.md)，复杂转译规则见[设计工作流](references/design-workflow.md)。

## 已知限制 / Known Limitations

- 默认是近正交俯视单场景，不生成完整关卡流程、瓦片集或引擎物理配置。
- 图像生成具有非确定性；脚点几何、覆盖图和 QA 是确定性的。
- 只有名称或短描述时只能生成解释性布局，不能宣称精确复原现实或影视空间。

The Skill targets one top-down space at a time. Image generation remains nondeterministic, and sparse briefs produce interpretive rather than exact layouts.

## 许可 / License

本 Skill 的代码、文档、匿名程序化参考素材和原创测试夹具采用仓库根目录的 [MIT License](../../LICENSE)。用户材料、第三方作品及其生成输出不自动纳入该许可。

The Skill's code, documentation, anonymous programmatic assets, and original fixtures follow the repository's [MIT License](../../LICENSE). User and third-party materials are not automatically relicensed.

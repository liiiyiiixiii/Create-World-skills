---
name: scene-generation
description: 将影视截图、现实空间、场景名称或文字描述转译成可游玩的俯视 2D 游戏场景，并交付严格对齐的红色碰撞图、碰撞几何和 QA。用于单个游戏空间的场景化改编；不用于制定整体美术方向、角色生成、完整关卡机制、瓦片拆分或引擎接入。
---

# Scene Generation

把一个场景重构成一张能走、能碰撞、能继续接入游戏的俯视 2D 空间。默认创建独立资产包，不修改游戏工程。

## 输入、模式与输出

- 接受影视/现实空间参考图、场景名称或描述，以及可选地标、入口、出口、交互点、画幅、玩家尺寸、`art-direction.yaml` 和 `generation_mode`。
- `generation_mode` 默认为 `balanced`：`fast` 只生成一次且不重试；`balanced` 只在硬性空间失败时定向重试一次；`quality` 可做一次风格或细节修订。任何模式都不得超过两次图像调用。
- 只有场景名称时做保守推断，并把结果称为“解释性布局”；需要精确还原时要求用户提供可定位的视觉材料。
- 默认方形、近正交俯视、脚点碰撞、连续主通路、无角色/NPC、无 UI、无文字。

正式目录只包含：

```text
scene.png
collision-overlay.png
collision.json
qa-report.json
```

中间 `layout-guide.png` 写入交付目录外的暂存位置。不得让图像模型重画碰撞版本。

## 风格优先级

1. 用户明确要求的单场景偏离；若与既有方向冲突，说明偏离。
2. 用户提供或当前项目中唯一明确、已批准的 `art-direction.yaml`；只读取视觉内核、像素制度和可玩环境资产族，不自动创建或修改 Art Direction。
3. 精简默认：近正交俯视、完整空间轮廓、清晰地面网络、硬边 2D 像素/混合像素处理、材质主导的克制色彩。

参考照片默认控制场景内容、地标和空间证据；已有 Art Direction 时，不自动把照片本身当成风格参考。

## 几何优先流程

1. 先写简短场景 brief：空间功能、地标、出入口、交互站位、主路线、玩家尺度和画幅。只有缺失信息会改变拓扑时才询问。
2. 在生成美术前写 `collision.json` v1：`coordinate_space`、`collision_model: footpoint`、可选 `metadata`、`walkable[].points`、`obstacles`（`rect`/`circle`/`polygon`）和 `anchors`（`spawn`/`exit`/`interaction`）。普通单房间或院落直接使用这些字段；多区域、复杂多边形、特殊通道或校验失败时才读取 [references/collision-spec.md](references/collision-spec.md)。
3. 先运行 `validate`，再运行 `guide`：

   ```text
   python scripts/scene_collision.py validate --spec collision.json
   python scripts/scene_collision.py guide --spec collision.json --output layout-guide.png
   ```

4. 使用 built-in `image_gen` 只生成干净场景。布局引导控制几何，用户参考控制空间证据，Art Direction 控制风格。复杂影视透视转译或需要提示词细则时才读取 [references/design-workflow.md](references/design-workflow.md)。
5. 检查投影、完整空间、必需地标、门洞、路线和意外角色/UI。小范围画面漂移只调整碰撞几何，不重生成；错误投影、缺失地标、入口堵塞、空间断裂、画面裁切或意外角色/UI 才属于硬失败。
6. 将接受的图保存为 `scene.png`，在 `collision.json.metadata` 记录场景 ID、模式、输入类型、图像调用次数和 Art Direction ID，再确定性生成覆盖图与报告：

   ```text
   python scripts/scene_collision.py render --scene scene.png --spec collision.json --output collision-overlay.png --report qa-report.json
   ```

7. 交付前查看两张图，确认红线贴合可见地面接触面、门洞保持开放、锚点可达、非红线像素未改变。

## 不变量

- 两张 PNG 尺寸一致；`collision-overlay.png` 只能在 `scene.png` 上增加指定红线。
- 障碍沿物体的地面接触面标注，不沿高处轮廓；交互触发区不等于实体碰撞。
- 不为了简化 JSON 添加与画面矛盾的隐形墙。
- 不把脚点碰撞直接宣称为其他引擎的完整物理数据。
- 不覆盖已有资产包；创建 `-v2`、`-v3` 等新目录。

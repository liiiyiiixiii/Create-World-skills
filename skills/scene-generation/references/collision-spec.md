# Collision Geometry Contract

仅在多区域、复杂多边形障碍、特殊通道或校验失败时读取本页。`collision.json` 是布局引导与红色覆盖图的共同几何源，坐标对应最终干净场景，不对应原始照片、提示词或引擎视口。

## Version 1

```json
{
  "version": 1,
  "coordinate_space": { "width": 1024, "height": 1024 },
  "collision_model": "footpoint",
  "player_footprint": { "width": 48, "height": 64, "foot_inset": 8 },
  "metadata": {
    "scene_id": "library-room",
    "generation_mode": "balanced",
    "input_type": "reference-image",
    "image_generation_calls": 1,
    "art_direction_id": "beyond-walls-v1"
  },
  "walkable": [
    {
      "id": "main-floor",
      "points": [[96, 128], [928, 128], [928, 896], [608, 896], [608, 976], [416, 976], [416, 896], [96, 896]]
    }
  ],
  "obstacles": [
    { "id": "desk", "shape": "rect", "x": 336, "y": 352, "width": 352, "height": 176 },
    { "id": "plant", "shape": "circle", "cx": 824, "cy": 280, "radius": 44 },
    { "id": "shelf", "shape": "polygon", "points": [[760, 576], [904, 560], [912, 792], [768, 808]] }
  ],
  "anchors": [
    { "id": "spawn", "kind": "spawn", "x": 512, "y": 920 },
    { "id": "door", "kind": "exit", "x": 512, "y": 952 },
    { "id": "desk-front", "kind": "interaction", "x": 512, "y": 576 }
  ]
}
```

`metadata` 可选且向后兼容；只保存 ID 与运行事实，不保存用户素材或绝对路径。允许字段为 `scene_id`、`generation_mode`（`fast|balanced|quality`）、`input_type`（`reference-image|description|name|mixed`）、`image_generation_calls`（0–2）和 `art_direction_id`。

## 几何语义

- `walkable`：合法玩家脚点区域。入口必须由多边形中的真实开口或外伸通道表达。
- `obstacles`：从可行走区域扣除的地面接触占地，支持 `rect`、`circle` 和 `polygon`。
- `anchors`：必须在可行走区域且相互可达的测试点。交互锚点是玩家站位，不是道具中心。
- `player_footprint`：设计净宽使用的元数据；确定性连通性检查采用脚点模型。
- 坐标原点在左上，`x` 向右、`y` 向下。

矩形使用 `x/y/width/height`，圆形使用 `cx/cy/radius`，多边形点可写为 `[x, y]` 或 `{ "x": ..., "y": ... }`。

## 作者规则

- 先验证几何，再生成美术。
- 沿桌腿、树干、床架等地面接触面标注；悬空或外挑轮廓默认不扩大障碍。
- 把门、门洞、楼梯、隧道和地图过渡保留为真实可通行缺口。
- 优先使用少量忠实多边形，不为了简化 JSON 抹掉窄通道或增加隐形墙。
- 交互触发区只有在物理上实体时才进入碰撞。
- 接受后的画面若有轻微漂移，修正本文件并重新校验；不要手改覆盖图。

## 命令与报告

```shell
python scripts/scene_collision.py validate --spec collision.json --scene scene.png --report qa-report.json
python scripts/scene_collision.py guide --spec collision.json --output layout-guide.png
python scripts/scene_collision.py render --scene scene.png --spec collision.json --output collision-overlay.png --report qa-report.json
```

引导图固定使用黑色外部、浅色可行走地面、深色障碍和中性色边缘，不含红线、文字、角色或调试标记。渲染器仅在场景与坐标空间比例一致时缩放；完全相同尺寸最稳妥。

最终 `qa-report.json` 记录：验证结果与警告、模式/输入类型/调用次数/Art Direction ID、可行走区域/障碍/锚点统计、场景图与碰撞图尺寸是否一致、变化像素是否全部为指定红色，以及未标注像素是否保持不变。正式交付不得依赖 `--allow-invalid`。

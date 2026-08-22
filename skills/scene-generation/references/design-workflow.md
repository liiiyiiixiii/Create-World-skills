# Complex Scene Translation Notes

仅在影视截图透视复杂、空间关系需要重建或一次生成出现硬性空间失败时读取本页。普通单房间、院落和文字场景无需加载。

## 三类输入各自负责什么

- `collision.json` 与其中性引导图负责入口、可行走地面、障碍占地和整体拓扑。
- 用户图片负责场景身份、地标、材质证据和可推断的空间关系；它不是自动风格参考。
- 已批准的 `art-direction.yaml` 负责视觉内核、像素制度、色彩和可玩环境规则。

若没有 Art Direction，使用精简默认规则：完整可玩轮廓、近正交俯视、清晰地面网络、硬边 2D 像素或混合像素处理、材质主导的克制色彩。匿名参考板只用于文档示例，不是运行时输入。

## 从电影镜头重建空间

保留原镜头中可验证的地标关系与叙事功能，但可以校正透视、补全被遮挡地面、拉宽玩家通道并把散乱道具归并为清晰的障碍岛。不要把单一镜头的深透视、前景遮挡或戏剧性裁切直接复制成地图。

先明确：

1. 哪些入口、出口和交互站位必须互通；
2. 哪些地标必须出现且只能出现一次；
3. 哪些物体接触地面并形成实体障碍；
4. 普通通道与特殊窄道允许的最小玩家净宽；
5. 是否必须在一个画面中看见完整空间。

## 图像提示词骨架

按实际输入删减，不要堆叠无关风格词。

```text
Asset: one clean playable top-down 2D game environment, no characters or interface
Geometry authority: follow the supplied neutral layout guide for the complete footprint, open entrances, connected floor and obstacle positions
Scene evidence: preserve [required landmarks/materials/relationships] from the user reference or description
Art direction: follow [approved art-direction rules / compact default rules]; do not infer style from the reference photo unless explicitly requested
Projection: near-orthographic overhead view, complete space visible, no horizon or deep cinematic perspective
Gameplay clarity: readable floor network, adequate approach space at entrances and interactions, consistent player scale
Exclude: player, NPC, text, UI, grid, red line, debug marker, watermark, clipped room, blocked entrance
```

## 允许重试的硬失败

- 错误投影或空间不在同一可玩坐标平面；
- 必需地标缺失或重复；
- 入口被墙、装饰、阴影或道具堵住；
- 必需路线断裂；
- 空间被画幅裁切；
- 出现角色、NPC、UI、文字或调试标记。

轻微色差、纹理粗细、装饰位置或接触面漂移不触发 `balanced` 重试；优先接受场景并调整碰撞几何。

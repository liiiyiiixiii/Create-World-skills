# 原创示例：《雾港最后一盏灯》

本示例只说明 Schema 2.0 的关键判断。可直接运行的完整数据位于 tests/fixtures/fog-harbor-v2.yaml。

## 输入

1. 林玥买好末班船票，准备离开雾港；父亲只留下用途不明的黄铜钥匙。
2. 风暴令灯塔熄灭。渡船因无法引航而停航；鱼市里仍有人在雨中跳舞，孩子把纸船推入积水。
3. 钥匙打开工具柜，维修日志帮助林玥恢复灯塔。次日她把钥匙交给老何后离开。

用户指定：“保留雨中鱼市与纸船。”

## 结构判断

- N-001 建立离开目标与钥匙。
- N-002 灯塔故障阻断离开，是具有信息发现、时间压力和行动转向的高价值节点。
- N-003 修复、交接并离开，回收钥匙和责任冲突。
- NF-001 鱼市片段不推动主因果，但被用户锁定，必须保留。

## 覆盖与版本

~~~yaml
coverage:
  material_coverage:
    status: "complete"
    units:
      - id: "UNIT-001"
        source_id: "SRC-001"
        label: "lines 1-3"
        status: "analyzed"
        notes: ""
    notes: []
  target_fidelity:
    target_medium: "play"
    target_version: "完整原创梗概"
    status: "verified"
    basis_source_ids: ["SRC-001"]
    caveats: []
~~~

若同样的材料被声明为“电影分析”，而实际只有剧本，材料覆盖仍可为 complete，但 target_fidelity.status 必须为 unverified。

## 普通节点提示

~~~yaml
adaptation_hint:
  priority: "normal"
  player_action: "整理行李并检查父亲留下的钥匙。"
  experience_goal: "让玩家建立离开愿望和未解物件。"
  narrative_invariant: "林玥必须决定当晚离开，并保留黄铜钥匙。"
  selection_reason: ""
  interaction_shape: []
  pressure_or_feedback: ""
~~~

普通节点只给局部行动与体验目标，不把铺垫扩成完整机制。

## 高价值节点提示

~~~yaml
adaptation_hint:
  priority: "high"
  player_action: "在风暴中确认故障、寻找线索并决定折返。"
  experience_goal: "让离开愿望和公共责任形成可操作的时间压力。"
  narrative_invariant: "渡船必须因灯塔失效而停航，林玥必须折返。"
  selection_reason: "同时包含信息发现、时间压力和明确行动转向。"
  interaction_shape:
    - "检查故障"
    - "赶到码头"
    - "听见停航原因"
    - "折返灯塔"
  pressure_or_feedback: "风雨增强、船期逼近，灯光和广播即时反馈航路状态。"
~~~

提示可以改变玩家如何经历该节点，但不能让渡船照常离港或让林玥不再折返。

## 用户锁定片段

~~~yaml
- id: "NF-001"
  title: "雨中鱼市与纸船"
  notability_basis: "user_marked"
  status: "locked"
  related_node_ids: ["N-002"]
  presentation_hint:
    player_involvement: "允许玩家短暂停步观察、推一只纸船或继续赶路。"
    experience_goal: "在时间压力中保留雾港仍然鲜活的生活感。"
    covered_by_node_id: ""
~~~

鱼市片段不承担主线因果，但用户锁定和独立氛围价值使它进入最终档案。

## 生成与验证

~~~shell
python scripts/validate_structure.py tests/fixtures/fog-harbor-v2.yaml
python scripts/render_structure.py tests/fixtures/fog-harbor-v2.yaml --output-dir output/fog-harbor
~~~

渲染结果包含一页概览和完整结构稿；两者均来自同一YAML。


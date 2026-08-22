#!/usr/bin/env python3
"""Render art-direction.md deterministically from art-direction.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from validate_art_direction import load_yaml, territory_score, validate_data


def _items(values: list[str], empty: str = "无") -> str:
    return "；".join(value.rstrip("。；") for value in values) if values else empty


def _bullets(values: list[str], empty: str = "- 无。") -> list[str]:
    return [f"- {value}" for value in values] if values else [empty]


def render(data: dict[str, Any], warnings: list[str]) -> str:
    project = data["project"]
    selection = data["selection"]
    kernel = data["style_kernel"]
    visual = data["visual_system"]
    selected = next(
        item for item in data["territories"] if item["id"] == selection["selected_territory_id"]
    )
    lines = [
        f"# 《{project['title']}》Art Direction",
        "",
        f"> 由 art-direction.yaml 确定性生成；Schema {data['schema_version']}，"
        f"修订 r{data['metadata']['revision']:04d}，状态 **{data['review']['approval_status']}**。",
        "> v1 的 `approved` 只表示生产规范获批，不表示经过目标玩家验证。玩家证据由 `visual-decision.yaml` 单独记录。",
        "",
        "## 1. 方向结论",
        "",
        f"**{kernel['direction_sentence']}**",
        "",
        f"- 选择：{selected['id']} · {selected['name']}",
        f"- 情绪契约：{kernel['emotional_contract']}",
        f"- 选择理由：{selection['selection_rationale']}",
        f"- 接受的代价：{_items(selection['accepted_tradeoffs'])}",
        f"- 身份 token：{_items(kernel['identity_tokens'])}",
        "",
        "## 2. 项目与约束",
        "",
        f"- 改编范围：{project['source_scope']}",
        f"- 游戏形态：{project['game_format']}",
        f"- 平台：{_items(project['target_platforms'])}",
        f"- 画幅：{_items(project['aspect_ratios'])}",
        f"- 镜头：{_items(project['camera_modes'])}",
        f"- 玩家体验：{project['player_experience']}",
        "",
        "### 技术",
        "",
        *_bullets(data["constraints"]["technical"]),
        "",
        "### 玩法可读性",
        "",
        *_bullets(data["constraints"]["gameplay_readability"]),
        "",
        "### 生产与无障碍",
        "",
        *[f"- 生产：{item}" for item in data["constraints"]["production"]],
        *[f"- 无障碍：{item}" for item in data["constraints"]["accessibility"]],
        "",
        "### 假设",
        "",
        *_bullets(data["constraints"]["assumptions"]),
        "",
        "## 3. 来源与视觉观察",
        "",
        "| ID | 来源 | 角色 | 证据状态 | 定位方式 |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {item['id']} | {item['title']} | {item['role']} | {item['evidence_status']} | {item['locator_scheme']} |"
        for item in data["sources"]
    )
    lines += [
        "",
        "| ID | 类别 | 观察 | 置信度 | 来源定位 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in data["observations"]:
        refs = "；".join(f"{ref['source_id']} {ref['locator']}" for ref in item["source_refs"])
        lines.append(
            f"| {item['id']} | {item['category']} | {item['statement']} | {item['confidence']} | {refs} |"
        )

    lines += [
        "",
        "## 4. 候选方向与选型",
        "",
        "| ID | Direction | 忠实 | 可读 | 可产 | 辨识 | 一致 | 总分 | 状态 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in data["territories"]:
        scores = item["scores"]
        lines.append(
            f"| {item['id']} | {item['name']} | {scores['source_fidelity']} | "
            f"{scores['gameplay_readability']} | {scores['production_feasibility']} | "
            f"{scores['distinctiveness']} | {scores['system_coherence']} | "
            f"{territory_score(item)} | {item['status']} |"
        )
        lines += [
            "",
            f"### {item['id']} · {item['name']}",
            "",
            item["thesis"],
            "",
            f"- 视觉公式：{item['visual_formula']}",
            f"- 保留：{_items(item['keeps'])}",
            f"- 转化：{_items(item['transforms'])}",
            f"- 排除：{_items(item['rejects'])}",
            f"- 风险：{_items(item['risks'])}",
            "",
        ]

    lines += ["## 5. 视觉内核", ""]
    for pillar in kernel["pillars"]:
        lines += [
            f"### {pillar['id']} · {pillar['name']}",
            "",
            f"- 规则：{pillar['rule']}",
            f"- Proof：{pillar['proof']}",
            "",
        ]
    lines += ["### 反支柱", "", *_bullets(kernel["anti_pillars"]), ""]

    lines += [
        "## 6. 原作到游戏的转译矩阵",
        "",
        "| ID | 来源线索 | 叙事功能 | 处理 | 游戏规则 | 资产族 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in data["translation_rules"]:
        lines.append(
            f"| {item['id']} | {item['source_cue']} | {item['narrative_function']} | "
            f"{item['treatment']} | {item['game_rule']} | {_items(item['asset_family_ids'])} |"
        )

    pixel = visual["pixel_policy"]
    palette = visual["palette"]
    lines += [
        "",
        "## 7. 视觉系统",
        "",
        "### 像素与采样",
        "",
        f"- 模式：**{pixel['mode']}**",
        f"- 原生规格：{pixel['native_canvas']}",
        f"- 采样：{pixel['sampling']}；显示缩放：{pixel['display_scaling']}",
        f"- 网格规则：{_items(pixel['grid_rules'])}",
        f"- 例外：{_items(pixel['exception_rules'])}",
        "",
        "### 调色板",
        "",
        palette["strategy"],
        "",
        "| 名称 | 色值 | 角色 | 用途 |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {color['name']} | `{color['hex']}` | {color['role']} | {color['usage']} |"
        for color in palette["colors"]
    )
    shape = visual["shape_language"]
    lighting = visual["lighting"]
    camera = visual["camera_composition"]
    material = visual["material_texture"]
    typography = visual["typography_ui"]
    motion = visual["motion_effects"]
    lines += [
        "",
        f"- 场景变体：{_items(palette['scene_variation'])}",
        f"- 禁止漂移：{_items(palette['forbidden_drift'])}",
        "",
        "### 明度、形状与光线",
        "",
        f"- 明度层级：{_items(visual['value_structure'])}",
        f"- 主体块面：{shape['primary_masses']}",
        f"- 边缘：{shape['edge_language']}",
        f"- 轮廓：{shape['silhouette_rule']}",
        f"- 细节：{shape['detail_distribution']}",
        f"- 常态光：{lighting['baseline']}",
        f"- 阴影：{lighting['shadow_logic']}",
        f"- 强调光：{lighting['accent_logic']}",
        f"- 光线变体：{_items(lighting['scene_variation'])}",
        "",
        "### 镜头、材质、UI 与动作",
        "",
        f"- Gameplay camera：{camera['gameplay_camera']}",
        f"- Narrative camera：{camera['narrative_camera']}",
        f"- 构图：{_items(camera['framing_rules'])}",
        f"- 景深：{_items(camera['depth_rules'])}",
        f"- UI 安全区：{_items(camera['ui_safe_zones'])}",
        f"- 材质：{_items(material['base_materials'])}",
        f"- 纹理尺度：{material['texture_scale']}",
        f"- 做旧：{material['weathering_rule']}",
        f"- 禁止效果：{_items(material['forbidden_effects'])}",
        f"- 字体：{typography['font_direction']}",
        f"- 层级：{_items(typography['hierarchy'])}",
        f"- 框架：{typography['frame_language']}",
        f"- 控件：{typography['control_language']}",
        f"- 对比：{typography['contrast_rule']}",
        f"- 动画节奏：{motion['frame_cadence']}",
        f"- 缓动：{motion['easing_language']}",
        f"- 环境动势：{_items(motion['ambient_motion'])}",
        f"- 冲击效果：{_items(motion['impact_effects'])}",
        f"- 克制规则：{_items(motion['restraint_rules'])}",
        "",
        "## 8. 资产族规范",
        "",
    ]
    for family in data["asset_families"]:
        lines += [
            f"### {family['id']} · {family['name']}",
            "",
            f"- 功能：{family['function']}",
            f"- 表现模式：{family['visual_mode']}；镜头：{family['camera']}",
            f"- 原生规格：{family['native_spec']}",
            f"- 缩放：{family['scale_rule']}",
            f"- 色彩：{family['palette_rule']}",
            f"- 形状：{family['shape_rule']}",
            f"- 光线：{family['lighting_rule']}",
            f"- 细节预算：{family['detail_budget']}",
            f"- 动作：{family['motion_rule']}",
            f"- 可读性测试：{family['readability_test']}",
            f"- Do：{_items(family['do'])}",
            f"- Avoid：{_items(family['avoid'])}",
            "",
        ]

    capsule = data["prompt_capsule"]
    lines += [
        "## 9. 下游提示词胶囊",
        "",
        f"- Style anchor：{capsule['style_anchor']}",
        f"- Positive：{_items(capsule['positive_tokens'])}",
        f"- Negative：{_items(capsule['negative_tokens'])}",
        f"- 构图模板：{capsule['composition_template']}",
        "",
    ]
    for family_id, note in capsule["asset_specific_notes"].items():
        lines.append(f"- {family_id}：{note}")

    lines += [
        "",
        "## 10. Pilot 计划",
        "",
        f"- 生成状态：{data['pilot_plan']['generation_status']}",
        f"- 产物：{_items(data['pilot_plan']['artifact_paths'])}",
        "",
    ]
    for test in data["pilot_plan"]["tests"]:
        lines += [
            f"### {test['id']} · {test['asset_family_id']}",
            "",
            f"- 假设：{test['hypothesis']}",
            f"- 交付物：{test['deliverable']}",
            f"- 通过条件：{_items(test['pass_criteria'])}",
            "",
        ]

    lines += [
        "## 11. QA 与风险",
        "",
        "| ID | 类别 | 严重度 | 标准 | 方法 |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {gate['id']} | {gate['category']} | {gate['severity']} | {gate['criterion']} | {gate['method']} |"
        for gate in data["qa"]["gates"]
    )
    lines += [
        "",
        "### 已知风险",
        "",
        *_bullets(data["qa"]["known_risks"]),
        "",
        "### 未决问题",
        "",
        *_bullets(data["qa"]["open_questions"]),
        "",
        "### 校验说明",
        "",
        *_bullets(data["review"]["validation_notes"]),
    ]
    if warnings:
        lines += ["", "### 当前警告", "", *_bullets(warnings)]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("yaml_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        data = load_yaml(args.yaml_path)
        result = validate_data(data)
    except Exception as error:  # CLI boundary reports concise failure.
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    destination = args.output_dir / "art-direction.md"
    destination.write_text(render(data, result.warnings), encoding="utf-8")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    print(f"WROTE: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

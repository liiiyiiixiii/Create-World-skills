#!/usr/bin/env python3
"""Render overview.md and structure.md deterministically from structure.yaml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from validate_structure import DEFAULT_SCHEMA, load_yaml, validate_data


def _refs(refs: list[dict[str, str]]) -> str:
    return "；".join(
        f"{ref['source_id']} {ref['locator']}" + (f"（{ref['note']}）" if ref.get("note") else "")
        for ref in refs
    )


def _items(values: list[str], empty: str = "无") -> str:
    return "、".join(values) if values else empty


def _active_nodes(data: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [node for node in data["nodes"] if not node.get("superseded_by")],
        key=lambda item: (item["order"], item["id"]),
    )


def render_overview(data: dict[str, Any]) -> str:
    work = data["work"]
    coverage = data["coverage"]
    nodes = _active_nodes(data)
    spine = [node for node in nodes if node["importance"] == "spine"]
    high = [node for node in nodes if node["adaptation_hint"]["priority"] == "high"]
    fragments = [item for item in data["notable_fragments"] if item["status"] != "excluded"]
    lines = [
        f"# 《{work['title']}》结构概览",
        "",
        f"- Schema：{data['schema_version']}",
        f"- Skill：{data['metadata']['skill_version']}",
        f"- 修订：r{data['metadata']['revision']:04d}",
        f"- 分析范围：{work['scope']}",
        f"- 材料覆盖：**{coverage['material_coverage']['status']}**",
        f"- 目标版本可信度：**{coverage['target_fidelity']['status']}** — "
        f"{coverage['target_fidelity']['target_medium']} / {coverage['target_fidelity']['target_version']}",
    ]
    if coverage["target_fidelity"]["caveats"]:
        lines.append(f"- 版本限制：{_items(coverage['target_fidelity']['caveats'])}")
    lines += [
        "",
        "## 故事概览",
        "",
        data["overview"]["premise"],
        "",
        f"**核心问题：** {data['overview']['central_question'].get('claim', '')}",
        "",
        f"- 初始状态：{data['overview']['initial_state']}",
        f"- 最终状态：{data['overview']['final_state']}",
        "",
        "## 故事脊柱",
        "",
        "| ID | 节点 | 结果 |",
        "| --- | --- | --- |",
    ]
    lines.extend(f"| {node['id']} | {node['title']} | {node['outcome']} |" for node in spine)
    lines += ["", "## 高价值玩法候选", ""]
    if high:
        for node in high:
            hint = node["adaptation_hint"]
            lines += [
                f"### {node['id']} · {node['title']}",
                "",
                f"- 玩家行动：{hint['player_action']}",
                f"- 体验目标：{hint['experience_goal']}",
                f"- 简要流程：{' → '.join(hint['interaction_shape'])}",
                f"- 不可破坏：{hint['narrative_invariant']}",
                "",
            ]
    else:
        lines += ["无高价值玩法候选。", ""]
    lines += ["## 精选片段", ""]
    if fragments:
        lines += ["| ID | 片段 | 状态 | 保留价值 |", "| --- | --- | --- | --- |"]
        lines.extend(
            f"| {item['id']} | {item['title']} | {item['status']} | {item['retention_reason']} |"
            for item in fragments
        )
    else:
        lines.append("无未排除片段。")
    lines += ["", "## 主要缺口", ""]
    if data["gaps"]:
        lines.extend(f"- {item['id']}：{item.get('description', '')}" for item in data["gaps"])
    else:
        lines.append("- 无。")
    lines += [
        "",
        "## 审阅入口",
        "",
        "- 可按ID锁定、排除或恢复片段。",
        "- 可按ID合并、拆分节点，调整 spine/support 或 normal/high。",
        "- 玩法提示是设计提案；原作事实与分析推断请在完整结构稿中核对。",
        "",
    ]
    return "\n".join(lines)


def _render_hint(node: dict[str, Any]) -> list[str]:
    hint = node["adaptation_hint"]
    lines = [
        f"- 优先级：{hint['priority']}",
        f"- 玩家行动：{hint['player_action']}",
        f"- 体验目标：{hint['experience_goal']}",
        f"- 叙事不变量：{hint['narrative_invariant']}",
    ]
    if hint["priority"] == "high":
        lines += [
            f"- 提名理由：{hint['selection_reason']}",
            f"- 交互形态：{' → '.join(hint['interaction_shape'])}",
            f"- 压力/反馈：{hint['pressure_or_feedback']}",
        ]
    return lines


def render_structure(data: dict[str, Any], warnings: list[str]) -> str:
    work = data["work"]
    coverage = data["coverage"]
    nodes = _active_nodes(data)
    by_id = {node["id"]: node for node in nodes}
    lines = [
        f"# 《{work['title']}》叙事结构稿",
        "",
        f"> 由 structure.yaml 确定性生成；Schema {data['schema_version']}，"
        f"修订 r{data['metadata']['revision']:04d}。",
        "",
        "## 1. 分析范围与覆盖",
        "",
        f"- 范围：{work['scope']}",
        f"- 材料覆盖：**{coverage['material_coverage']['status']}**",
        f"- 目标版本：{coverage['target_fidelity']['target_medium']} / "
        f"{coverage['target_fidelity']['target_version']}",
        f"- 目标可信度：**{coverage['target_fidelity']['status']}**",
    ]
    if coverage["target_fidelity"]["caveats"]:
        lines.append(f"- 限制：{_items(coverage['target_fidelity']['caveats'])}")
    lines += [
        "",
        "### 来源",
        "",
        "| ID | 标题 | 角色 | 定位 |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {src['id']} | {src['title']} | {src['role']} | {src['locator_scheme']} |"
        for src in data["sources"]
    )
    lines += ["", "### 覆盖单元", "", "| ID | 来源 | 单元 | 状态 |", "| --- | --- | --- | --- |"]
    lines.extend(
        f"| {unit['id']} | {unit['source_id']} | {unit['label']} | {unit['status']} |"
        for unit in coverage["material_coverage"]["units"]
    )
    lines += [
        "",
        "## 2. 故事概览",
        "",
        data["overview"]["premise"],
        "",
        f"**核心问题：** {data['overview']['central_question'].get('claim', '')}",
        "",
        f"- 初始状态：{data['overview']['initial_state']}",
        f"- 最终状态：{data['overview']['final_state']}",
        "",
        "## 3. 故事脊柱",
        "",
        "| ID | 节点 | 结果 |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        f"| {node['id']} | {node['title']} | {node['outcome']} |"
        for node in nodes
        if node["importance"] == "spine"
    )
    lines += ["", "## 4. 分段、节点与轻量玩法提示", ""]
    for segment in sorted(data["segments"], key=lambda item: (item["order"], item["id"])):
        lines += [f"### {segment['id']} · {segment['title']}", ""]
        if segment.get("structural_purpose"):
            lines += [segment["structural_purpose"], ""]
        for node_id in segment["node_ids"]:
            node = by_id[node_id]
            lines += [
                f"#### {node['id']} · {node['title']}｜{node['importance']}",
                "",
                node["summary"],
                "",
                "**原作事实**",
                "",
            ]
            if node["facts"]:
                for fact in node["facts"]:
                    lines.append(f"- {fact['claim']}（{_refs(fact['source_refs'])}）")
            else:
                lines.append("- 无。")
            lines += ["", "**分析推断**", ""]
            if node["inferences"]:
                for inference in node["inferences"]:
                    basis = _refs(inference.get("basis_refs", []))
                    suffix = f"；依据：{basis}" if basis else ""
                    lines.append(
                        f"- [{inference.get('confidence', '')}] {inference.get('claim', '')}"
                        f"；理由：{inference.get('rationale', '')}{suffix}"
                    )
            else:
                lines.append("- 无。")
            lines += [
                "",
                f"- 结果：{node['outcome']}",
                "",
                "**轻量玩法提示（设计提案）**",
                "",
            ]
            lines.extend(_render_hint(node))
            lines.append("")
    lines += ["## 5. 精选片段库", ""]
    for fragment in sorted(data["notable_fragments"], key=lambda item: (item["order"], item["id"])):
        hint = fragment["presentation_hint"]
        lines += [
            f"### {fragment['id']} · {fragment['title']}｜{fragment['status']}",
            "",
            fragment["summary"],
            "",
            f"- 来源：{_refs(fragment['source_refs'])}",
            f"- 价值：{_items(fragment['reason_tags'])}",
            f"- 保留理由：{fragment['retention_reason']}",
            f"- 玩家参与：{hint['player_involvement']}",
            f"- 体验目标：{hint['experience_goal']}",
        ]
        if hint["covered_by_node_id"]:
            lines.append(f"- 已由节点覆盖：{hint['covered_by_node_id']}")
        lines.append("")
    lines += ["## 6. 人物目标与关系", ""]
    if data["characters"]:
        for character in data["characters"]:
            lines += [
                f"### {character['id']} · {character.get('name', '')}",
                "",
                f"- 作用：{character.get('role', '')}",
                f"- 初始状态：{character.get('initial_state', '')}",
                "",
            ]
    else:
        lines += ["无。", ""]
    lines += ["## 7. 关键物件、信息、地点与意象", ""]
    if data["story_elements"]:
        lines += ["| ID | 元素 | 类型 | 结构作用 |", "| --- | --- | --- | --- |"]
        lines.extend(
            f"| {item['id']} | {item.get('name', '')} | {item.get('type', '')} | "
            f"{item.get('structural_role', '')} |"
            for item in data["story_elements"]
        )
    else:
        lines.append("无。")
    lines += ["", "## 8. 铺垫与回收", ""]
    if data["setup_payoffs"]:
        lines += ["| ID | 状态 | 说明 |", "| --- | --- | --- |"]
        lines.extend(
            f"| {item['id']} | {item.get('status', '')} | {item.get('explanation', '')} |"
            for item in data["setup_payoffs"]
        )
    else:
        lines.append("无。")
    lines += ["", "## 9. 缺口与版本问题", ""]
    if data["gaps"]:
        for gap in data["gaps"]:
            lines += [
                f"### {gap['id']} · {gap.get('type', '')}",
                "",
                gap.get("description", ""),
                "",
                f"- 影响：{gap.get('impact', '')}",
                f"- 处理：{gap.get('resolution_needed', '')}",
                "",
            ]
    else:
        lines += ["无。", ""]
    lines += ["## 10. 审阅与验证", ""]
    review = data["review"]
    for label, key in [
        ("待核实事实", "facts_to_verify"),
        ("待确认推断", "inferences_to_review"),
        ("待审片段", "notable_fragments_to_review"),
        ("待审玩法提示", "adaptation_hints_to_review"),
    ]:
        lines.append(f"- {label}：{_items(review[key])}")
    lines.append(f"- 用户锁定片段：{_items(review['user_locked_fragment_ids'])}")
    notes = list(review["validation_notes"]) + warnings
    lines.append(f"- 校验说明：{_items(notes)}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = args.structure.resolve()
    data = load_yaml(source)
    result = validate_data(data, args.schema.resolve())
    for message in result.errors:
        print(f"ERROR: {message}")
    for message in result.warnings:
        print(f"WARNING: {message}")
    if result.errors:
        return 1
    output_dir = (args.output_dir or source.parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "overview.md").write_text(render_overview(data), encoding="utf-8")
    (output_dir / "structure.md").write_text(
        render_structure(data, result.warnings), encoding="utf-8"
    )
    print(f"WROTE: {output_dir / 'overview.md'}")
    print(f"WROTE: {output_dir / 'structure.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


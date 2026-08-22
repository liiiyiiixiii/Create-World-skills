#!/usr/bin/env python3
"""Validate, test, analyze, report, and export a 2D visual-direction decision."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import os
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


SKILL_ROOT = Path(__file__).resolve().parents[1]
DECISION_SCHEMA = SKILL_ROOT / "references" / "visual-decision-v1.schema.json"
ANALYSIS_SCHEMA = SKILL_ROOT / "references" / "player-analysis-v1.schema.json"
CONTRACT_SCHEMA = SKILL_ROOT / "references" / "style-contract-v1.schema.json"
GATE_CATEGORIES = {"source_function", "craft", "readability", "technical", "production"}
FINAL_STATUSES = {"player_supported", "creator_selected_unvalidated", "creator_override"}
PANELS = {"gameplay_scene", "native_character", "ui_hud", "narrative_frame"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    return data


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")
    return data


def _load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_text(parts: Iterable[Any]) -> str:
    text = "$"
    for part in parts:
        text += f"[{part}]" if isinstance(part, int) else f".{part}"
    return text


def _schema_errors(data: dict[str, Any], schema_path: Path) -> list[str]:
    validator = Draft202012Validator(
        _load_schema(schema_path), format_checker=FormatChecker()
    )
    return [
        f"{_path_text(error.absolute_path)}: {error.message}"
        for error in sorted(
            validator.iter_errors(data), key=lambda item: list(item.absolute_path)
        )
    ]


def _duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _is_relative_safe(path_text: str) -> bool:
    path = Path(path_text)
    return bool(path_text) and not path.is_absolute() and ".." not in path.parts


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_test(data: dict[str, Any], test_id: str) -> dict[str, Any]:
    for test in data["player_tests"]:
        if test["id"] == test_id:
            return test
    raise ValueError(f"unknown player test {test_id}")


def _gate_matrix(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    matrix: dict[str, dict[str, str]] = {
        item["id"]: {} for item in data["candidates"]
    }
    for gate in data["craft_gates"]:
        matrix.setdefault(gate["candidate_id"], {})[gate["category"]] = gate["result"]
    return matrix


def _gate_pass_candidates(data: dict[str, Any]) -> list[str]:
    matrix = _gate_matrix(data)
    return sorted(
        candidate_id
        for candidate_id, categories in matrix.items()
        if set(categories) == GATE_CATEGORIES
        and all(result == "pass" for result in categories.values())
    )


def validate_decision(
    data: dict[str, Any],
    *,
    base_path: Path | None = None,
    check_files: bool = False,
    analysis: dict[str, Any] | None = None,
) -> ValidationResult:
    result = ValidationResult(errors=_schema_errors(data, DECISION_SCHEMA))
    if result.errors:
        return result

    candidates = {item["id"]: item for item in data["candidates"]}
    candidate_ids = list(candidates)
    if duplicates := _duplicates(candidate_ids):
        result.errors.append(f"duplicate candidate IDs: {', '.join(duplicates)}")
    blind_ids = [item["blind_id"] for item in data["candidates"]]
    if duplicates := _duplicates(blind_ids):
        result.errors.append(f"duplicate blind IDs: {', '.join(duplicates)}")
    for candidate in data["candidates"]:
        if candidate["id"] != f"C-{candidate['blind_id']}":
            result.errors.append(
                f"{candidate['id']}: id and blind_id must identify the same candidate"
            )
        if candidate["benchmark_id"] != data["benchmark"]["id"]:
            result.errors.append(
                f"{candidate['id']}: benchmark_id must match benchmark.id"
            )
        if set(candidate["panel_coverage"]) != PANELS:
            result.errors.append(f"{candidate['id']}: must cover the four benchmark panels")
        if candidate["generation_attempts"] > data["benchmark"]["max_generation_attempts"]:
            result.errors.append(f"{candidate['id']}: generation attempt limit exceeded")
        if candidate["revision_round"] == 0 and candidate["derived_from"] is not None:
            result.errors.append(f"{candidate['id']}: first-round candidate cannot derive from another")
        if candidate["revision_round"] == 1 and candidate["derived_from"] is None:
            result.errors.append(f"{candidate['id']}: revised candidate requires derived_from")
        for key in ("board_path",):
            if not _is_relative_safe(candidate[key]):
                result.errors.append(f"{candidate['id']}.{key} must be a safe relative path")
        if check_files and base_path is not None:
            board = base_path / candidate["board_path"]
            if not board.is_file():
                result.errors.append(f"{candidate['id']}: board file does not exist: {board}")
            elif _sha256(board) != candidate["board_sha256"]:
                result.errors.append(f"{candidate['id']}: board_sha256 does not match file")

    revised = [item for item in data["candidates"] if item["revision_round"] == 1]
    if len(revised) > 2:
        result.errors.append("at most two candidates may be revised in the second round")

    gate_ids = [gate["id"] for gate in data["craft_gates"]]
    if duplicates := _duplicates(gate_ids):
        result.errors.append(f"duplicate craft gate IDs: {', '.join(duplicates)}")
    seen_gate_keys: set[tuple[str, str]] = set()
    for gate in data["craft_gates"]:
        if gate["candidate_id"] not in candidates:
            result.errors.append(
                f"{gate['id']}: unknown candidate {gate['candidate_id']}"
            )
        gate_key = (gate["candidate_id"], gate["category"])
        if gate_key in seen_gate_keys:
            result.errors.append(
                f"duplicate {gate['category']} gate for {gate['candidate_id']}"
            )
        seen_gate_keys.add(gate_key)

    status = data["status"]
    if status != "draft" and set(candidate_ids) != {"C-A", "C-B", "C-C"}:
        result.errors.append(f"{status} requires exactly candidates C-A, C-B, and C-C")
    if status in {
        "test_ready",
        "tested_inconclusive",
        "player_supported",
        "creator_selected_unvalidated",
        "creator_override",
    }:
        if any(item["status"] != "pass" for item in data["source_functions"]):
            result.errors.append(f"{status} requires every source function to pass")
        gate_pass_count = len(_gate_pass_candidates(data))
        if status == "test_ready" and gate_pass_count != 3:
            result.errors.append("test_ready requires all three candidates to pass every craft gate")
        elif status != "test_ready" and gate_pass_count < 2:
            result.errors.append(f"{status} requires at least two gate-passing candidates")

    test_ids = [item["id"] for item in data["player_tests"]]
    if duplicates := _duplicates(test_ids):
        result.errors.append(f"duplicate player test IDs: {', '.join(duplicates)}")
    rounds = [str(item["round"]) for item in data["player_tests"]]
    if duplicates := _duplicates(rounds):
        result.errors.append(f"duplicate player test rounds: {', '.join(duplicates)}")
    for test in data["player_tests"]:
        for path_text in test["response_paths"]:
            if not _is_relative_safe(path_text):
                result.errors.append(f"{test['id']}: response path must be relative: {path_text}")
        if test["analysis_path"] is not None and not _is_relative_safe(test["analysis_path"]):
            result.errors.append(f"{test['id']}: analysis_path must be a safe relative path")
        if test["status"] == "completed" and not test["response_paths"]:
            result.errors.append(f"{test['id']}: completed test requires response_paths")
        if test["status"] == "completed" and not test["analysis_path"]:
            result.errors.append(f"{test['id']}: completed test requires analysis_path")

    for path_text in data["provenance"]["source_paths"]:
        if not _is_relative_safe(path_text):
            result.errors.append(f"provenance source path must be relative: {path_text}")
    for path_text in data["provenance"]["input_hashes"]:
        if not _is_relative_safe(path_text):
            result.errors.append(f"provenance hash key must be a relative path: {path_text}")

    recommendation = data["recommendation"]
    creator = data["creator_decision"]
    if recommendation["candidate_id"] is not None and recommendation["candidate_id"] not in candidates:
        result.errors.append("recommendation references an unknown candidate")
    if creator["selected_candidate_id"] is not None and creator["selected_candidate_id"] not in candidates:
        result.errors.append("creator decision references an unknown candidate")

    if status in {"draft", "candidates_ready", "test_ready"}:
        if recommendation["status"] != "not_ready" or creator["status"] != "undecided":
            result.errors.append(f"{status} cannot contain a completed recommendation or decision")
    elif status == "tested_inconclusive":
        if recommendation["status"] != "inconclusive":
            result.errors.append("tested_inconclusive requires an inconclusive recommendation")
    elif status == "player_supported":
        if recommendation["status"] != "player_leader":
            result.errors.append("player_supported requires a player_leader recommendation")
        if creator["status"] != "accepted_player_leader":
            result.errors.append("player_supported requires creator acceptance")
        if creator["selected_candidate_id"] != recommendation["candidate_id"]:
            result.errors.append("creator must accept the recommended player leader")
    elif status == "creator_override":
        if recommendation["status"] != "player_leader":
            result.errors.append("creator_override requires a player_leader recommendation")
        if creator["status"] != "overrode_player_leader":
            result.errors.append("creator_override requires overrode_player_leader")
        if creator["selected_candidate_id"] == recommendation["candidate_id"]:
            result.errors.append("creator_override must select a different candidate")
        if not creator["rationale"].strip():
            result.errors.append("creator_override requires a rationale")
    elif status == "creator_selected_unvalidated":
        if creator["status"] != "selected_without_validation":
            result.errors.append(
                "creator_selected_unvalidated requires selected_without_validation"
            )
        if creator["selected_candidate_id"] is None:
            result.errors.append("creator_selected_unvalidated requires a selected candidate")

    if status in FINAL_STATUSES and creator["decided_at"] is None:
        result.errors.append(f"{status} requires creator_decision.decided_at")

    if analysis is not None:
        result.errors.extend(_schema_errors(analysis, ANALYSIS_SCHEMA))
        if not result.errors:
            try:
                analyzed_test = _find_test(data, analysis["test_id"])
            except ValueError as error:
                result.errors.append(str(error))
                analyzed_test = None
            if analyzed_test is not None:
                recorded_responses = {
                    Path(path_text).name for path_text in analyzed_test["response_paths"]
                }
                analyzed_responses = set(analysis["response_hashes"])
                if recorded_responses != analyzed_responses:
                    result.errors.append(
                        "player test response_paths must match every hashed analysis input"
                    )
                if analyzed_test["round"] != analysis["test_round"]:
                    result.errors.append("player test round conflicts with analysis")
                if analyzed_test["cohort_type"] != analysis["cohort_type"]:
                    result.errors.append("player test cohort_type conflicts with analysis")
            if analysis["input_response_count"] != len(analysis["response_hashes"]):
                result.errors.append("analysis input count must match response hashes")
            if analysis["input_response_count"] != (
                analysis["valid_response_count"] + len(analysis["excluded_responses"])
            ):
                result.errors.append("analysis input count must equal valid plus excluded responses")
            if analysis["result"] == "player_leader":
                if recommendation["status"] not in {"player_leader", "not_ready"}:
                    result.errors.append("decision recommendation conflicts with analysis")
                if recommendation["candidate_id"] not in {
                    analysis["leader_candidate_id"],
                    None,
                }:
                    result.errors.append("recommended candidate conflicts with analysis leader")
            elif recommendation["status"] == "player_leader":
                result.errors.append("inconclusive analysis cannot support player_leader")
            if status == "player_supported" and analysis["result"] != "player_leader":
                result.errors.append("player_supported requires conclusive player analysis")
            if status == "player_supported" and analysis["leader_candidate_id"] != creator["selected_candidate_id"]:
                result.errors.append("selected candidate does not match player analysis leader")
            if status == "player_supported" and analysis["test_round"] == 2 and analysis["cohort_type"] != "new":
                result.errors.append("second-round player support requires a fresh cohort")

    return result


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _test_config(data: dict[str, Any], test: dict[str, Any], base_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "test_id": test["id"],
        "candidate_ids": [item["id"] for item in data["candidates"]],
        "candidates": [
            {"id": item["id"], "image": _data_uri(base_path / item["board_path"])}
            for item in data["candidates"]
        ],
        "screen": test["target_player_screen"],
        "tasks": [
            {
                "id": item["id"],
                "prompt": item["prompt"],
                "options": item["options"],
                "exposure_seconds": item["exposure_seconds"],
            }
            for item in data["benchmark"]["readability_tasks"]
        ],
    }


def build_test_page(data: dict[str, Any], test: dict[str, Any], base_path: Path) -> str:
    config_json = json.dumps(
        _test_config(data, test, base_path), ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    title = html.escape(data["decision_brief"]["title"])
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:,">
<title>{title} · 匿名视觉方向测试</title>
<style>
:root{{--ink:#172033;--muted:#65708a;--paper:#f4f1e8;--card:#fff;--accent:#bb5a2a;--line:#d8d1c2}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}
main{{width:min(920px,calc(100% - 28px));margin:28px auto 80px}}h1,h2{{line-height:1.18}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 8px 24px #17203312}}
.notice{{color:var(--muted)}}.candidate img{{display:block;width:100%;height:auto;border-radius:10px;background:#111}}
.candidate img.hidden{{visibility:hidden}}label{{display:block;margin:12px 0}}select,textarea,button{{font:inherit}}
select,textarea{{width:100%;padding:9px;border:1px solid var(--line);border-radius:8px;background:#fff}}
textarea{{min-height:78px}}button{{border:0;border-radius:9px;padding:11px 16px;background:var(--accent);color:#fff;cursor:pointer}}
button:disabled{{opacity:.45;cursor:not-allowed}}.rating-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.task-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.error{{color:#a51d1d;font-weight:650}}
@media(max-width:680px){{.rating-grid,.task-grid{{grid-template-columns:1fr}}.card{{padding:16px}}}}
</style>
</head>
<body>
<main>
<section class="card">
<h1>{title}：匿名视觉方向测试</h1>
<p>本测试比较三套内容和构图相同的视觉样板。候选顺序会随机化；请按第一感受作答。</p>
<p class="notice">不收集姓名或邮箱，答案只保存在本设备，提交时下载一个 JSON 文件。招募与知情同意由测试组织者负责。</p>
<label><input id="consent" type="checkbox"> 我知情同意参加本次测试。</label>
<label><input id="targetMatch" type="checkbox"> 我符合以下目标玩家条件：</label>
<ul id="screen"></ul>
<label>注意力检查：请选择“4”<select id="attention"><option value="">请选择</option><option>2</option><option>4</option><option>6</option></select></label>
</section>
<div id="candidates"></div>
<section class="card">
<h2>整体排序</h2>
<p>请把三套方案排成第一、第二、第三，不能重复。</p>
<div class="rating-grid" id="ranking"></div>
<label>还有什么影响了你的选择？<textarea id="overallComment"></textarea></label>
<p id="error" class="error" role="alert"></p>
<button id="download">完成并下载匿名答卷</button>
</section>
</main>
<script id="config" type="application/json">{config_json}</script>
<script>
const cfg=JSON.parse(document.getElementById('config').textContent);
const shuffle=a=>{{a=[...a];for(let i=a.length-1;i>0;i--){{const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}}return a}};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
const order=shuffle(cfg.candidates);const labels=new Map(order.map((c,i)=>[c.id,`方案 ${{i+1}}`]));
document.getElementById('screen').innerHTML=cfg.screen.map(x=>`<li>${{esc(x)}}</li>`).join('');
const optionHtml=()=>order.map(c=>`<option value="${{c.id}}">${{labels.get(c.id)}}</option>`).join('');
const rating=(name,label)=>`<label>${{label}}<select data-field="${{name}}"><option value="">1–7</option>${{[1,2,3,4,5,6,7].map(n=>`<option>${{n}}</option>`).join('')}}</select></label>`;
const container=document.getElementById('candidates');
order.forEach((candidate,index)=>{{
  const section=document.createElement('section');section.className='card candidate';section.dataset.candidate=candidate.id;section.dataset.step=String(index);
  section.innerHTML=`<h2>${{labels.get(candidate.id)}}</h2><p>点击后样板只显示 ${{Math.max(...cfg.tasks.map(t=>t.exposure_seconds))}} 秒，然后回答可读性问题。</p><button class="expose">开始限时观看</button><img class="hidden" alt="${{labels.get(candidate.id)}}综合视觉样板" src="${{candidate.image}}"><div class="answers" hidden><div class="rating-grid">${{rating('appeal','视觉吸引力')}}${{rating('narrative_fit','与叙事气质契合')}}${{rating('want_to_play','想进一步游玩')}}</div><div class="task-grid">${{cfg.tasks.map(t=>`<label>${{esc(t.prompt)}}<select data-task="${{t.id}}"><option value="">请选择</option>${{t.options.map(o=>`<option>${{esc(o)}}</option>`).join('')}}</select></label>`).join('')}}</div><label>喜欢或不喜欢什么？<textarea data-field="comment"></textarea></label></div>`;
  const button=section.querySelector('.expose'),image=section.querySelector('img'),answers=section.querySelector('.answers');
  button.disabled=index>0;
  button.addEventListener('click',()=>{{button.disabled=true;image.classList.remove('hidden');setTimeout(()=>{{image.classList.add('hidden');answers.hidden=false;const next=container.querySelector(`.candidate[data-step="${{index+1}}"] .expose`);if(next)next.disabled=false}},Math.max(...cfg.tasks.map(t=>t.exposure_seconds))*1000)}});
  container.appendChild(section);
}});
document.getElementById('ranking').innerHTML=[1,2,3].map(n=>`<label>第 ${{n}} 名<select data-rank="${{n}}"><option value="">请选择</option>${{optionHtml()}}</select></label>`).join('');
const uuid=()=>globalThis.crypto?.randomUUID?.()||`anon-${{Date.now()}}-${{Math.random().toString(16).slice(2)}}`;
document.getElementById('download').addEventListener('click',()=>{{
  const error=document.getElementById('error');error.textContent='';
  if(!document.getElementById('consent').checked){{error.textContent='请先确认知情同意。';return}}
  const ranking=[...document.querySelectorAll('[data-rank]')].map(x=>x.value);
  if(ranking.some(x=>!x)||new Set(ranking).size!==3){{error.textContent='请完成不重复的三项排序。';return}}
  const responses={{}};let incomplete=false;
  document.querySelectorAll('.candidate').forEach(section=>{{
    const values=name=>section.querySelector(`[data-field="${{name}}"]`)?.value||'';
    const readability_answers={{}};section.querySelectorAll('[data-task]').forEach(x=>readability_answers[x.dataset.task]=x.value);
    const ratings={{appeal:Number(values('appeal')),narrative_fit:Number(values('narrative_fit')),want_to_play:Number(values('want_to_play'))}};
    if(Object.values(ratings).some(x=>!x)||Object.values(readability_answers).some(x=>!x))incomplete=true;
    responses[section.dataset.candidate]={{ratings,readability_answers,comment:values('comment')}};
  }});
  if(incomplete){{error.textContent='请先观看并完成每套方案的评分和可读性问题。';return}}
  const payload={{schema_version:'1.0',test_id:cfg.test_id,participant_id:uuid(),submitted_at:new Date().toISOString(),candidate_order:order.map(x=>x.id),target_player_match:document.getElementById('targetMatch').checked,attention_check_passed:document.getElementById('attention').value==='4',ranking,responses,overall_comment:document.getElementById('overallComment').value}};
  const blob=new Blob([JSON.stringify(payload,null,2)],{{type:'application/json'}}),url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=`${{cfg.test_id}}-${{payload.participant_id}}.json`;a.click();URL.revokeObjectURL(url);
}});
</script>
</body>
</html>
"""


def _validate_response(
    payload: dict[str, Any],
    test_id: str,
    candidate_ids: list[str],
    task_ids: list[str],
) -> str | None:
    if payload.get("schema_version") != "1.0":
        return "unsupported response schema"
    if payload.get("test_id") != test_id:
        return "response belongs to another test"
    if not isinstance(payload.get("participant_id"), str) or not payload["participant_id"]:
        return "missing anonymous participant ID"
    if payload.get("target_player_match") is not True:
        return "participant does not match target screen"
    if payload.get("attention_check_passed") is not True:
        return "attention check failed"
    if sorted(payload.get("candidate_order", [])) != sorted(candidate_ids):
        return "candidate order is incomplete"
    ranking = payload.get("ranking")
    if not isinstance(ranking, list) or len(ranking) != len(candidate_ids):
        return "ranking is incomplete"
    if sorted(ranking) != sorted(candidate_ids):
        return "ranking must contain every candidate exactly once"
    responses = payload.get("responses")
    if not isinstance(responses, dict) or set(responses) != set(candidate_ids):
        return "candidate responses are incomplete"
    for candidate_id in candidate_ids:
        response = responses[candidate_id]
        if not isinstance(response, dict):
            return f"{candidate_id} response is invalid"
        ratings = response.get("ratings")
        if not isinstance(ratings, dict) or set(ratings) != {
            "appeal",
            "narrative_fit",
            "want_to_play",
        }:
            return f"{candidate_id} ratings are incomplete"
        if any(not isinstance(value, int) or not 1 <= value <= 7 for value in ratings.values()):
            return f"{candidate_id} ratings must be integers from 1 to 7"
        answers = response.get("readability_answers")
        if not isinstance(answers, dict) or set(answers) != set(task_ids):
            return f"{candidate_id} readability answers are incomplete"
    return None


def analyze_responses(
    data: dict[str, Any], test: dict[str, Any], response_paths: list[Path]
) -> dict[str, Any]:
    candidate_ids = [item["id"] for item in data["candidates"]]
    tasks = data["benchmark"]["readability_tasks"]
    expected = {item["id"]: item["expected_answer"] for item in tasks}
    valid: list[tuple[Path, dict[str, Any]]] = []
    excluded: list[dict[str, str]] = []
    participant_ids: set[str] = set()
    response_hashes: dict[str, str] = {}
    for path in sorted(response_paths, key=lambda item: item.as_posix().casefold()):
        try:
            response_hashes[path.name] = _sha256(path)
        except OSError as error:
            excluded.append({"file": path.name, "reason": f"unreadable file: {error}"})
            continue
        try:
            payload = load_json(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            excluded.append({"file": path.name, "reason": f"invalid JSON: {error}"})
            continue
        reason = _validate_response(payload, test["id"], candidate_ids, list(expected))
        participant_id = payload.get("participant_id")
        if reason is None and participant_id in participant_ids:
            reason = "duplicate anonymous participant ID"
        if reason:
            excluded.append({"file": path.name, "reason": reason})
            continue
        participant_ids.add(participant_id)
        valid.append((path, payload))

    metrics: dict[str, dict[str, Any]] = {}
    valid_count = len(valid)
    for candidate_id in candidate_ids:
        rankings = [payload["ranking"] for _, payload in valid]
        appeals = [payload["responses"][candidate_id]["ratings"]["appeal"] for _, payload in valid]
        fits = [payload["responses"][candidate_id]["ratings"]["narrative_fit"] for _, payload in valid]
        wants = [payload["responses"][candidate_id]["ratings"]["want_to_play"] for _, payload in valid]
        total_answers = valid_count * len(expected)
        correct = sum(
            payload["responses"][candidate_id]["readability_answers"][task_id]
            == answer
            for _, payload in valid
            for task_id, answer in expected.items()
        )
        pairwise: dict[str, float] = {}
        for other in candidate_ids:
            if other == candidate_id:
                continue
            wins = sum(ranking.index(candidate_id) < ranking.index(other) for ranking in rankings)
            pairwise[other] = round(wins / valid_count, 4) if valid_count else 0.0
        metrics[candidate_id] = {
            "first_choice_count": sum(ranking[0] == candidate_id for ranking in rankings),
            "borda_points": sum(len(candidate_ids) - 1 - ranking.index(candidate_id) for ranking in rankings),
            "appeal_median": float(statistics.median(appeals)) if appeals else 0.0,
            "narrative_fit_median": float(statistics.median(fits)) if fits else 0.0,
            "want_to_play_median": float(statistics.median(wants)) if wants else 0.0,
            "readability_accuracy": round(correct / total_answers, 4) if total_answers else 0.0,
            "pairwise_preference": pairwise,
        }

    craft_eligible = _gate_pass_candidates(data)
    eligible = [
        candidate_id
        for candidate_id in craft_eligible
        if metrics[candidate_id]["readability_accuracy"] >= 0.75
    ]
    leader: str | None = None
    reasons: list[str] = []
    if len(eligible) >= 2:
        leader = sorted(
            eligible,
            key=lambda candidate_id: (
                -metrics[candidate_id]["borda_points"],
                -metrics[candidate_id]["first_choice_count"],
                -metrics[candidate_id]["appeal_median"],
                candidate_id,
            ),
        )[0]
    else:
        reasons.append("fewer than two candidates passed craft and 75% readability gates")
    if valid_count < 8:
        reasons.append(f"only {valid_count} valid responses; at least 8 are required")
    if test["round"] == 2 and test["cohort_type"] != "new":
        reasons.append("second-round evidence reused participants and is reference-only")
    if leader is not None:
        rival_rates = [
            metrics[leader]["pairwise_preference"][other]
            for other in eligible
            if other != leader
        ]
        if any(rate < 0.60 for rate in rival_rates):
            reasons.append("leader did not reach 60% pairwise preference against every rival")
        if metrics[leader]["appeal_median"] < 5:
            reasons.append("leader appeal median is below 5/7")
    result_status = "player_leader" if leader is not None and not reasons else "inconclusive"
    if result_status == "inconclusive" and not reasons:
        reasons.append("preference evidence is inconclusive")
    analysis = {
        "schema_version": "1.0",
        "test_id": test["id"],
        "test_round": test["round"],
        "cohort_type": test["cohort_type"],
        "input_response_count": len(response_paths),
        "valid_response_count": valid_count,
        "excluded_responses": excluded,
        "eligible_candidates": eligible,
        "candidate_metrics": metrics,
        "leader_candidate_id": leader,
        "result": result_status,
        "reasons": reasons,
        "response_hashes": response_hashes,
    }
    schema_errors = _schema_errors(analysis, ANALYSIS_SCHEMA)
    if schema_errors:
        raise ValueError("generated analysis is invalid: " + "; ".join(schema_errors))
    return analysis


def render_report(data: dict[str, Any], analysis: dict[str, Any] | None) -> str:
    brief = data["decision_brief"]
    creator = data["creator_decision"]
    lines = [
        f"# 《{brief['title']}》视觉方向决策报告",
        "",
        f"> 状态 **{data['status']}**。本报告区分制作质量门槛与玩家主观吸引力；不代表绝对美感或统计性市场结论。",
        "",
        "## 决策简报",
        "",
        f"- 目标玩家：{'；'.join(brief['target_players'])}",
        f"- 平台：{'；'.join(brief['target_platforms'])}",
        f"- 分辨率：{'；'.join(brief['target_resolutions'])}",
        f"- 镜头：{'；'.join(brief['camera_modes'])}",
        f"- 可读性目标：{brief['gameplay_readability_goal']}",
        f"- 生产预算：{brief['production_budget']}",
        "",
        "## 原作叙事功能硬门槛",
        "",
        "| ID | 功能 | 状态 | 证据 |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {item['id']} | {item['statement']} | {item['status']} | {item['evidence'] or '待补'} |"
        for item in data["source_functions"]
    )
    lines += ["", "## 同题候选", ""]
    for item in data["candidates"]:
        lines += [
            f"### {item['id']} · {item['name']}",
            "",
            item["hypothesis"],
            "",
            f"![{item['id']} 综合样板]({item['board_path']})",
            "",
            f"- 生成尝试：{item['generation_attempts']} / {data['benchmark']['max_generation_attempts']}",
            f"- Style anchor：{item['style_system']['style_anchor']}",
            "",
        ]
    lines += [
        "## 制作质量门槛",
        "",
        "| 候选 | 类别 | 结果 | 方法 | 可见证据 |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {gate['candidate_id']} | {gate['category']} | {gate['result']} | {gate['method']} | {gate['evidence'] or '待补'} |"
        for gate in data["craft_gates"]
    )
    lines += ["", "## 玩家盲测", ""]
    if analysis is None:
        lines.append("尚无可验证的玩家分析；不得声称玩家支持。")
    else:
        lines += [
            f"- 测试：{analysis['test_id']}，第 {analysis['test_round']} 轮",
            f"- 有效答卷：{analysis['valid_response_count']}；剔除：{len(analysis['excluded_responses'])}",
            f"- 结果：**{analysis['result']}**",
            "",
            "| 候选 | 第一选择 | 排序积分 | 吸引力中位数 | 叙事契合 | 游玩意愿 | 可读性 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for candidate_id, metrics in sorted(analysis["candidate_metrics"].items()):
            lines.append(
                f"| {candidate_id} | {metrics['first_choice_count']} | {metrics['borda_points']} | "
                f"{metrics['appeal_median']:.1f} | {metrics['narrative_fit_median']:.1f} | "
                f"{metrics['want_to_play_median']:.1f} | {metrics['readability_accuracy']:.0%} |"
            )
        lines += ["", "### 判断依据", ""]
        lines.extend(f"- {reason}" for reason in analysis["reasons"] or ["全部玩家支持阈值已满足。"])
    lines += [
        "",
        "## 推荐与创作者裁决",
        "",
        f"- 推荐状态：{data['recommendation']['status']}",
        f"- 推荐候选：{data['recommendation']['candidate_id'] or '无'}",
        f"- 创作者决定：{creator['status']}",
        f"- 最终候选：{creator['selected_candidate_id'] or '未决定'}",
        f"- 理由：{creator['rationale'] or '未填写'}",
        "",
        "## 证据边界",
        "",
        "- 玩家招募、目标画像匹配和知情同意由创作者负责。",
        "- 少量玩家结果只提供方向性证据，不代表市场规模或统计性成功概率。",
        "- 完整 Art Bible 是选型后的可选扩展；本报告的核心职责是证明选择过程。",
        "",
    ]
    return "\n".join(lines)


def export_style_contract(
    data: dict[str, Any],
    decision_path: Path,
    output_path: Path,
    analysis: dict[str, Any] | None,
    analysis_path: Path | None,
) -> dict[str, Any]:
    if data["status"] not in FINAL_STATUSES:
        raise ValueError("style contract requires a completed creator decision")
    validation = validate_decision(
        data, base_path=decision_path.parent, check_files=True, analysis=analysis
    )
    if validation.errors:
        raise ValueError("decision is not exportable: " + "; ".join(validation.errors))
    selected_id = data["creator_decision"]["selected_candidate_id"]
    selected = next(item for item in data["candidates"] if item["id"] == selected_id)
    style = selected["style_system"]
    contract = {
        "schema_version": "1.0",
        "contract_id": f"{data['decision_brief']['slug']}-style-r{data['metadata']['revision']:04d}",
        "revision": data["metadata"]["revision"],
        "project_slug": data["decision_brief"]["slug"],
        "decision_status": data["status"],
        "selected_candidate_id": selected_id,
        "reference_assets": [
            {
                "path": Path(os.path.relpath(decision_path.parent / selected["board_path"], output_path.parent)).as_posix(),
                "sha256": selected["board_sha256"],
                "role": "selected_composite_board",
            }
        ],
        "style_anchor": style["style_anchor"],
        "pixel_policy": style["pixel_policy"],
        "palette": style["palette"],
        "shape_language": style["shape_language"],
        "lighting": style["lighting"],
        "camera": style["camera"],
        "ui": style["ui"],
        "motion": style["motion"],
        "negative_rules": style["negative_rules"],
        "asset_overrides": style["asset_overrides"],
        "provenance": {
            "visual_decision": Path(os.path.relpath(decision_path, output_path.parent)).as_posix(),
            "visual_decision_sha256": _sha256(decision_path),
            "player_analysis": (
                Path(os.path.relpath(analysis_path, output_path.parent)).as_posix()
                if analysis_path is not None
                else None
            ),
            "player_analysis_sha256": _sha256(analysis_path) if analysis_path is not None else None,
        },
    }
    errors = _schema_errors(contract, CONTRACT_SCHEMA)
    if errors:
        raise ValueError("generated style contract is invalid: " + "; ".join(errors))
    return contract


def _print_validation(result: ValidationResult) -> int:
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate visual-decision.yaml")
    validate_parser.add_argument("decision", type=Path)
    validate_parser.add_argument("--check-files", action="store_true")
    validate_parser.add_argument("--analysis", type=Path)

    build_parser = subparsers.add_parser("build-test", help="build the offline blind-test page")
    build_parser.add_argument("decision", type=Path)
    build_parser.add_argument("--test-id", required=True)
    build_parser.add_argument("--output-dir", type=Path, required=True)

    analyze_parser = subparsers.add_parser("analyze", help="analyze exported anonymous responses")
    analyze_parser.add_argument("decision", type=Path)
    analyze_parser.add_argument("--test-id", required=True)
    analyze_parser.add_argument("--responses-dir", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)

    render_parser = subparsers.add_parser("render", help="render decision-report.md")
    render_parser.add_argument("decision", type=Path)
    render_parser.add_argument("--analysis", type=Path)
    render_parser.add_argument("--output-dir", type=Path, required=True)

    contract_parser = subparsers.add_parser("export-contract", help="export style-contract.yaml")
    contract_parser.add_argument("decision", type=Path)
    contract_parser.add_argument("--analysis", type=Path)
    contract_parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    try:
        data = load_yaml(args.decision)
        if args.command == "validate":
            analysis = load_json(args.analysis) if args.analysis else None
            result = validate_decision(
                data,
                base_path=args.decision.parent,
                check_files=args.check_files,
                analysis=analysis,
            )
            code = _print_validation(result)
            if code == 0:
                print(f"VALID: {args.decision}")
            return code

        if args.command == "build-test":
            result = validate_decision(data, base_path=args.decision.parent, check_files=True)
            if code := _print_validation(result):
                return code
            if data["status"] not in {
                "test_ready",
                "tested_inconclusive",
                "player_supported",
                "creator_selected_unvalidated",
                "creator_override",
            }:
                raise ValueError("blind-test page requires test_ready or a later status")
            test = _find_test(data, args.test_id)
            args.output_dir.mkdir(parents=True, exist_ok=True)
            output = args.output_dir / "index.html"
            output.write_text(
                build_test_page(data, test, args.decision.parent), encoding="utf-8"
            )
            print(f"WROTE: {output}")
            return 0

        if args.command == "analyze":
            result = validate_decision(data)
            if code := _print_validation(result):
                return code
            test = _find_test(data, args.test_id)
            paths = list(args.responses_dir.glob("*.json"))
            analysis = analyze_responses(data, test, paths)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"WROTE: {args.output}")
            return 0

        if args.command == "render":
            analysis = load_json(args.analysis) if args.analysis else None
            result = validate_decision(data, analysis=analysis)
            if code := _print_validation(result):
                return code
            args.output_dir.mkdir(parents=True, exist_ok=True)
            output = args.output_dir / "decision-report.md"
            output.write_text(render_report(data, analysis), encoding="utf-8")
            print(f"WROTE: {output}")
            return 0

        if args.command == "export-contract":
            analysis = load_json(args.analysis) if args.analysis else None
            contract = export_style_contract(
                data, args.decision, args.output, analysis, args.analysis
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                yaml.safe_dump(contract, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            print(f"WROTE: {args.output}")
            return 0
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "visual-decision"
FIXTURE = FIXTURE_DIR / "visual-decision.yaml"
sys.path.insert(0, str(SCRIPTS))

from visual_decision import (  # noqa: E402
    analyze_responses,
    build_test_page,
    export_style_contract,
    render_report,
    validate_decision,
)


def make_response(
    participant_id: str,
    *,
    ranking: list[str],
    appeal: dict[str, int] | None = None,
    correct: dict[str, bool] | None = None,
    target_match: bool = True,
    attention_passed: bool = True,
) -> dict:
    appeal = appeal or {"C-A": 6, "C-B": 5, "C-C": 4}
    correct = correct or {"C-A": True, "C-B": True, "C-C": True}
    expected = {"RT-001": "中央", "RT-002": "右上", "RT-003": "信件"}
    wrong = {"RT-001": "左侧", "RT-002": "左上", "RT-003": "铁门"}
    return {
        "schema_version": "1.0",
        "test_id": "TEST-001",
        "participant_id": participant_id,
        "submitted_at": "2026-08-22T12:00:00+08:00",
        "candidate_order": ["C-B", "C-A", "C-C"],
        "target_player_match": target_match,
        "attention_check_passed": attention_passed,
        "ranking": ranking,
        "responses": {
            candidate_id: {
                "ratings": {
                    "appeal": appeal[candidate_id],
                    "narrative_fit": 6 if candidate_id == "C-A" else 5,
                    "want_to_play": 6 if candidate_id == "C-A" else 4,
                },
                "readability_answers": expected if correct[candidate_id] else wrong,
                "comment": "匿名测试反馈",
            }
            for candidate_id in ("C-A", "C-B", "C-C")
        },
        "overall_comment": "按第一感受排序",
    }


class VisualDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
        self.test = self.data["player_tests"][0]

    def write_responses(self, directory: Path, payloads: list[dict]) -> list[Path]:
        paths = []
        for index, payload in enumerate(payloads, 1):
            path = directory / f"response-{index:02d}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            paths.append(path)
        return paths

    def clear_winner_payloads(self, count: int = 8) -> list[dict]:
        payloads = []
        for index in range(count):
            ranking = ["C-A", "C-B", "C-C"] if index < 6 else ["C-B", "C-A", "C-C"]
            payloads.append(make_response(f"participant-{index:02d}", ranking=ranking))
        return payloads

    def test_fixture_is_valid_and_files_match_hashes(self) -> None:
        result = validate_decision(self.data, base_path=FIXTURE_DIR, check_files=True)
        self.assertEqual([], result.errors)
        self.assertEqual({"C-A", "C-B", "C-C"}, {item["id"] for item in self.data["candidates"]})

    def test_forward_eval_corpus_covers_trigger_and_non_trigger_boundaries(self) -> None:
        corpus = yaml.safe_load((ROOT / "tests" / "forward-evals.yaml").read_text(encoding="utf-8"))
        cases = corpus["cases"]
        self.assertGreaterEqual(sum(item["should_trigger"] is True for item in cases), 5)
        self.assertGreaterEqual(sum(item["should_trigger"] is False for item in cases), 5)
        self.assertEqual(
            {"visual_decision", "production_spec"},
            {item["expected_mode"] for item in cases if item["should_trigger"]},
        )

    def test_every_candidate_requires_all_five_unique_gates(self) -> None:
        data = copy.deepcopy(self.data)
        data["craft_gates"] = data["craft_gates"][:-1]
        result = validate_decision(data)
        self.assertTrue(any("all three candidates" in item for item in result.errors))

        data = copy.deepcopy(self.data)
        data["craft_gates"][1]["category"] = "source_function"
        result = validate_decision(data)
        self.assertTrue(any("duplicate source_function" in item for item in result.errors))

    def test_test_ready_requires_source_functions_to_pass(self) -> None:
        data = copy.deepcopy(self.data)
        data["source_functions"][0]["status"] = "pending"
        result = validate_decision(data)
        self.assertTrue(any("source function" in item for item in result.errors))

    def test_no_more_than_two_candidates_may_be_revised(self) -> None:
        data = copy.deepcopy(self.data)
        for candidate in data["candidates"]:
            candidate["revision_round"] = 1
            candidate["derived_from"] = candidate["id"]
        result = validate_decision(data)
        self.assertTrue(any("at most two" in item for item in result.errors))

    def test_blind_test_page_is_offline_anonymous_and_randomized(self) -> None:
        page = build_test_page(self.data, self.test, FIXTURE_DIR)
        self.assertIn("Math.random", page)
        self.assertIn("button.disabled=index>0", page)
        self.assertIn("participant_id", page)
        self.assertIn("attention_check_passed", page)
        self.assertIn("data:image/svg+xml;base64", page)
        self.assertNotIn('"expected_answer"', page)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn('id="name"', page)
        self.assertNotIn('id="email"', page)

    def test_fewer_than_eight_responses_is_inconclusive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), self.clear_winner_payloads(7))
            analysis = analyze_responses(self.data, self.test, paths)
        self.assertEqual("inconclusive", analysis["result"])
        self.assertTrue(any("at least 8" in reason for reason in analysis["reasons"]))

    def test_invalid_and_duplicate_responses_are_excluded(self) -> None:
        payloads = self.clear_winner_payloads(8)
        payloads.append(make_response("participant-00", ranking=["C-A", "C-B", "C-C"]))
        payloads.append(
            make_response(
                "off-target",
                ranking=["C-A", "C-B", "C-C"],
                target_match=False,
            )
        )
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), payloads)
            analysis = analyze_responses(self.data, self.test, paths)
        self.assertEqual(8, analysis["valid_response_count"])
        self.assertEqual(2, len(analysis["excluded_responses"]))

    def test_clear_player_leader_uses_borda_pairwise_appeal_and_readability(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), self.clear_winner_payloads())
            analysis = analyze_responses(self.data, self.test, paths)
        self.assertEqual("player_leader", analysis["result"])
        self.assertEqual("C-A", analysis["leader_candidate_id"])
        self.assertEqual(0.75, analysis["candidate_metrics"]["C-A"]["pairwise_preference"]["C-B"])
        self.assertGreaterEqual(analysis["candidate_metrics"]["C-A"]["appeal_median"], 5)
        self.assertGreaterEqual(analysis["candidate_metrics"]["C-A"]["readability_accuracy"], 0.75)

    def test_preference_tie_is_inconclusive(self) -> None:
        rankings = [
            ["C-A", "C-B", "C-C"],
            ["C-A", "C-C", "C-B"],
            ["C-B", "C-A", "C-C"],
            ["C-B", "C-C", "C-A"],
            ["C-C", "C-A", "C-B"],
            ["C-C", "C-B", "C-A"],
            ["C-A", "C-B", "C-C"],
            ["C-B", "C-C", "C-A"],
        ]
        payloads = [make_response(f"tie-{index}", ranking=ranking) for index, ranking in enumerate(rankings)]
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), payloads)
            analysis = analyze_responses(self.data, self.test, paths)
        self.assertEqual("inconclusive", analysis["result"])
        self.assertTrue(any("60%" in reason for reason in analysis["reasons"]))

    def test_unreadable_preference_leader_is_not_eligible(self) -> None:
        payloads = [
            make_response(
                f"unreadable-{index}",
                ranking=["C-A", "C-B", "C-C"],
                correct={"C-A": False, "C-B": True, "C-C": True},
            )
            for index in range(8)
        ]
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), payloads)
            analysis = analyze_responses(self.data, self.test, paths)
        self.assertNotIn("C-A", analysis["eligible_candidates"])
        self.assertNotEqual("C-A", analysis["leader_candidate_id"])

    def test_second_round_reused_cohort_cannot_be_player_supported(self) -> None:
        data = copy.deepcopy(self.data)
        data["player_tests"][0]["round"] = 2
        data["player_tests"][0]["cohort_type"] = "reused"
        test = data["player_tests"][0]
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), self.clear_winner_payloads())
            analysis = analyze_responses(data, test, paths)
        self.assertEqual("inconclusive", analysis["result"])
        self.assertTrue(any("reference-only" in reason for reason in analysis["reasons"]))

    def _finalize(self, data: dict, analysis: dict, *, status: str, selected: str) -> None:
        data["status"] = status
        data["player_tests"][0].update(
            status="completed",
            response_paths=[
                f"player-test/responses/{filename}"
                for filename in sorted(analysis["response_hashes"])
            ],
            analysis_path="player-analysis.json",
        )
        data["recommendation"] = {
            "status": "player_leader",
            "candidate_id": analysis["leader_candidate_id"],
            "basis": ["8 份有效盲测答卷", "通过 60% 两两偏好阈值"],
        }
        data["creator_decision"] = {
            "status": (
                "accepted_player_leader" if status == "player_supported" else "overrode_player_leader"
            ),
            "selected_candidate_id": selected,
            "rationale": "接受玩家证据" if status == "player_supported" else "制作预算要求更低",
            "decided_at": "2026-08-22T18:00:00+08:00",
        }

    def test_player_supported_and_creator_override_states_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            paths = self.write_responses(Path(temp), self.clear_winner_payloads())
            analysis = analyze_responses(self.data, self.test, paths)
        supported = copy.deepcopy(self.data)
        self._finalize(supported, analysis, status="player_supported", selected="C-A")
        self.assertEqual([], validate_decision(supported, analysis=analysis).errors)
        tampered = copy.deepcopy(supported)
        tampered["player_tests"][0]["response_paths"] = tampered["player_tests"][0]["response_paths"][:-1]
        self.assertTrue(
            any("every hashed analysis input" in item for item in validate_decision(tampered, analysis=analysis).errors)
        )

        override = copy.deepcopy(self.data)
        self._finalize(override, analysis, status="creator_override", selected="C-B")
        self.assertEqual([], validate_decision(override, analysis=analysis).errors)

        override["creator_decision"]["selected_candidate_id"] = "C-A"
        self.assertTrue(any("different candidate" in item for item in validate_decision(override, analysis=analysis).errors))

    def test_style_contract_requires_decision_and_preserves_evidence_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            copied = temp_root / "project"
            shutil.copytree(FIXTURE_DIR, copied)
            decision_path = copied / "visual-decision.yaml"
            data = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
            response_dir = copied / "player-test" / "responses"
            response_dir.mkdir(parents=True)
            paths = self.write_responses(response_dir, self.clear_winner_payloads())
            analysis = analyze_responses(data, data["player_tests"][0], paths)
            analysis_path = copied / "player-analysis.json"
            analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "completed creator decision"):
                export_style_contract(data, decision_path, copied / "style-contract.yaml", analysis, analysis_path)

            self._finalize(data, analysis, status="player_supported", selected="C-A")
            decision_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            contract = export_style_contract(
                data, decision_path, copied / "style-contract.yaml", analysis, analysis_path
            )
        self.assertEqual("player_supported", contract["decision_status"])
        self.assertEqual("C-A", contract["selected_candidate_id"])
        self.assertFalse(Path(contract["reference_assets"][0]["path"]).is_absolute())
        self.assertEqual(64, len(contract["provenance"]["visual_decision_sha256"]))

    def test_report_never_claims_absolute_beauty(self) -> None:
        report = render_report(self.data, None)
        self.assertIn("不代表绝对美感", report)
        self.assertIn("不得声称玩家支持", report)

    def test_cli_build_test_and_legacy_renderer_remain_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "visual_decision.py"),
                    "build-test",
                    str(FIXTURE),
                    "--test-id",
                    "TEST-001",
                    "--output-dir",
                    temp,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertTrue((Path(temp) / "index.html").is_file())
            legacy = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_art_direction.py"),
                    str(ROOT / "tests" / "fixtures" / "fog-harbor.yaml"),
                    "--output-dir",
                    temp,
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, legacy.returncode, legacy.stdout + legacy.stderr)
            legacy_markdown = (Path(temp) / "art-direction.md").read_text(encoding="utf-8")
            self.assertIn("不表示经过目标玩家验证", legacy_markdown)

    def test_unified_cli_analyze_render_validate_and_export_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            shutil.copytree(FIXTURE_DIR, project)
            decision_path = project / "visual-decision.yaml"
            response_dir = project / "player-test" / "responses"
            response_dir.mkdir(parents=True)
            self.write_responses(response_dir, self.clear_winner_payloads())
            analysis_path = project / "player-analysis.json"

            analyze = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "visual_decision.py"),
                    "analyze",
                    str(decision_path),
                    "--test-id",
                    "TEST-001",
                    "--responses-dir",
                    str(response_dir),
                    "--output",
                    str(analysis_path),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, analyze.returncode, analyze.stdout + analyze.stderr)
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            data = yaml.safe_load(decision_path.read_text(encoding="utf-8"))
            self._finalize(data, analysis, status="player_supported", selected="C-A")
            decision_path.write_text(
                yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )

            commands = [
                [
                    "validate",
                    str(decision_path),
                    "--check-files",
                    "--analysis",
                    str(analysis_path),
                ],
                [
                    "render",
                    str(decision_path),
                    "--analysis",
                    str(analysis_path),
                    "--output-dir",
                    str(project),
                ],
                [
                    "export-contract",
                    str(decision_path),
                    "--analysis",
                    str(analysis_path),
                    "--output",
                    str(project / "style-contract.yaml"),
                ],
            ]
            for arguments in commands:
                completed = subprocess.run(
                    [sys.executable, str(SCRIPTS / "visual_decision.py"), *arguments],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            self.assertIn("player_supported", (project / "decision-report.md").read_text(encoding="utf-8"))
            contract = yaml.safe_load((project / "style-contract.yaml").read_text(encoding="utf-8"))
            self.assertEqual("C-A", contract["selected_candidate_id"])


if __name__ == "__main__":
    unittest.main()

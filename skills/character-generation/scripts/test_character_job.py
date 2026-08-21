#!/usr/bin/env python3
"""Regression tests for resumable character-generation job state."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from PIL import Image

import character_job as jobs


class CharacterJobTests(unittest.TestCase):
    def make_photo(self, root: Path, name: str = "codex-clipboard-1234.png") -> Path:
        path = root / name
        Image.new("RGB", (16, 16), (120, 80, 60)).save(path)
        return path

    def test_generic_photo_name_uses_timestamp_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            photo = self.make_photo(Path(temp))
            value = jobs.derive_character_id(photo, datetime(2026, 8, 21, 12, 34, 56))
            self.assertEqual(value, "character-20260821-123456")

    def test_semantic_photo_name_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            photo = self.make_photo(Path(temp), "Alice Zhang 正面照.png")
            self.assertEqual(jobs.derive_character_id(photo), "alice-zhang")

    def test_incomplete_job_resumes_without_storing_photo_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            photo = self.make_photo(root)
            first_dir, first, resumed = jobs.init_job(
                photo_path=photo,
                output_dir=root / "中文 输出",
                character_id="test-person",
            )
            second_dir, second, second_resumed = jobs.init_job(
                photo_path=photo,
                output_dir=root / "中文 输出",
                character_id="test-person",
            )
            self.assertFalse(resumed)
            self.assertTrue(second_resumed)
            self.assertEqual(first_dir, second_dir)
            self.assertEqual(first["photo_sha256"], second["photo_sha256"])
            state_text = (first_dir / "job.json").read_text(encoding="utf-8")
            self.assertNotIn(str(root), state_text)

    def test_explicit_different_character_id_does_not_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            photo = self.make_photo(root)
            first_dir, _, _ = jobs.init_job(
                photo_path=photo,
                output_dir=root / "output",
                character_id="first-person",
            )
            second_dir, _, resumed = jobs.init_job(
                photo_path=photo,
                output_dir=root / "output",
                character_id="second-person",
            )
            self.assertFalse(resumed)
            self.assertNotEqual(first_dir, second_dir)

    def test_record_preserves_source_and_versions_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            photo = self.make_photo(root)
            job_dir, _, _ = jobs.init_job(
                photo_path=photo,
                output_dir=root / "output",
                character_id="test-person",
            )
            generated = root / "generated.png"
            Image.new("RGBA", (32, 32), (20, 30, 40, 255)).save(generated)
            first = jobs.record_artifact(
                job_dir=job_dir, artifact="production-sheet", source_path=generated
            )
            second = jobs.record_artifact(
                job_dir=job_dir, artifact="production-sheet", source_path=generated
            )
            self.assertTrue(generated.is_file())
            self.assertNotEqual(first, second)
            payload = json.loads((job_dir / "job.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["attempts"]["production-sheet"], 2)
            self.assertEqual(payload["artifacts"]["production-sheet"], "masters/production-sheet-attempt-2.png")

    def test_completed_job_is_not_resumed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            photo = self.make_photo(root)
            output = root / "output"
            job_dir, _, _ = jobs.init_job(
                photo_path=photo,
                output_dir=output,
                character_id="test-person",
            )
            pack = output / "test-person"
            pack.mkdir(parents=True)
            (pack / "character.json").write_text("{}", encoding="utf-8")
            (pack / "qa-report.json").write_text("{}", encoding="utf-8")
            completed = jobs.complete_job(job_dir=job_dir, pack_dir=pack)
            self.assertEqual(completed["status"], "complete")

            next_dir, _, resumed = jobs.init_job(
                photo_path=photo,
                output_dir=output,
                character_id="test-person",
            )
            self.assertFalse(resumed)
            self.assertNotEqual(job_dir, next_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)

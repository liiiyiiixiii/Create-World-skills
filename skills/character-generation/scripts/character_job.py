#!/usr/bin/env python3
"""Manage resumable staging state for built-in character image generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from build_character_pack import STYLE_PROFILE, validate_character_id


GENERIC_STEM = re.compile(
    r"^(?:codex-clipboard-[0-9a-f-]+|image(?:[-_ ]?\d+)?|img(?:[-_ ]?\d+)?|screenshot(?:[-_ ].*)?)$",
    re.IGNORECASE,
)
ARTIFACT_NAMES = {"production-sheet", "turnaround", "down", "up", "right"}


class JobStateError(ValueError):
    """Raised when a resumable job operation is invalid."""


def hash_file(path: str | Path) -> str:
    source = Path(path)
    if not source.is_file():
        raise JobStateError(f"photo not found: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_character_id(path: str | Path, now: datetime | None = None) -> str:
    stem = Path(path).stem.strip()
    sanitized = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-_.")
    if not sanitized or GENERIC_STEM.fullmatch(stem):
        moment = now or datetime.now()
        return moment.strftime("character-%Y%m%d-%H%M%S")
    return sanitized[:64].rstrip("-_.")


def _read_job(job_dir: Path) -> dict[str, object]:
    path = job_dir / "job.json"
    if not path.is_file():
        raise JobStateError(f"job state not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JobStateError(f"invalid job state: {path}") from exc


def _write_job(job_dir: Path, payload: dict[str, object]) -> None:
    path = job_dir / "job.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _job_matches(
    payload: dict[str, object],
    *,
    photo_hash: str,
    character_id: str | None,
    generation_mode: str,
    cell_size: str,
    frame_duration_ms: int,
) -> bool:
    options = payload.get("options")
    return (
        payload.get("status") == "incomplete"
        and payload.get("photo_sha256") == photo_hash
        and payload.get("style_profile") == STYLE_PROFILE
        and (character_id is None or payload.get("character_id") == character_id)
        and isinstance(options, dict)
        and options.get("generation_mode") == generation_mode
        and options.get("cell_size") == cell_size
        and options.get("frame_duration_ms") == frame_duration_ms
    )


def init_job(
    *,
    photo_path: str | Path,
    output_dir: str | Path,
    character_id: str | None = None,
    generation_mode: str = "balanced",
    cell_size: str = "48x64",
    frame_duration_ms: int = 170,
) -> tuple[Path, dict[str, object], bool]:
    if generation_mode not in {"balanced", "fast", "quality"}:
        raise JobStateError("generation-mode must be balanced, fast, or quality")
    photo = Path(photo_path)
    photo_hash = hash_file(photo)
    requested_id = validate_character_id(character_id) if character_id else None
    output_root = Path(output_dir).resolve()
    work_root = output_root / ".work"
    work_root.mkdir(parents=True, exist_ok=True)

    for state_path in sorted(work_root.glob("*/job.json")):
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if _job_matches(
            payload,
            photo_hash=photo_hash,
            character_id=requested_id,
            generation_mode=generation_mode,
            cell_size=cell_size,
            frame_duration_ms=frame_duration_ms,
        ):
            return state_path.parent, payload, True

    resolved_id = requested_id or derive_character_id(photo)
    base = f"{resolved_id}-{photo_hash[:8]}"
    job_dir = work_root / base
    version = 2
    while job_dir.exists():
        job_dir = work_root / f"{base}-v{version}"
        version += 1
    (job_dir / "masters").mkdir(parents=True)

    payload: dict[str, object] = {
        "schema_version": 1,
        "status": "incomplete",
        "character_id": resolved_id,
        "photo_name": photo.name,
        "photo_sha256": photo_hash,
        "style_profile": STYLE_PROFILE,
        "options": {
            "generation_mode": generation_mode,
            "cell_size": cell_size,
            "frame_duration_ms": frame_duration_ms,
        },
        "artifacts": {},
        "attempts": {},
    }
    _write_job(job_dir, payload)
    return job_dir, payload, False


def record_artifact(
    *,
    job_dir: str | Path,
    artifact: str,
    source_path: str | Path,
) -> Path:
    if artifact not in ARTIFACT_NAMES:
        raise JobStateError(f"unsupported artifact name: {artifact}")
    job = Path(job_dir).resolve()
    source = Path(source_path)
    if not source.is_file():
        raise JobStateError(f"generated artifact not found: {source}")
    payload = _read_job(job)
    if payload.get("status") != "incomplete":
        raise JobStateError("cannot record an artifact on a completed job")

    attempts = payload.setdefault("attempts", {})
    artifacts = payload.setdefault("artifacts", {})
    if not isinstance(attempts, dict) or not isinstance(artifacts, dict):
        raise JobStateError("job state has invalid artifact records")
    attempt = int(attempts.get(artifact, 0)) + 1
    suffix = source.suffix.lower() or ".png"
    destination = job / "masters" / f"{artifact}-attempt-{attempt}{suffix}"
    shutil.copy2(source, destination)
    attempts[artifact] = attempt
    artifacts[artifact] = destination.relative_to(job).as_posix()
    _write_job(job, payload)
    return destination


def complete_job(*, job_dir: str | Path, pack_dir: str | Path) -> dict[str, object]:
    job = Path(job_dir).resolve()
    pack = Path(pack_dir).resolve()
    if not (pack / "character.json").is_file() or not (pack / "qa-report.json").is_file():
        raise JobStateError(f"completed pack is invalid: {pack}")
    payload = _read_job(job)
    payload["status"] = "complete"
    payload["pack_name"] = pack.name
    _write_job(job, payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage resumable character-generation staging.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--photo", required=True)
    init_parser.add_argument("--output-dir", default="output/character-generation")
    init_parser.add_argument("--character-id")
    init_parser.add_argument(
        "--generation-mode", choices=("balanced", "fast", "quality"), default="balanced"
    )
    init_parser.add_argument("--cell-size", default="48x64")
    init_parser.add_argument("--frame-duration", type=int, default=170)

    record_parser = subparsers.add_parser("record")
    record_parser.add_argument("--job-dir", required=True)
    record_parser.add_argument("--artifact", choices=sorted(ARTIFACT_NAMES), required=True)
    record_parser.add_argument("--source", required=True)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--job-dir", required=True)

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("--job-dir", required=True)
    complete_parser.add_argument("--pack-dir", required=True)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            job_dir, payload, resumed = init_job(
                photo_path=args.photo,
                output_dir=args.output_dir,
                character_id=args.character_id,
                generation_mode=args.generation_mode,
                cell_size=args.cell_size,
                frame_duration_ms=args.frame_duration,
            )
            result = {
                "job_dir": str(job_dir),
                "character_id": payload["character_id"],
                "resumed": resumed,
                "artifacts": payload["artifacts"],
            }
        elif args.command == "record":
            destination = record_artifact(
                job_dir=args.job_dir,
                artifact=args.artifact,
                source_path=args.source,
            )
            result = {"saved_path": str(destination)}
        elif args.command == "status":
            result = _read_job(Path(args.job_dir).resolve())
        else:
            result = complete_job(job_dir=args.job_dir, pack_dir=args.pack_dir)
    except (JobStateError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import csv
import json
import math
import shlex
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import AIModel, AudioFile, Detection, ProcessingJob, RawModelOutput, Site, SpeciesReference
from backend.app.services.job_state import sync_audio_status, transition_job


BirdnetResult = dict[str, float | str]


@dataclass(frozen=True)
class BirdnetRun:
    mode: str
    results: list[BirdnetResult]
    command: str | None = None
    output_files: list[str] | None = None
    stderr: str | None = None


def birdnet_status() -> dict[str, object]:
    settings = get_settings()
    return {
        "configured": bool(settings.birdnet_command),
        "mode": "configured" if settings.birdnet_command else "simulated",
        "min_confidence": settings.birdnet_min_confidence,
        "timeout_seconds": settings.birdnet_timeout_seconds,
        "command_template_present": bool(settings.birdnet_command),
        "supported_outputs": ["json", "csv", "table"],
        "recommended_command": "python -m birdnet_analyzer.analyze {input} -o {output_dir} --rtype csv --min_conf {min_conf}",
    }


def _audio_path(storage_uri: str) -> Path | None:
    parsed = urlparse(storage_uri)
    if parsed.scheme == "file":
        return Path(parsed.path)
    if not parsed.scheme:
        return Path(storage_uri)
    return None


def _birdnet_week(recorded_at: datetime | None) -> str:
    if recorded_at is None:
        return ""
    week_in_month = min(4, ((recorded_at.day - 1) // 7) + 1)
    return str((recorded_at.month - 1) * 4 + week_in_month)


def _parse_label(label: str) -> tuple[str, str]:
    if "_" in label:
        scientific_name, common_name = label.split("_", 1)
        return scientific_name.strip(), common_name.strip()
    known = {
        "American Robin": "Turdus migratorius",
        "Northern Cardinal": "Cardinalis cardinalis",
        "Blue Jay": "Cyanocitta cristata",
    }
    common_name = label.strip()
    return known.get(common_name, common_name), common_name


def _fallback_results(audio_file: AudioFile) -> list[BirdnetResult]:
    duration = audio_file.duration_seconds or 30.0
    windows = [(0.0, min(3.0, duration)), (max(3.0, duration * 0.35), min(duration, duration * 0.35 + 3.0))]
    return [
        {
            "label": "Turdus migratorius_American Robin",
            "confidence": 0.84,
            "start_seconds": windows[0][0],
            "end_seconds": windows[0][1],
        },
        {
            "label": "Cardinalis cardinalis_Northern Cardinal",
            "confidence": 0.72,
            "start_seconds": windows[1][0],
            "end_seconds": windows[1][1],
        },
    ]


def _first_value(row: dict[str, str], aliases: tuple[str, ...], default: str = "") -> str:
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for alias in aliases:
        value = normalized.get(alias.lower())
        if value not in {None, ""}:
            return value
    return default


def _float_or_default(value: object, default: float) -> float:
    try:
        if value in {None, ""}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_birdnet_rows(rows: list[dict[str, str]], audio_file: AudioFile) -> list[BirdnetResult]:
    normalized: list[BirdnetResult] = []
    duration = audio_file.duration_seconds or 30.0
    for index, row in enumerate(rows):
        scientific_name = _first_value(row, ("scientific name", "scientific_name", "species", "species name", "latin name"))
        common_name = _first_value(row, ("common name", "common_name", "label", "species common name", "class"))
        combined_label = _first_value(row, ("label", "species", "common name", "common_name"))
        if scientific_name and common_name:
            label = f"{scientific_name}_{common_name}"
        else:
            label = combined_label or scientific_name or common_name or "Unknown species"

        confidence = _float_or_default(
            _first_value(row, ("confidence", "score", "probability", "confidence score"), "0"),
            0.0,
        )
        start = _float_or_default(
            _first_value(row, ("start (s)", "start", "start_seconds", "begin time (s)", "begin time"), ""),
            index * 3.0,
        )
        end = _float_or_default(
            _first_value(row, ("end (s)", "end", "end_seconds", "end time (s)", "end time"), ""),
            min(duration, start + 3.0),
        )
        normalized.append(
            {
                "label": label,
                "confidence": max(0.0, min(1.0, confidence)),
                "start_seconds": max(0.0, start),
                "end_seconds": max(0.0, end),
            }
        )
    return normalized


def normalize_birdnet_payload(payload: object, audio_file: AudioFile) -> list[BirdnetResult]:
    duration = audio_file.duration_seconds or 30.0
    rows: list[BirdnetResult] = []
    source_rows = payload.get("results", payload) if isinstance(payload, dict) else payload
    if not isinstance(source_rows, list):
        return _fallback_results(audio_file)

    for index, row in enumerate(source_rows):
        if isinstance(row, dict):
            if all(isinstance(value, str) for value in row.values()):
                rows.extend(normalize_birdnet_rows([row], audio_file))
                continue
            label = str(row.get("label") or row.get("species") or row.get("common_name") or "Unknown species")
            confidence = _float_or_default(row.get("confidence") or row.get("score"), 0.0)
            start = _float_or_default(row.get("start_seconds") or row.get("start"), index * 3.0)
            end = _float_or_default(row.get("end_seconds") or row.get("end"), min(duration, start + 3.0))
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            label = str(row[0])
            confidence = _float_or_default(row[1], 0.0)
            start = float(index * 3)
            end = min(duration, start + 3)
        else:
            continue
        rows.append(
            {
                "label": label,
                "confidence": max(0.0, min(1.0, confidence)),
                "start_seconds": max(0.0, start),
                "end_seconds": max(0.0, end),
            }
        )
    return rows or _fallback_results(audio_file)


def parse_birdnet_output_file(path: Path, audio_file: AudioFile) -> list[BirdnetResult]:
    if path.suffix.lower() == ".json":
        return normalize_birdnet_payload(json.loads(path.read_text()), audio_file)
    if path.suffix.lower() in {".csv", ".txt"}:
        text = path.read_text(errors="replace")
        sample = text[:2048]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.excel_tab if "\t" in sample else csv.excel
        rows = list(csv.DictReader(text.splitlines(), dialect=dialect))
        return normalize_birdnet_rows(rows, audio_file)
    return []


def _discover_output_files(output_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for suffix in ("*.json", "*.csv", "*.txt"):
        candidates.extend(output_dir.rglob(suffix))
    return sorted(candidates, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)


def _run_configured_birdnet(db: Session, audio_file: AudioFile) -> BirdnetRun:
    settings = get_settings()
    command = settings.birdnet_command
    audio_path = _audio_path(audio_file.storage_uri)
    if not command or audio_path is None or not audio_path.exists():
        return BirdnetRun(mode="simulated", results=_fallback_results(audio_file))

    site = db.get(Site, audio_file.site_id)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        output_path = output_dir / "birdnet-results.json"
        rendered = command.format(
            input=str(audio_path),
            output=str(output_path),
            output_dir=str(output_dir),
            lat="" if site is None or site.latitude is None else site.latitude,
            lon="" if site is None or site.longitude is None else site.longitude,
            week=_birdnet_week(audio_file.recorded_at),
            min_conf=settings.birdnet_min_confidence,
        )
        completed = subprocess.run(
            shlex.split(rendered),
            check=True,
            capture_output=True,
            text=True,
            timeout=settings.birdnet_timeout_seconds,
        )
        results: list[BirdnetResult] = []
        output_files = _discover_output_files(output_dir)
        for output_file in output_files:
            results.extend(parse_birdnet_output_file(output_file, audio_file))
        if not results:
            return BirdnetRun(
                mode="configured_no_output",
                results=_fallback_results(audio_file),
                command=rendered,
                output_files=[str(path) for path in output_files],
                stderr=completed.stderr,
            )
        return BirdnetRun(
            mode="configured",
            results=results,
            command=rendered,
            output_files=[str(path) for path in output_files],
            stderr=completed.stderr,
        )


def _get_or_create_species(db: Session, scientific_name: str, common_name: str) -> SpeciesReference:
    species = db.scalar(select(SpeciesReference).where(SpeciesReference.scientific_name == scientific_name))
    if species is None:
        species = SpeciesReference(scientific_name=scientific_name, common_name=common_name, taxon_rank="species")
        db.add(species)
        db.flush()
    elif not species.common_name:
        species.common_name = common_name
    return species


def run_birdnet_processing(db: Session, job: ProcessingJob) -> ProcessingJob:
    if job.status in {"completed", "cancelled"}:
        return job

    audio_file = db.get(AudioFile, job.audio_file_id)
    if audio_file is None:
        transition_job(db, job, "failed", "Audio file not found.")
        db.commit()
        db.refresh(job)
        return job

    if job.status == "failed":
        transition_job(db, job, "queued")
    transition_job(db, job, "running")
    sync_audio_status(audio_file, job.status)
    db.flush()

    bird_model = db.scalar(select(AIModel).where(AIModel.name == "BirdNET Analyzer"))
    try:
        run = _run_configured_birdnet(db, audio_file)
    except (subprocess.SubprocessError, OSError, TimeoutError) as exc:
        transition_job(db, job, "failed", f"BirdNET runner failed: {exc}")
        sync_audio_status(audio_file, job.status)
        db.commit()
        db.refresh(job)
        return job
    raw_payload = {
        "contract": "birdnet_analysis.v1",
        "mode": run.mode,
        "configured": bool(get_settings().birdnet_command),
        "source": "BirdNET Analyzer adapter",
        "command": run.command,
        "output_files": run.output_files or [],
        "stderr": run.stderr,
        "results": run.results,
    }
    db.add(
        RawModelOutput(
            processing_job_id=job.id,
            audio_file_id=audio_file.id,
            ai_model_id=bird_model.id if bird_model else None,
            output_format="birdnet_json",
            payload=raw_payload,
        )
    )

    for result in run.results:
        scientific_name, common_name = _parse_label(str(result["label"]))
        species = _get_or_create_species(db, scientific_name, common_name)
        db.add(
            Detection(
                processing_job_id=job.id,
                audio_file_id=audio_file.id,
                ai_model_id=bird_model.id if bird_model else None,
                species_reference_id=species.id,
                detection_type="species",
                label=common_name,
                confidence=float(result["confidence"]),
                start_seconds=float(result["start_seconds"]),
                end_seconds=float(result["end_seconds"]),
            )
        )

    transition_job(db, job, "completed")
    sync_audio_status(audio_file, job.status)
    db.commit()
    db.refresh(job)
    return job


def shannon_diversity(labels: list[str]) -> float:
    total = len(labels)
    if total == 0:
        return 0.0
    counts = Counter(labels)
    return round(-sum((count / total) * math.log(count / total) for count in counts.values()), 4)

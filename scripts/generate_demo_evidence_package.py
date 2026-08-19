#!/usr/bin/env python3
"""Build a transparent demonstration evidence draft from a PCM WAV file.

The script records objective file metadata and a SHA-256 checksum. It never
creates species detections. Optional model candidates must be supplied from an
external result file and remain unreviewed in the generated package.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
import wave


DISCLAIMER = (
    "Demonstration evidence draft only. Automated model outputs are unreviewed "
    "candidates, not confirmed species observations. This package is not a "
    "TNFD or ESRS E4 disclosure, certification, assurance opinion, regulatory "
    "submission, or compliance determination."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_wav_metadata(path: Path) -> dict[str, int | float | str]:
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        sample_rate = audio.getframerate()
        return {
            "file_name": path.name,
            "sha256": sha256_file(path),
            "channels": audio.getnchannels(),
            "sample_width_bytes": audio.getsampwidth(),
            "sample_rate_hz": sample_rate,
            "frame_count": frames,
            "duration_seconds": round(frames / sample_rate, 3) if sample_rate else 0.0,
        }


def load_candidates(path: Path | None) -> list[dict[str, object]]:
    if path is None:
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("Candidate input must be a JSON array.")

    candidates: list[dict[str, object]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Candidate {index} must be a JSON object.")
        candidate = dict(item)
        candidate["review_status"] = "unreviewed"
        candidate["claim_status"] = "model_candidate_only"
        candidates.append(candidate)
    return candidates


def build_package(
    wav_path: Path,
    *,
    source_kind: str,
    candidates_path: Path | None = None,
) -> dict[str, object]:
    metadata = read_wav_metadata(wav_path)
    candidates = load_candidates(candidates_path)
    return {
        "schema_version": "listening.bio/evidence-draft/v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "demonstration_only": True,
        "source_kind": source_kind,
        "audio": metadata,
        "integrity_record": {
            "method": "SHA-256",
            "status": "checksum_recorded",
            "limitation": (
                "A checksum can detect a change to this exact file. It does not "
                "establish collection identity, custody, or authenticity by itself."
            ),
        },
        "model_candidates": candidates,
        "review": {
            "status": "not_started" if candidates else "not_applicable",
            "confirmed_observations": 0,
        },
        "framework_context": {
            "status": "reference_only",
            "references": ["TNFD recommendations and LEAP guidance", "ESRS E4"],
        },
        "disclaimer": DISCLAIMER,
    }


def render_html(package: dict[str, object]) -> str:
    audio = package["audio"]
    assert isinstance(audio, dict)
    rows = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value))}</td></tr>"
        for key, value in audio.items()
    )
    candidate_count = len(package["model_candidates"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Listening.bio demonstration evidence draft</title>
  <style>
    body {{ margin: 0; background: #07110f; color: #e8f3ee; font: 16px/1.55 system-ui, sans-serif; }}
    main {{ max-width: 860px; margin: auto; padding: 48px 24px 72px; }}
    .status {{ color: #f4cf65; font-weight: 700; text-transform: uppercase; }}
    h1 {{ font-size: clamp(2rem, 7vw, 4.5rem); line-height: 1; max-width: 10ch; }}
    .notice {{ border-left: 3px solid #f4cf65; background: #111d19; padding: 16px 18px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 32px; }}
    th, td {{ border-bottom: 1px solid #294039; padding: 10px 0; text-align: left; }}
    th {{ color: #9db8ae; width: 36%; font-weight: 500; }}
  </style>
</head>
<body><main>
  <p class="status">Demonstration only</p>
  <h1>Evidence draft</h1>
  <p class="notice">{html.escape(DISCLAIMER)}</p>
  <p><strong>Model candidates supplied:</strong> {candidate_count}. <strong>Confirmed observations:</strong> 0.</p>
  <table>{rows}</table>
</main></body>
</html>
"""


def write_package(
    wav_path: Path,
    output_dir: Path,
    *,
    source_kind: str,
    candidates_path: Path | None = None,
) -> tuple[Path, Path]:
    package = build_package(
        wav_path,
        source_kind=source_kind,
        candidates_path=candidates_path,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evidence-draft.json"
    html_path = output_dir / "evidence-draft.html"
    json_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(package), encoding="utf-8")
    return json_path, html_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path, help="PCM WAV recording")
    parser.add_argument("--output-dir", type=Path, default=Path("work/evidence-draft"))
    parser.add_argument(
        "--source-kind",
        choices=("public_data", "client_authorized", "field_pilot", "synthetic"),
        required=True,
    )
    parser.add_argument("--candidates", type=Path, help="Optional external model-candidate JSON array")
    args = parser.parse_args()
    json_path, html_path = write_package(
        args.wav,
        args.output_dir,
        source_kind=args.source_kind,
        candidates_path=args.candidates,
    )
    print(json_path)
    print(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


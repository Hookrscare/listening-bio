import hashlib
import json
from pathlib import Path
import struct
import wave

from scripts.generate_demo_evidence_package import DISCLAIMER, build_package, write_package


def _wav(path: Path) -> Path:
    samples = [0, 1200, -1200, 600] * 2000
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return path


def test_package_records_objective_wav_metadata_without_fabricating_detections(tmp_path):
    wav_path = _wav(tmp_path / "sample.wav")
    package = build_package(wav_path, source_kind="synthetic")

    assert package["demonstration_only"] is True
    assert package["model_candidates"] == []
    assert package["review"]["confirmed_observations"] == 0
    assert package["audio"]["sha256"] == hashlib.sha256(wav_path.read_bytes()).hexdigest()
    assert package["audio"]["duration_seconds"] == 1.0
    assert package["disclaimer"] == DISCLAIMER


def test_external_candidates_remain_unreviewed(tmp_path):
    wav_path = _wav(tmp_path / "sample.wav")
    candidates_path = tmp_path / "candidates.json"
    candidates_path.write_text(
        json.dumps([{"common_name": "American Robin", "confidence": 0.91}]),
        encoding="utf-8",
    )

    package = build_package(
        wav_path,
        source_kind="public_data",
        candidates_path=candidates_path,
    )

    candidate = package["model_candidates"][0]
    assert candidate["review_status"] == "unreviewed"
    assert candidate["claim_status"] == "model_candidate_only"
    assert package["review"]["confirmed_observations"] == 0


def test_generated_artifacts_do_not_use_false_assurance_language(tmp_path):
    wav_path = _wav(tmp_path / "sample.wav")
    json_path, html_path = write_package(
        wav_path,
        tmp_path / "out",
        source_kind="synthetic",
    )
    combined = (json_path.read_text() + html_path.read_text()).lower()

    for forbidden in (
        "tnfd compliant",
        "esrs e4 verified",
        "cryptographically_verified",
        "species presence certificate",
        "tamper-proof",
    ):
        assert forbidden not in combined


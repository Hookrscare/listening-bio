import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile

from backend.app.config import get_settings


ALLOWED_WAV_TYPES = {"audio/wav", "audio/x-wav", "audio/wave", "application/octet-stream"}


@dataclass(frozen=True)
class StoredAudio:
    file_name: str
    content_type: str
    storage_uri: str
    sha256: str
    bytes_written: int
    waveform_peaks: list[float] | None = None


def extract_waveform_peaks(content: bytes, sample_count: int = 100) -> list[float]:
    """Extract normalized peak amplitude array from WAV bytes for instantaneous frontend visual rendering."""
    if len(content) < 44 or not content.startswith(b"RIFF"):
        return [0.2] * sample_count

    try:
        # Find 'data' subchunk
        data_pos = content.find(b"data")
        if data_pos == -1 or len(content) <= data_pos + 8:
            raw_samples = content[44:]
        else:
            raw_samples = content[data_pos + 8:]

        if not raw_samples:
            return [0.2] * sample_count

        total_bytes = len(raw_samples)
        chunk_size = max(2, total_bytes // sample_count)
        peaks: list[float] = []

        for i in range(sample_count):
            start = i * chunk_size
            end = min(start + chunk_size, total_bytes)
            slice_bytes = raw_samples[start:end]
            if len(slice_bytes) >= 2:
                # Interpret as 16-bit signed PCM
                count_shorts = len(slice_bytes) // 2
                shorts = struct.unpack(f"<{count_shorts}h", slice_bytes[: count_shorts * 2])
                max_val = max(abs(s) for s in shorts) if shorts else 0
                normalized = round(min(1.0, max_val / 32768.0), 3)
                peaks.append(max(0.05, normalized))
            else:
                peaks.append(0.1)

        return peaks
    except Exception:
        return [0.25] * sample_count


async def save_uploaded_wav(file: UploadFile, site_id: str) -> StoredAudio:
    suffix = Path(file.filename or "").suffix.lower()
    content_type = file.content_type or "application/octet-stream"
    if suffix != ".wav" or content_type not in ALLOWED_WAV_TYPES:
        raise HTTPException(status_code=400, detail="Only WAV audio uploads are supported in this MVP slice.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded WAV file is empty.")
    if len(content) < 12 or not content.startswith(b"RIFF") or content[8:12] != b"WAVE":
        raise HTTPException(status_code=400, detail="Uploaded file does not look like a valid WAV container.")

    digest = hashlib.sha256(content).hexdigest()
    upload_root = Path(get_settings().upload_dir).expanduser().resolve()
    site_dir = upload_root / site_id
    site_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = Path(file.filename or "audio.wav").stem.replace(" ", "-")[:80] or "audio"
    target = site_dir / f"{digest[:16]}-{safe_stem}.wav"
    if not target.exists():
        target.write_bytes(content)

    peaks = extract_waveform_peaks(content, 100)

    return StoredAudio(
        file_name=file.filename or target.name,
        content_type=content_type if content_type != "application/octet-stream" else "audio/wav",
        storage_uri=target.as_uri(),
        sha256=digest,
        bytes_written=len(content),
        waveform_peaks=peaks,
    )

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

    import hashlib

    digest = hashlib.sha256(content).hexdigest()
    upload_root = Path(get_settings().upload_dir).expanduser().resolve()
    site_dir = upload_root / site_id
    site_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = Path(file.filename or "audio.wav").stem.replace(" ", "-")[:80] or "audio"
    target = site_dir / f"{digest[:16]}-{safe_stem}.wav"
    if not target.exists():
        target.write_bytes(content)

    return StoredAudio(
        file_name=file.filename or target.name,
        content_type=content_type if content_type != "application/octet-stream" else "audio/wav",
        storage_uri=target.as_uri(),
        sha256=digest,
        bytes_written=len(content),
    )

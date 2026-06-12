import math
import sys
import wave
from pathlib import Path


def create_sample_wav(path: Path, seconds: float = 6.0, sample_rate: int = 24_000, frequency: float = 220.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    amplitude = 8000
    frame_count = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for index in range(frame_count):
            # A quiet synthetic tone only verifies the runner path; use field audio for meaningful detections.
            value = int(amplitude * math.sin(2 * math.pi * frequency * index / sample_rate))
            wav.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def main() -> int:
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "work/sample-birdnet.wav")
    create_sample_wav(output)
    print(f"WAV sample written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

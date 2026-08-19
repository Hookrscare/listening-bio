import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


from dotenv import load_dotenv

load_dotenv()

RECOMMENDED_COMMAND = '"{python}" -m birdnet_analyzer.analyze {{input}} -o {{output_dir}} --rtype csv --min_conf {{min_conf}}'


def main() -> int:
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    spec = importlib.util.find_spec("birdnet_analyzer")
    if spec is None:
        print("BirdNET-Analyzer: not installed")
        print('Install with: .venv/bin/pip install -e ".[birdnet]"')
        return 1

    print("BirdNET-Analyzer: installed")
    recommended = RECOMMENDED_COMMAND.format(python=sys.executable)
    command = os.environ.get("BIRDNET_COMMAND", recommended)
    print(f"BIRDNET_COMMAND: {command}")
    executable = shlex.split(command)[0]
    if not Path(executable).exists() and shutil.which(executable) is None:
        print("Command executable is not on PATH.")
        return 1

    help_result = subprocess.run(
        [sys.executable, "-m", "birdnet_analyzer.analyze", "--help"],
        text=True,
        capture_output=True,
        timeout=90,
    )
    if help_result.returncode:
        print("BirdNET help command failed:")
        print((help_result.stderr or help_result.stdout).strip())
        return help_result.returncode

    first_line = (help_result.stdout or "").splitlines()[0] if help_result.stdout else "help output available"
    print(f"BirdNET CLI: {first_line}")
    print("Recommended app command:")
    print(f"export BIRDNET_COMMAND='{recommended}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import shutil
import subprocess
import sys


def main() -> int:
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version.split()[0]}")
    for command in ("git", "gh", "docker"):
        path = shutil.which(command)
        print(f"{command}: {path or 'not found'}")
    if shutil.which("git"):
        result = subprocess.run(["git", "--version"], text=True, capture_output=True)
        if result.returncode:
            print("git check failed:")
            print((result.stderr or result.stdout).strip())
        else:
            print(result.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


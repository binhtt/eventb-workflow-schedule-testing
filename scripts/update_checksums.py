#!/usr/bin/env python3
"""Refresh the repository checksum inventory after reviewing intended edits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {".git", "outputs", "__pycache__", ".venv", "venv"}


def main():
    inventory = {}
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if relative.as_posix() == "SOURCE_SHA256.json":
            continue
        inventory[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "SOURCE_SHA256.json").write_text(
        json.dumps(inventory, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Recorded {len(inventory)} file checksums.")


if __name__ == "__main__":
    main()

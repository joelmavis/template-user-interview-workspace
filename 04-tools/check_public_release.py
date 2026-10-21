#!/usr/bin/env python3
"""Check that this copy is safe to publish as a blank research template."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

PUBLIC_EXTENSIONS = {".md", ".csv", ".html", ".json"}
SENSITIVE = re.compile(r"\b(?:confidential|internal only|do not share|api[_ -]?key|access[_ -]?token|password|private[_ -]?key)\b", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.I)


def fail(message):
    raise ValueError(message)


def check_blank_workspace(root):
    workspace = root / "01-workspace"
    visible = [path for path in workspace.rglob("*") if path.name not in {".gitkeep", ".DS_Store"}]
    if visible:
        fail(f"Public template workspace is not blank: {visible[0].relative_to(root)}")


def scan_public_text(root):
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in PUBLIC_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SENSITIVE.search(text):
            fail(f"Potential sensitive text found in {path.relative_to(root)}")
        for match in EMAIL.finditer(text):
            domain = match.group(1).lower()
            if domain != "example.com" and not domain.endswith(".example.com"):
                fail(f"Potential private email found in {path.relative_to(root)}")


def git_status(root):
    if not (root / ".git").exists():
        return "Skipped — Not a Git Repository"
    result = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True)
    if result.returncode != 0:
        return "Skipped — Git status unavailable"
    return result.stdout.rstrip() or "clean"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        check_blank_workspace(root)
        scan_public_text(root)
    except (OSError, ValueError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 1
    print("OK Template Release Mode: blank user workspace and public text scan")
    print("Git status:", git_status(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Comprobación local para secretos comunes; no sustituye la revisión humana."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "logs",
    "test-results",
    "playwright-report",
}
PATTERNS = [
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{24,}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
]


def main():
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(p in SKIP for p in path.relative_to(ROOT).parts):
            continue
        if path.name == ".env":
            continue  # Se comprueba abajo si estuviera versionado.
        if path.stat().st_size > 1_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if any(p.search(content) for p in PATTERNS):
            findings.append(str(path.relative_to(ROOT)))
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, text=True, capture_output=True
    )
    if tracked.returncode == 0 and any(
        Path(p).name == ".env" for p in tracked.stdout.splitlines()
    ):
        findings.append(".env está versionado")
    for value in findings:
        print("REVISAR:", value, file=sys.stderr)
    print(f"Archivos con hallazgos: {len(findings)}")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())

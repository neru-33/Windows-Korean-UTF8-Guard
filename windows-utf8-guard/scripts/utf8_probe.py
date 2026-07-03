#!/usr/bin/env python3
from __future__ import annotations

import argparse
import locale
import os
import sys
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    "\N{REPLACEMENT CHARACTER}",
    "?뚰",
    "?꾩",
    "?섎",
    "?덈",
    "蹂묒",
    "怨듦",
    "吏",
    "媛",
    "移",
    "鍮",
    "遺",
    "洹쇨",
]

TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml",
    ".csv", ".tsv", ".html", ".css", ".js", ".ts", ".tsx", ".jsx",
}

DEFAULT_EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", "dist", "build",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose UTF-8 file bytes without trusting terminal rendering."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--all-text", action="store_true", help="Try every file, not only known text suffixes.")
    parser.add_argument("--exclude-dir", action="append", default=[], help="Directory name to skip.")
    parser.add_argument("--max-preview", type=int, default=120, help="Escaped preview length per finding.")
    return parser.parse_args()


def main() -> int:
    force_ascii_stdio()
    args = parse_args()
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    print_environment()

    files = list(iter_files(args.paths, exclude_dirs, args.all_text))
    findings = []
    ok = 0
    for file_path in files:
        result = inspect_file(file_path, args.max_preview)
        if result:
            findings.extend(result)
        else:
            ok += 1

    for message in findings:
        print(message)
    print(f"files={len(files)} utf8_ok_without_suspicious_patterns={ok} findings={len(findings)}")
    return 1 if findings else 0


def force_ascii_stdio() -> None:
    # ASCII with backslash escapes keeps diagnostic output readable even in broken consoles.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="ascii", errors="backslashreplace")


def print_environment() -> None:
    print(
        "env "
        f"stdout={sys.stdout.encoding!r} "
        f"stderr={sys.stderr.encoding!r} "
        f"preferred={locale.getpreferredencoding(False)!r} "
        f"PYTHONUTF8={os.environ.get('PYTHONUTF8')!r} "
        f"PYTHONIOENCODING={os.environ.get('PYTHONIOENCODING')!r}"
    )


def inspect_file(file_path: Path, max_preview: int) -> list[str]:
    try:
        data = file_path.read_bytes()
    except OSError as exc:
        return [f"{file_path}: read_error:{exc!r}"]

    bom = data.startswith(b"\xef\xbb\xbf")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return [f"{file_path}: utf8_decode_error:{exc!r} bytes={len(data)} bom_utf8={bom}"]

    findings = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        matched = [pattern for pattern in SUSPICIOUS_PATTERNS if pattern in line]
        if matched:
            preview = ascii(line.strip()[:max_preview])
            matched_preview = ",".join(ascii(pattern) for pattern in matched)
            findings.append(
                f"{file_path}:{line_no}: suspicious={matched_preview} "
                f"bytes={len(data)} bom_utf8={bom} preview={preview}"
            )
    return findings


def iter_files(paths: list[Path], exclude_dirs: set[str], all_text: bool):
    for path in paths:
        if path.is_file():
            if all_text or path.suffix.lower() in TEXT_SUFFIXES:
                yield path
            continue
        if not path.exists():
            print(f"{path}: missing")
            continue
        for child in path.rglob("*"):
            if child.is_dir():
                continue
            if any(part in exclude_dirs for part in child.parts):
                continue
            if all_text or child.suffix.lower() in TEXT_SUFFIXES:
                yield child


if __name__ == "__main__":
    raise SystemExit(main())

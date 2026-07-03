#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_PATTERNS = [
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
    parser = argparse.ArgumentParser(description="Scan text files for likely Windows/Korean mojibake.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--pattern", action="append", dest="patterns", help="Additional suspicious pattern.")
    parser.add_argument("--exclude-dir", action="append", default=[], help="Directory name to skip.")
    parser.add_argument("--all-text", action="store_true", help="Try every file, not only known text suffixes.")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    args = parse_args()
    patterns = [*DEFAULT_PATTERNS, *(args.patterns or [])]
    exclude_dirs = DEFAULT_EXCLUDE_DIRS | set(args.exclude_dir)
    findings = []
    for path in args.paths:
        for file_path in iter_files(path, exclude_dirs, args.all_text):
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                findings.append((file_path, 0, f"utf8_decode_error:{exc}"))
                continue
            except OSError as exc:
                findings.append((file_path, 0, f"read_error:{exc}"))
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                matched = [pattern for pattern in patterns if pattern in line]
                if matched:
                    preview = line.strip()[:180]
                    findings.append((file_path, line_no, f"patterns={matched} text={preview}"))
    for file_path, line_no, message in findings:
        location = f"{file_path}:{line_no}" if line_no else str(file_path)
        print(f"{location}: {message}")
    print(f"scanned_paths={len(args.paths)} findings={len(findings)}")
    return 1 if findings else 0


def iter_files(path: Path, exclude_dirs: set[str], all_text: bool):
    if path.is_file():
        if all_text or path.suffix.lower() in TEXT_SUFFIXES:
            yield path
        return
    if not path.exists():
        return
    for child in path.rglob("*"):
        if child.is_dir():
            continue
        if any(part in exclude_dirs for part in child.parts):
            continue
        if all_text or child.suffix.lower() in TEXT_SUFFIXES:
            yield child


if __name__ == "__main__":
    raise SystemExit(main())

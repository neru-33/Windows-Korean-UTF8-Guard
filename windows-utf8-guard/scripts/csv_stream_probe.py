#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stream a CSV and print an ASCII-safe UTF-8/BOM-aware summary."
    )
    parser.add_argument("path", type=Path)
    parser.add_argument("--encoding", default="utf-8-sig")
    parser.add_argument("--sample-rows", type=int, default=3)
    parser.add_argument("--max-preview", type=int, default=80)
    parser.add_argument("--delimiter", default=None)
    return parser.parse_args()


def main() -> int:
    force_ascii_stdio()
    args = parse_args()
    if not args.path.exists():
        print(f"missing path={args.path}")
        return 2

    try:
        return inspect_csv(args)
    except UnicodeDecodeError as exc:
        print(f"decode_error={exc!r}")
        return 1
    except csv.Error as exc:
        print(f"csv_error={exc!r}")
        return 1


def force_ascii_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="ascii", errors="backslashreplace")


def inspect_csv(args: argparse.Namespace) -> int:
    with args.path.open("r", encoding=args.encoding, newline="") as handle:
        if args.delimiter:
            reader = csv.DictReader(handle, delimiter=args.delimiter)
        else:
            sample = handle.read(65536)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
            except csv.Error:
                dialect = csv.excel
            reader = csv.DictReader(handle, dialect=dialect)

        fieldnames = reader.fieldnames or []
        empty_counts = Counter()
        suspicious_counts = Counter()
        samples = []
        rows = 0

        for row in reader:
            rows += 1
            if len(samples) < args.sample_rows:
                samples.append(row)
            for key in fieldnames:
                value = row.get(key)
                if value is None or value == "":
                    empty_counts[key] += 1
                    continue
                for pattern in SUSPICIOUS_PATTERNS:
                    if pattern in value:
                        suspicious_counts[key] += 1
                        break

    print(f"path={args.path}")
    print(f"encoding={args.encoding} rows={rows} columns={len(fieldnames)}")
    print("headers=" + ascii(fieldnames))
    if fieldnames:
        empty_preview = {
            key: empty_counts[key]
            for key in sorted(fieldnames, key=lambda item: empty_counts[item], reverse=True)[:10]
            if empty_counts[key]
        }
        suspicious_preview = {
            key: suspicious_counts[key]
            for key in sorted(fieldnames, key=lambda item: suspicious_counts[item], reverse=True)[:10]
            if suspicious_counts[key]
        }
        print("empty_counts_top=" + ascii(empty_preview))
        print("suspicious_counts_top=" + ascii(suspicious_preview))
    for index, row in enumerate(samples, start=1):
        clipped = {
            key: (value[: args.max_preview] if isinstance(value, str) else value)
            for key, value in row.items()
        }
        print(f"sample_{index}=" + ascii(clipped))
    return 1 if suspicious_counts else 0


if __name__ == "__main__":
    raise SystemExit(main())

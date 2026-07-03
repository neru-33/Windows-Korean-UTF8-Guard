---
name: windows-utf8-guard
description: Prevent Korean/non-ASCII UTF-8 mojibake and accidental text corruption on Windows. Use before reading or editing non-ASCII files, diagnosing garbled text such as "�", "?뚰", "蹂묒", "媛", or "吏", or passing Korean text through PowerShell, Get-Content, Python stdout, subprocess arguments, file paths, JSON, YAML, Markdown, source files, or large CSV output.
---

# Windows UTF-8 Guard

## Core Rule

Treat Windows shell output as untrusted for Korean/non-ASCII text. Distinguish terminal display mojibake from real file corruption before editing, and never copy garbled console text back into source, YAML, Markdown, JSON, tests, or fixtures.

Prefer UTF-8-aware file APIs over shell text pipelines. Use PowerShell as a last-mile command runner, not as the source of truth for file contents.

## Safe Workflow

1. Verify file bytes with a UTF-8-aware runtime before patching.
   - Prefer Python `Path.read_text(encoding="utf-8")` or Node `fs.readFileSync(path, "utf8")`.
   - For suspicious terminal output, run `scripts/utf8_probe.py <path>`; it prints escaped ASCII previews that survive broken consoles.

2. Decide whether corruption is real.
   - Real corruption appears in UTF-8-decoded text, often as `�`, `?뚰`, `?꾩`, `蹂묒`, `怨듦`, `吏`, `媛`, `移`, `鍮`, `遺`, or `洹쇨`.
   - Console-only corruption appears in PowerShell/cmd output but not in UTF-8 file reads.

3. Edit only after verification.
   - Write normal UTF-8 text directly.
   - Use `apply_patch` for source edits; then re-read with UTF-8 or run the mojibake scanner.
   - Prefer semantic assertions over exact Korean strings when the exact phrase is not essential.

4. Make diagnostic output encoding-safe.
   - In Python scripts that print Korean text, use `sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")`.
   - When the terminal itself is suspect, print `ascii()`, `repr()`, or JSON with `ensure_ascii=True`.
   - Use `json.dumps(..., ensure_ascii=False)` only when stdout is UTF-8-safe.

## Windows Failure Patterns

- **PowerShell display:** `Get-Content`, `Select-String`, `>`, `>>`, and `Out-File` can misread, misrender, or rewrite non-ASCII text depending on PowerShell version, code page, BOM, and profile settings. Verify with Python/Node before acting on what the terminal shows.
- **Python stdout:** A script may read UTF-8 correctly but fail with CP949 `UnicodeEncodeError` when printing. Reconfigure stdout or escape diagnostics.
- **CLI arguments:** Korean text passed through PowerShell here-strings, inline scripts, or command arguments can arrive as `???`. For batch tests, build Korean strings inside Python, read them from UTF-8 files/JSON, or pass UTF-8 stdin from a trusted runtime.
- **Non-ASCII paths:** If a hard-coded Korean path appears missing, search from an ASCII-safe parent by filename, then operate on the discovered `Path` object. Print paths with `repr()` or `ascii(str(path))` when debugging.
- **Large CSVs:** Do not dump large CSVs through PowerShell. Stream with Python `csv.DictReader`, use `encoding="utf-8-sig"` for CSV exports, and print bounded ASCII-safe summaries. Use `scripts/csv_stream_probe.py <csv-path>` when useful.
- **Inline regex/scripts:** Avoid complex regex-heavy Python embedded in PowerShell when escaping or encoding is already suspect. Put the script in a `.py` file or verify patterns with `ascii(pattern)`.

## PowerShell Fallback

Prefer `pwsh` over Windows PowerShell 5.1 when PowerShell is unavoidable. Session settings can reduce failures but do not replace file-level verification:

```powershell
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
```

These settings are session-scoped unless placed in a profile. Do not rely on a user's profile for repo scripts or tests; set encoding inside the script or use Python/Node file APIs.

## Bundled Tools

- `scripts/check_mojibake.py <path>`: scan text files for common Korean mojibake patterns.
- `scripts/utf8_probe.py <path>`: diagnose UTF-8 bytes with ASCII-safe previews.
- `scripts/csv_stream_probe.py <csv-path>`: stream large CSVs and print bounded ASCII-safe summaries.

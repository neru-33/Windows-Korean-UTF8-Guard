# Windows Korean UTF-8 Guard

Windows + PowerShell/cmd 환경에서 한글/비 ASCII 텍스트를 다룰 때 생기는 UTF-8 깨짐, 잘못된 파일 수정, 콘솔 출력 오판을 줄이기 위한 Codex 스킬입니다.

WSL, Linux, macOS, bash처럼 UTF-8 처리가 안정적인 환경에서는 기본적으로 사용할 필요가 없습니다. 이 스킬은 Windows 네이티브 셸이나 Windows 앱/export를 경유하면서 깨짐이 실제로 보일 때 쓰는 opt-in guard입니다.

이 스킬은 다음 상황에서 사용하도록 설계되었습니다.

- PowerShell `Get-Content`, `Select-String`, 리다이렉션 출력에서 한글이 깨져 보일 때
- 파일은 UTF-8인데 Python stdout이 CP949라 `UnicodeEncodeError`가 날 때
- 한글 CLI 인자, 한글 경로, here-string, inline Python을 거치며 문자열이 `???`로 바뀔 때
- 대용량 CSV를 콘솔에 직접 출력하지 않고 안전하게 요약해야 할 때
- 깨진 콘솔 문자열을 소스/YAML/Markdown/JSON에 다시 써서 실제 파일을 오염시키는 일을 막고 싶을 때

## 구성

```text
windows-utf8-guard/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    ├── check_mojibake.py
    ├── csv_stream_probe.py
    └── utf8_probe.py
```

배포 대상은 위 `windows-utf8-guard` 폴더입니다. `README.md`와 `LICENSE`는 GitHub 저장소 설명용 파일입니다.

## 설치

### 1. 저장소 클론

```powershell
git clone https://github.com/neru-33/Windows-Korean-UTF8-Guard.git
cd Windows-Korean-UTF8-Guard
```

### 2. Codex 스킬 폴더로 복사

`CODEX_HOME`을 쓰고 있다면 해당 경로의 `skills` 폴더에 설치하고, 아니면 기본값인 `%USERPROFILE%\.codex\skills`에 설치합니다.

```powershell
$skillRoot = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME "skills"
} else {
    Join-Path $env:USERPROFILE ".codex\skills"
}

New-Item -ItemType Directory -Force -Path $skillRoot
Copy-Item -Recurse -Force ".\windows-utf8-guard" $skillRoot
```

설치 후 새 Codex 세션에서 `$windows-utf8-guard`를 사용할 수 있습니다. 일반 WSL/bash 작업에서는 자동으로 쓰기보다, Windows PowerShell/cmd 인코딩 문제가 의심될 때 명시적으로 호출하는 용도를 권장합니다.

## 사용법

Codex에게 한글 파일, Windows 인코딩, PowerShell 출력 깨짐, CSV 깨짐 등을 다루게 할 때 다음처럼 요청합니다.

```text
Use $windows-utf8-guard to diagnose this Korean text that broke in Windows PowerShell.
```

또는 한국어로 요청해도 됩니다.

```text
$windows-utf8-guard를 사용해서 이 한글 Markdown 파일이 실제로 깨진 건지 확인해줘.
```

## 포함된 도구

### `check_mojibake.py`

텍스트 파일에서 흔한 한글 mojibake 패턴을 찾습니다.

```powershell
python .\windows-utf8-guard\scripts\check_mojibake.py .\path\to\project
```

### `utf8_probe.py`

PowerShell 콘솔 출력이 깨지는 상황에서도 파일 바이트와 UTF-8 디코딩 상태를 ASCII-safe 출력으로 진단합니다.

```powershell
python .\windows-utf8-guard\scripts\utf8_probe.py .\path\to\file.md
```

### `csv_stream_probe.py`

대용량 CSV를 전체 출력하지 않고, 헤더/행 수/빈값/샘플/mojibake 의심 컬럼만 스트리밍으로 요약합니다. CSV는 기본적으로 `utf-8-sig`로 읽습니다.

```powershell
python .\windows-utf8-guard\scripts\csv_stream_probe.py .\path\to\data.csv
```

## 핵심 원칙

PowerShell 화면 출력은 한글 파일 내용의 진실 공급원이 아닙니다. 파일이 실제로 깨졌는지 판단하기 전에 Python/Node 같은 UTF-8-aware 파일 API로 확인하세요.

깨진 콘솔 문자열을 그대로 복사해서 소스, YAML, Markdown, JSON, 테스트 fixture에 넣지 마세요. 실제 파일 오염으로 이어질 수 있습니다.

## 요구 사항

- Codex 스킬로 사용할 경우: Codex가 로드할 수 있는 `skills` 디렉터리
- 스크립트 실행: Python 3.9 이상 권장
- 외부 Python 패키지 없음

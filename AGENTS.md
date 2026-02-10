# AGENTS.md

## Purpose
This repository has had repeated technical issues caused by encoding mismatches, partial command approvals, and interrupted turns. Follow this guide strictly before creating or modifying files.

## 1) Language and Encoding (Mandatory)
- Write all Korean text in `UTF-8`.
- Default file encoding: `UTF-8` (without BOM preferred).
- Never assume terminal rendering means file is broken. Verify bytes when needed.
- Do not convert files to CP949/EUC-KR unless explicitly requested.

## 2) PowerShell Output/Input Rules (Mandatory)
Before reading Korean text in PowerShell, set:

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8
```

When writing files, always specify encoding:

```powershell
Set-Content -Path <path> -Value <content> -Encoding UTF8
```

For append:

```powershell
Add-Content -Path <path> -Value <content> -Encoding UTF8
```

## 3) Pre-Write Checklist
Before creating/editing files:
1. Confirm exact target path exists/is intended.
2. Confirm scope from user request (do not create extra files).
3. In read-only sandbox, request escalation once with clear justification.
4. If turn was aborted, re-check filesystem state before retry.

## 4) Post-Write Verification
After writing a file:
1. Verify file exists and size > 0.
2. Read first lines with UTF-8 output setting.
3. If Korean text looks broken, verify raw bytes (BOM/UTF-8) before rewriting.
4. Report created/updated paths explicitly.

## 5) Scope Control
- If user asks for one file, create only that file.
- Do not implement additional code or docs unless requested.
- Prefer minimal, deterministic changes.

## 6) Command Safety and Interruptions
- If a command is rejected/aborted, assume partial state is possible.
- Re-run only after checking current state.
- Never use destructive git/file commands unless explicitly requested.
- For investigative reads (read operations), run a single command first; use parallel reads only after at least one successful single read.
- If a parallel read is rejected, immediately retry the same target as one single command.
- After a user interruption, avoid parallel execution on first retry; do one state-check command, then continue.

## 7) Document Quality Gate
For planning documents (`masterplan`, `plan`, etc.):
- Include clear objective, scope, assumptions, interfaces, tests, risks.
- Use actionable, implementation-ready wording.
- Keep section titles stable and scan-friendly.

## 8) Recommended Quick Checks
```powershell
# 1) Path exists?
Test-Path <path>

# 2) UTF-8 read
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8; Get-Content <path>

# 3) First bytes (BOM check)
[byte[]]$b=[IO.File]::ReadAllBytes('<path>'); $b[0..3]
```

## 9) Default Assumptions for This Repo
- Primary language for docs: Korean.
- Primary encoding: UTF-8.
- Priority: prevent encoding corruption and accidental scope expansion.

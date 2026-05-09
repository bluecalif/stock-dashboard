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

## 2.1) Codex/PowerShell Korean Rendering Exception (Mandatory)
- This repo's docs may display as mojibake in Codex/PowerShell even when the file itself is valid UTF-8.
- Do **not** conclude that a document is corrupted only because terminal output looks broken.
- Treat repository documents as authoritative unless raw-byte verification proves the file is actually damaged.
- If Korean looks broken in terminal output, do this before raising an encoding issue:
  1. Verify BOM/bytes with `[IO.File]::ReadAllBytes(...)`.
  2. Re-read with UTF-8 assumptions.
  3. If needed, inspect via a non-profile path or byte-based fallback before claiming corruption.
- Do not spend time "fixing" docs, frontend labels, or lint findings that only appear broken because of this PowerShell/Codex rendering problem unless the user explicitly asks for actual encoding repair.
- When reviewing project status, record this as an environment/tooling limitation, not as a document defect, unless byte verification contradicts that assumption.

## 2.2) Session Restart Rule
- At the start of a new session, assume:
  - docs are intended to be valid UTF-8,
  - Korean mojibake in PowerShell/Codex is a known reader-side issue,
  - repeated re-diagnosis of the same symptom is wasteful unless raw bytes indicate real corruption.
- If `silver-session-summary.md` or similar planning docs look broken in terminal output, continue the review by using structure, file references, and byte checks rather than escalating the doc itself as a project problem.

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
- Known limitation: Codex/PowerShell may misrender Korean while files remain valid.

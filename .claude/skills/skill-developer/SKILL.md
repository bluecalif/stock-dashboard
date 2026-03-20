---
name: skill-developer
description: Claude Code 스킬 생성 및 관리 가이드. 새 스킬 추가, skill-rules.json 수정, 트리거 패턴 설계, hook 메커니즘 이해, 스킬 활성화 디버깅 시 사용. 키워드 트리거, intent 패턴, enforcement 레벨(block, suggest, warn), UserPromptSubmit hook, PostToolUse hook, 500라인 규칙, progressive disclosure 패턴 포함.
---

# Skill Developer Guide

## 목적

Stock Dashboard 프로젝트의 스킬 시스템을 생성하고 관리하기 위한 가이드.

## 사용 시점

- 새 스킬 생성/추가
- skill-rules.json 수정
- 트리거 패턴 설계/디버깅
- hook 시스템 이해 및 에러 해결

---

## 시스템 개요

### 아키텍처

```
.claude/
├── hooks/
│   ├── skill-activation-prompt.ps1   # PowerShell wrapper (Windows)
│   ├── skill-activation-prompt.ts    # UserPromptSubmit 메인 로직
│   └── post-tool-use-tracker.ps1     # PostToolUse: 편집 파일 추적
├── settings.json                     # Hook 등록
└── skills/
    ├── skill-rules.json              # 스킬 정의 (마스터 설정)
    └── {skill-name}/
        └── SKILL.md                  # 스킬 콘텐츠
```

### Hook 동작 흐름

```
User Prompt → settings.json → PowerShell Wrapper → TypeScript Hook
                                                        ↓
                                              skill-rules.json 로드
                                                        ↓
                                              키워드/패턴 매칭
                                                        ↓
                                              매칭된 스킬 출력 (stdout → Claude)
```

### 현재 등록된 스킬

| 스킬 | 타입 | 적용 | 우선순위 |
|------|------|------|----------|
| backend-dev | domain | suggest | high |
| frontend-dev | domain | suggest | high |
| langgraph-dev | domain | suggest | high |
| skill-developer | domain | suggest | medium |

---

## 새 스킬 생성 (Quick Start)

### Step 1: 스킬 파일 생성

**위치:** `.claude/skills/{skill-name}/SKILL.md`

```markdown
---
name: my-skill-name
description: 스킬 설명. 트리거 키워드를 포함해야 함. 최대 1024자.
---

# 스킬 이름

## 목적
## 사용 시점
## 핵심 정보
```

### Step 2: skill-rules.json에 추가

```json
{
  "my-skill-name": {
    "type": "domain",
    "enforcement": "suggest",
    "priority": "medium",
    "promptTriggers": {
      "keywords": ["키워드1", "keyword2"],
      "intentPatterns": ["(생성|추가).*무엇"]
    }
  }
}
```

### Step 3: 테스트

```bash
echo '{"session_id":"test","prompt":"테스트 키워드1"}' | \
  npx tsx .claude/hooks/skill-activation-prompt.ts
```

### Step 4: 패턴 개선

- 누락된 키워드 추가
- false positive 줄이도록 intent 패턴 조정
- 한글/영문 키워드 균형 맞춤

---

## 스킬 타입 & Enforcement

| 타입 | 목적 | enforcement | 예시 |
|------|------|-------------|------|
| guardrail | 핵심 규칙 강제 | warn / block | 데이터 무결성, 아키텍처 계약 |
| domain | 영역별 가이드 제공 | suggest | backend-dev, frontend-dev |

| Enforcement | 동작 | 사용 시점 |
|-------------|------|-----------|
| block | Exit code 2, 진행 차단 | 치명적 실수 방지 |
| suggest | 리마인더 주입, 강제 아님 | 가장 일반적 |
| warn | 낮은 우선순위 제안 | 정보성 |

---

## 트리거 타입

### Keywords (명시적 주제)

```json
"keywords": ["collector", "수집기", "FDR", "FastAPI"]
```

- 대소문자 무시 (hook에서 lowercase 변환)
- 한글+영문 모두 포함
- 너무 일반적인 단어 피하기 (예: "data", "코드")

### Intent Patterns (암시적 행동)

```json
"intentPatterns": ["(생성|구현).*수집.*collector", "(create|add).*endpoint"]
```

- 정규식 사용, `.*`로 유연 매칭
- 너무 느슨하면 false positive 증가

---

## Hook 에러 해결 가이드

### 증상: `UserPromptSubmit hook error` / `PostToolUse hook error`

Claude Code가 hook 실행 후 **exit code != 0** 또는 **stderr 출력**을 감지하면 에러로 표시. 채팅 흐름에는 영향 없지만 노이즈.

### 원인과 해결

#### 1. PowerShell wrapper 경로 문제

**증상:** `Cannot find module` 에러

**원인:** `$env:CLAUDE_PROJECT_DIR`이 빈 값일 때 잘못된 경로로 이동

**해결:** `$PSScriptRoot` 사용 (스크립트 자체 위치 기준)

```powershell
# BAD — 환경변수 미설정 시 C:\.claude\hooks로 이동
Push-Location "$env:CLAUDE_PROJECT_DIR\.claude\hooks"

# GOOD — 스크립트 파일 위치 기준
Push-Location $PSScriptRoot
```

#### 2. ErrorActionPreference 설정

**증상:** 사소한 에러에도 hook error 표시

**원인:** `$ErrorActionPreference = "Stop"` → 어떤 에러든 즉시 throw

**해결:** `SilentlyContinue` + try/catch + `exit 0` 보장

```powershell
$ErrorActionPreference = "SilentlyContinue"

try {
    # hook 로직
} catch {
    # 조용히 종료
} finally {
    Pop-Location
}
exit 0
```

#### 3. TypeScript exit code

**증상:** TS 스크립트 에러 시 `process.exit(1)` → hook error

**해결:** catch에서 `process.exit(0)` 사용

```typescript
} catch (err) {
    if (process.env.DEBUG_HOOKS) {
        console.error('Hook error:', err);
    }
    process.exit(0);  // NOT exit(1)
}
```

#### 4. stdin JSON 파싱 실패

**증상:** `ConvertFrom-Json` 에러 (빈 입력, BOM 포함 등)

**해결 (PowerShell):** try/catch 래핑 + null 체크

```powershell
try {
    $toolInfo = $input | Out-String | ConvertFrom-Json
} catch {
    exit 0
}
if (-not $toolInfo) { exit 0 }
```

**해결 (TypeScript):** BOM strip

```typescript
const raw = readFileSync(0, 'utf-8');
const input = raw.replace(/^\uFEFF/, '');
const data = JSON.parse(input);
```

### Hook 에러 핵심 원칙

> **Hook은 절대 채팅을 방해하면 안 된다.**
> 에러 시 조용히 `exit 0`. 디버깅이 필요하면 `DEBUG_HOOKS=1` 환경변수로 stderr 출력.

### 디버깅 방법

```bash
# 수동 테스트 (UserPromptSubmit)
echo '{"session_id":"test","prompt":"hello"}' | \
  powershell.exe -ExecutionPolicy Bypass -File .claude/hooks/skill-activation-prompt.ps1

# 수동 테스트 (PostToolUse)
echo '{"tool_name":"Edit","tool_input":{"file_path":"test.py"}}' | \
  powershell.exe -ExecutionPolicy Bypass -File .claude/hooks/post-tool-use-tracker.ps1

# DEBUG 모드
DEBUG_HOOKS=1 echo '...' | npx tsx .claude/hooks/skill-activation-prompt.ts
```

---

## 테스트 체크리스트

- [ ] `.claude/skills/{name}/SKILL.md` 생성 (frontmatter 포함)
- [ ] `skill-rules.json`에 항목 추가
- [ ] 키워드 테스트 통과 (한글/영문)
- [ ] Intent 패턴 테스트 통과
- [ ] false positive / false negative 없음
- [ ] SKILL.md 500라인 미만

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `.claude/skills/skill-rules.json` | 마스터 설정 |
| `.claude/settings.json` | Hook 등록 |
| `.claude/hooks/skill-activation-prompt.ps1` | UserPromptSubmit wrapper |
| `.claude/hooks/skill-activation-prompt.ts` | UserPromptSubmit 로직 |
| `.claude/hooks/post-tool-use-tracker.ps1` | PostToolUse: 편집 추적 |

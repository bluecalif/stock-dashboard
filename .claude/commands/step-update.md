---
description: Step 완료 → Phase docs + project-overall 동시 업데이트 → Git commit
argument-hint: phase-name step-number (예: "phase4-api 4.3")
---

# 단계 업데이트 (Step Update)

**Task:** $ARGUMENTS

## Overview

개발 단계(step) 완료 시 실행. Phase 문서와 project-overall 문서를 **동시에** 업데이트한 뒤 커밋.

```
Phase docs 업데이트 + project-overall 동기화 → Git Commit
```

---

## Instructions

### 1. 인자 파싱 (Parse Arguments)

입력 형식: `[phase-name] [step-id]`

예시:
- `phase4-api 4.3` → Phase 4, Step 3
- `phase5-frontend 5.6` → Phase 5, Step 6

### 2. 현재 상태 확인 (Check Current State)

읽어야 할 파일 (전부 읽기):
```
dev/active/[phase-name]/[phase-name]-tasks.md
dev/active/[phase-name]/[phase-name]-context.md
dev/active/[phase-name]/[phase-name]-plan.md
dev/active/project-overall/project-overall-tasks.md
dev/active/project-overall/project-overall-plan.md
dev/active/project-overall/project-overall-context.md
docs/session-compact.md
```

확인 사항:
- [ ] Phase dev-docs 파일 존재 여부 (없으면 `/dev-docs` 먼저 실행 안내)
- [ ] 현재 브랜치, 커밋되지 않은 변경사항
- [ ] 완료된 step의 실제 코드 변경 내역 (`git diff --stat`)

### 3. Phase Dev-Docs 업데이트

#### 3.1 `[phase-name]-tasks.md`
- 완료된 step 체크: `- [ ]` → `- [x]` + commit hash
- Progress 카운터 갱신 (예: `3/14 (21%)`)
```markdown
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `abc1234`
```

#### 3.2 `[phase-name]-context.md`
- 변경/생성된 파일 목록 추가
- 새 결정사항 추가 (있을 경우)
```markdown
## Changed Files (Step 4.3)
- `api/repositories/price_repo.py` — 신규 생성
- `api/repositories/base.py` — 신규 생성
```

#### 3.3 `[phase-name]-plan.md`
- Last Updated 날짜 갱신
- Status / Current Step 갱신
- Current State 섹션에 완료 항목 추가

### 4. project-overall 동기화 (CRITICAL — 반드시 수행)

#### 4.1 `project-overall-tasks.md`
- 해당 Phase의 동일 step을 체크: `- [ ]` → `- [x]` + commit hash
- Phase tasks.md와 **정확히 동일한 상태** 유지
- Summary 섹션 갱신 (완료 태스크 수)

#### 4.2 `project-overall-plan.md`
- Current State 섹션 갱신 (진행률 업데이트)
- 해당 Phase 설명이 실제 구현과 일치하는지 확인

#### 4.3 `project-overall-context.md`
- 새 결정사항 → 주요 결정사항 테이블에 추가
- 컨벤션 체크리스트 중 완료 항목 체크

### 5. session-compact.md 업데이트

- Remaining/TODO 해당 항목 진행 상태 반영
- Phase 마지막 step 완료 시: Phase 자체를 `[x]` 완료 처리

### 6. 정합성 검증 (Consistency Check)

업데이트 후 아래를 검증:
- [ ] Phase tasks.md 체크 상태 == project-overall-tasks.md 해당 섹션
- [ ] Phase tasks.md 진행률 == project-overall-plan.md 해당 Phase 설명
- [ ] session-compact.md의 TODO가 실제 진행률과 일치

### 7. Git Commit

#### 7.1 Staging
```bash
# 코드 변경 + 문서 변경 모두 포함
git add backend/api/ frontend/       # 해당 Phase 코드
git add dev/active/[phase-name]/     # Phase dev-docs
git add dev/active/project-overall/  # project-overall (항상 포함!)
git add docs/session-compact.md      # session-compact (변경 시)
```

#### 7.2 Commit Message 형식
```
[phase-name] Step X.Y: 간단한 설명

- 주요 변경 1
- 주요 변경 2

Refs: dev/active/[phase-name]/[phase-name]-tasks.md
```

#### 7.3 Phase 완료 시 추가 작업
Phase 마지막 step 완료 시:
- Phase plan.md Status → `Complete`
- Phase tasks.md Progress → `N/N (100%)`
- project-overall-tasks.md 해당 Phase 헤더에 `✅ 완료` 추가
- session-compact.md 해당 Phase `[x]` 체크

---

## Output Format

```
Step Update 완료

Task: [phase-name]
Step: X.Y — [Step Name]

Phase docs 업데이트:
- tasks.md: Step X.Y 완료 체크 (N/M, P%)
- context.md: N개 파일/결정사항 추가
- plan.md: 상태 업데이트

project-overall 동기화:
- tasks.md: 동일 step 체크 완료
- plan.md: Current State 갱신
- context.md: 결정사항 반영

Git:
- Commit: [hash] [message]
- Branch: [branch-name]

전체 진행률: Phase X/Y steps (N%)
프로젝트 진행률: N/76 tasks (N%)
```

---

## Error Handling

| 상황 | 대응 |
|------|------|
| Phase dev-docs 없음 | `/dev-docs` 먼저 실행 안내 |
| project-overall 없음 | 경고 후 Phase docs만 업데이트 |
| 커밋할 변경 없음 | 문서만 업데이트 후 커밋 스킵 |
| tasks.md 불일치 | 경고 메시지 출력 + 수동 확인 요청 |
| Phase 완료 감지 | 자동으로 완료 처리 + 다음 Phase 안내 |

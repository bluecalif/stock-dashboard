---
description: 개발 단계 완료 시 문서 업데이트, 커밋, PR 생성/푸시
argument-hint: task-name step-number (예: "fdr-collector 1.2")
---

# 단계 업데이트 (Step Update)

**Task:** $ARGUMENTS

## Overview

개발 단계(step/sub-phase) 완료 시 실행하는 통합 업데이트 커맨드.

```
문서 업데이트 → Git Commit → PR 생성/업데이트 → Push
```

---

## Instructions

### 1. 인자 파싱 (Parse Arguments)

입력 형식: `[task-name] [step-id]`

예시:
- `fdr-collector 1.2` → Phase 1, Step 2
- `backtest-engine 2.1` → Phase 2, Step 1

### 2. 현재 상태 확인 (Check Current State)

```bash
ls dev/active/[task-name]/
git status
git branch
```

확인 사항:
- [ ] dev-docs 파일 존재 여부
- [ ] 현재 브랜치 확인
- [ ] 커밋되지 않은 변경사항

### 3. Dev-Docs 업데이트 (Update Documentation)

#### 3.1 tasks.md 업데이트
완료된 태스크 체크:
```markdown
## Phase 1: [Phase Name]
### Step 1.2: [Step Name] ← 현재
- [x] Task C (완료)  ← 업데이트
- [ ] Task D (진행중)
```

#### 3.2 context.md 업데이트
변경된 파일 및 결정사항 추가:
```markdown
## Changed Files (Step 1.2)
- `collector/fdr_client.py` - 신규 생성
- `collector/validators.py` - 수정

## Decisions
- [Step 1.2] FDR 호출 시 지수 백오프 최대 3회 재시도
```

#### 3.3 plan.md 업데이트
진행 상태 갱신:
```markdown
> Last Updated: YYYY-MM-DD
> Status: In Progress
> Current Step: 1.2
```

### 4. Git Commit (커밋)

#### 4.1 Staging
```bash
git add collector/ research_engine/ api/ dashboard/
git add dev/active/[task-name]/
```

#### 4.2 Commit Message 형식
```
[task-name] Step X.Y: 간단한 설명

- 주요 변경 1
- 주요 변경 2

Refs: dev/active/[task-name]/[task-name]-tasks.md
```

### 5. PR 생성/업데이트 (Pull Request)

#### 5.1 브랜치
```bash
git checkout -b feature/[task-name]  # 신규시
git checkout feature/[task-name]      # 기존시
```

#### 5.2 Push & PR
```bash
git push -u origin feature/[task-name]
```

PR 최초 생성:
```bash
gh pr create \
  --title "[task-name] Implementation" \
  --body "## Summary
[task-name] 구현 PR

## Progress
- [x] Step 1.1
- [x] Step 1.2 ← Current

## Related
- Plan: dev/active/[task-name]/[task-name]-plan.md
- Tasks: dev/active/[task-name]/[task-name]-tasks.md"
```

---

## Output Format

```
Step Update 완료

Task: [task-name]
Step: X.Y - [Step Name]

문서 업데이트:
- tasks.md: N개 태스크 완료 체크
- context.md: N개 파일 추가
- plan.md: 상태 업데이트

Git:
- Commit: [hash] [message]
- Branch: feature/[task-name]
- PR: #[number] [url]

전체 진행률: X/Y steps (N%)
```

---

## Error Handling

| 상황 | 대응 |
|------|------|
| dev-docs 없음 | `/dev-docs` 먼저 실행 안내 |
| 커밋할 변경 없음 | 문서만 업데이트 후 스킵 |
| PR 이미 존재 | 기존 PR에 코멘트 추가 |
| 충돌 발생 | 충돌 해결 안내 |

---
description: 프로젝트 마무리 — 교훈, 재사용 패턴, 설계 순서도, 총괄 요약 생성
argument-hint: (선택) 컨텍스트 파일 경로 (예: "docs/session-compact.md")
---

# Project Wrapup

**컨텍스트 파일:** $ARGUMENTS

## Instructions

### 1. 프로젝트 분석 (Gather Context)

아래를 모두 읽고 프로젝트 전체 그림을 파악:

**필수 참조:**
- `docs/masterplan-v0.md` — 설계 문서
- `docs/session-compact.md` — 최종 상태
- `README.md` — 프로젝트 소개
- `CLAUDE.md` — 컨벤션
- `dev/active/project-overall/` — 전체 Phase 계획/컨텍스트/태스크
- `dev/active/*/debug-history.md` — Phase별 디버깅 이력

**보조 참조 (존재 시):**
- 사용자 제공 컨텍스트 파일 (`$ARGUMENTS`)
- `dev/active/*/` — 각 Phase plan/context/tasks

**Git 분석:**
- `git log --oneline` — 전체 커밋 히스토리
- `git log --shortstat` — 코드 변경량
- 총 커밋 수, 테스트 수, 주요 마일스톤 커밋

### 2. 산출물 생성 (Generate Artifacts)

**위치:** `project-wrapup/`

아래 5개 파일을 순서대로 생성:

---

#### 2.1 `lessons-learned.md` — 교훈 상세

```markdown
# Lessons Learned — [프로젝트명]
> Generated: YYYY-MM-DD

## 기술적 교훈 (Technical)
| # | 카테고리 | 문제 | 해결 | Phase |
|---|----------|------|------|-------|

## 설계 교훈 (Architecture)
| # | 카테고리 | 결정 | 이유 | 결과 |
|---|----------|------|------|------|

## 프로세스 교훈 (Process)
| # | 카테고리 | 교훈 | 상세 |
|---|----------|------|------|
```

- Phase별 debug-history.md의 Lessons Learned 섹션을 통합·정리
- 카테고리 예: db, auth, api, frontend, infra, testing, ai, data

---

#### 2.2 `lessons-learned.json` — 교훈 DB (구조화)

```json
{
  "project": "프로젝트명",
  "stack": ["Python", "FastAPI", "React", ...],
  "generated": "YYYY-MM-DD",
  "lessons": [
    {
      "id": "T-001",
      "type": "technical | architecture | process",
      "category": "db | auth | api | frontend | infra | testing | ai | data",
      "title": "한 줄 제목",
      "problem": "문제 상황",
      "solution": "해결 방법",
      "impact": "high | medium | low",
      "phase": "Phase X",
      "tags": ["keyword1", "keyword2"]
    }
  ]
}
```

- `lessons-learned.md`와 동일 내용의 JSON 버전
- 다른 프로젝트의 JSON과 합쳐서 크로스 프로젝트 교훈 DB 구축 가능

---

#### 2.3 `reusable-patterns/` — 재사용 코드 스니펫

프로젝트에서 검증된 패턴을 추출하여 독립 스니펫으로 저장:

- 각 파일 상단에 `## 용도`, `## 사용법`, `## 출처` 주석 포함
- 실제 프로젝트 코드에서 추출 (핵심만 남기고 프로젝트 특화 부분 제거)
- 파일명은 패턴 이름 기반 (예: `jwt-auth-flow.py`, `zustand-auth-store.ts`)

**추출 기준:**
- 다른 프로젝트에서 재사용 가능한가?
- 충분히 검증되었는가? (테스트 통과, 프로덕션 사용)
- 패턴으로서 가치가 있는가? (단순 CRUD는 제외)

---

#### 2.4 `project-blueprint.md` — 유사 프로젝트 설계 순서도

```markdown
# Project Blueprint — [프로젝트 유형] 설계 순서도
> Source: [프로젝트명] 개발 경험 기반

## 프로젝트 유형
(이 프로젝트와 유사한 프로젝트의 특성 정의)

## 권장 Phase 순서
### Phase 1: [이름]
- 목표:
- 체크포인트:
- 예상 규모:
- 주의사항:

### Phase 2: ...

## 피해야 할 함정
| # | 함정 | 왜 위험한가 | 대안 |
|---|------|------------|------|

## 추천 스택 조합
(이 프로젝트에서 검증된 조합 + 대안)

## 체크리스트
(각 Phase 완료 시 확인할 항목)
```

---

#### 2.5 `wrapup-summary.md` — 총괄 요약 (마지막에 생성)

```markdown
# Project Wrapup — [프로젝트명]
> Generated: YYYY-MM-DD

## 프로젝트 개요
(1-2문장 소개)

## 최종 상태
- Phase: 완료/총 Phase
- 테스트: N개
- 커밋: N개
- 기간: 시작일 ~ 종료일

## 핵심 성과
(주요 기능, 기술적 성취 3-5개)

## 교훈 요약
(lessons-learned.md에서 high impact 항목 3-5개 발췌)
→ 상세: [lessons-learned.md](lessons-learned.md)
→ DB: [lessons-learned.json](lessons-learned.json)

## 재사용 패턴
(reusable-patterns/에서 핵심 패턴 목록 + 한 줄 설명)
→ 상세: [reusable-patterns/](reusable-patterns/)

## 설계 순서도 요약
(project-blueprint.md에서 Phase 순서만 발췌)
→ 상세: [project-blueprint.md](project-blueprint.md)

## 후속 과제
(남은 TODO, 확장 가능성)
```

---

### 3. 정합성 검증 (Consistency Check)

- [ ] lessons-learned.md의 모든 항목이 lessons-learned.json에 존재
- [ ] reusable-patterns/ 각 파일이 실제 프로젝트 코드에서 추출됨
- [ ] project-blueprint.md의 Phase 순서가 실제 개발 경험 반영
- [ ] wrapup-summary.md의 링크가 모두 유효

---

## Output Format

```
생성 완료

project-wrapup/
├── wrapup-summary.md          (총괄 요약)
├── lessons-learned.md         (교훈 상세)
├── lessons-learned.json       (교훈 DB — 크로스 프로젝트 활용)
├── project-blueprint.md       (설계 순서도)
└── reusable-patterns/         (재사용 코드 스니펫)
    ├── [pattern-1].py
    ├── [pattern-2].ts
    └── ...

요약:
- 교훈: N건 (기술 n, 설계 n, 프로세스 n)
- 재사용 패턴: N개
- Blueprint Phase: N단계
```

---
description: 프로젝트 마무리 — 교훈, 재사용 패턴, 설계 순서도, 총괄 요약 생성
argument-hint: (선택) 컨텍스트 파일 경로 (예: "docs/session-compact.md")
---

# Project Wrapup

**컨텍스트 파일:** $ARGUMENTS

## 핵심 원칙

이 스킬의 산출물은 **"우리가 뭘 했는가"를 남기는 회고 문서가 아니라, "다음 유사 프로젝트가 시행착오를 줄이려면 어떻게 해야 하는가"를 남기는 실행 가이드**다.

- 회고 중심 문장보다 **지침 중심 문장**을 우선한다
- 모든 교훈은 **예방 규칙, 사전 점검, 재사용 패턴**과 연결한다
- 문서 간 역할이 겹치지 않고, **ID 기반 교차 참조**로 연결한다

---

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

**가이드라인 참조:**
- `project-wrapup/project-wrapup-guideline.md` — 산출물 품질 기준 (존재 시)

---

### 2. 산출물 생성 (Generate Artifacts)

**위치:** `project-wrapup/`

아래 5개를 순서대로 생성. **모든 문서에서 공통 ID 체계**를 사용한다:
- Phase ID: `Phase 1`, `Phase 2`, ...
- Lesson ID: `T-001` (기술), `A-001` (설계), `P-001` (프로세스)
- Pattern ID: 파일명 (예: `jwt-auth-flow.py`)

---

#### 2.1 `lessons-learned.md` — 실수 방지 플레이북

> **역할**: 사후 회고표가 아니라, 유사 프로젝트를 위한 **실수 방지 플레이북**

**High-impact 항목** (프로젝트에서 가장 큰 영향을 준 교훈, 보통 5-10개)은 상세 형식으로 작성:

```markdown
### T-001: [한 줄 제목]

- **문제**: 무슨 일이 있었는가
- **왜 발생했는가**: 근본 원인
- **조기 징후**: 이 문제가 터지기 전에 보이는 신호
- **예방 규칙**: 다음 프로젝트에서 이걸 막으려면 어떤 규칙을 세워야 하는가
- **코드/설계 대응**: 구체적 코드 또는 설계 수준 해결법
- **PR 전 점검법**: 코드 리뷰 시 이걸 잡으려면 뭘 확인해야 하는가
- **관련 pattern**: `[pattern-file.py]` (있는 경우)
- **관련 blueprint 단계**: Phase N
```

**일반 항목**은 테이블 형식 + 예방 규칙 열 추가:

```markdown
## 기술적 교훈 (Technical)
| ID | 카테고리 | 문제 | 해결 | 예방 규칙 | Phase |
|----|----------|------|------|----------|-------|

## 설계 교훈 (Architecture)
| ID | 카테고리 | 결정 | 이유 | 예방 규칙 | 결과 |
|----|----------|------|------|----------|------|

## 프로세스 교훈 (Process)
| ID | 카테고리 | 교훈 | 예방 규칙 | 상세 |
|----|----------|------|----------|------|
```

- Phase별 debug-history.md의 Lessons Learned 섹션을 통합·정리
- 카테고리 예: db, auth, api, frontend, infra, testing, ai, data
- **"이 문제를 겪었다"가 아니라 "이 문제를 다음에 어떻게 미리 막는가"가 보여야 한다**

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
      "prevention_rule": "예방 규칙 — 다음 프로젝트에서 이걸 막으려면",
      "early_signs": "조기 징후 (high-impact만, 나머지는 null)",
      "impact": "high | medium | low",
      "phase": "Phase X",
      "related_patterns": ["pattern-file.py"],
      "related_blueprint_phase": "Phase N",
      "tags": ["keyword1", "keyword2"]
    }
  ]
}
```

- `lessons-learned.md`와 동일 내용의 JSON 버전
- `prevention_rule`은 **모든 항목에 필수**
- `early_signs`, `related_patterns`는 high-impact 항목에만 (나머지는 null)
- 다른 프로젝트의 JSON과 합쳐서 크로스 프로젝트 교훈 DB 구축 가능

---

#### 2.3 `reusable-patterns/` — 재사용 스니펫 라이브러리

> **역할**: 예시 코드 모음이 아니라, 유사 프로젝트를 위한 **스니펫 자산 라이브러리**

각 파일 상단에 **7-필드 헤더**를 반드시 포함:

```python
"""
## 용도
(이 패턴이 해결하는 문제)

## 언제 쓰는가
(어떤 상황에서 이 패턴이 필요한가)

## 전제조건
(이 패턴을 쓰려면 미리 갖춰야 할 것)

## 의존성
(필요한 패키지, import, 환경 변수)

## 통합 포인트
(어떤 계층/모듈에 들어가는지, 다른 코드와 어떻게 연결되는지)

## 주의사항
(실패하기 쉬운 포인트, 흔한 실수)

## 출처
(원본 프로젝트 파일 경로)
"""
```

**추출 기준:**
- 다른 프로젝트에서 재사용 가능한가?
- 충분히 검증되었는가? (테스트 통과, 프로덕션 사용)
- 패턴으로서 가치가 있는가? (단순 CRUD는 제외)
- placeholder는 명시적으로 `# TODO: 프로젝트에 맞게 수정` 표시
- **복붙 가능 / 수정 필요** 여부를 헤더에 명시

---

#### 2.4 `project-blueprint.md` — 유사 프로젝트 설계 가이드

> **역할**: 단순 Phase 목록이 아니라, 유사 프로젝트를 위한 **이상적 개발 계획서**

```markdown
# Project Blueprint — [프로젝트 유형] 설계 가이드
> Source: [프로젝트명] 개발 경험 기반

## 프로젝트 유형
(이 프로젝트와 유사한 프로젝트의 특성 정의)

## 권장 개발 경로

### Core Path (반드시 먼저)
#### Phase 1: [이름]
- **목표**: 
- **선행조건**: (이것 없이는 시작하지 말 것)
- **완료조건**: (이것을 확인해야 다음으로)
- **시작하지 말아야 할 조건**: (이 단계에서 아직 하면 안 되는 것)
- **초기에 결정할 사항**: 
- **관련 교훈**: T-001, A-002
- **규모감**: 소/중/대

### Expansion Path (Core 완료 후)
#### Phase N: [이름]
(동일 구조)

## 피해야 할 함정
| # | 함정 | 왜 위험한가 | 대안 | 관련 교훈 |
|---|------|------------|------|----------|

## 의사결정 규칙
- 배포와 데이터 정합성 전에 AI 확장을 먼저 하지 않는다
- Canonical Form과 데이터 Flow 정합성을 먼저 고정한다
- 대시보드와 Agentic 데이터 소스 일치 전에는 AI 고도화를 확장하지 않는다
- 실사용 근거가 없는 Context/Memory는 후순위로 둔다

## 추천 스택 조합
(이 프로젝트에서 검증된 조합 + 대안)

## 체크리스트
(각 Phase 완료 시, 배포 전, AI 기능 추가 전 확인할 항목)
```

**핵심 방향:**
- 각 Phase에 **gate 조건**(선행/완료/금지)이 있어야 Phase 나열이 아닌 실행 가이드가 된다
- Core Path / Expansion Path 구분으로 고급 기능이 코어보다 뒤로 밀려야 한다
- `관련 교훈` 필드로 blueprint → lessons-learned 교차 참조

---

#### 2.5 `wrapup-summary.md` — 패키지 활용 가이드 (마지막에 생성)

> **역할**: 프로젝트 자랑 문서가 아니라, **문서 패키지 전체의 입구**

```markdown
# Project Wrapup — [프로젝트명]
> Generated: YYYY-MM-DD

## 이 패키지로 무엇을 얻을 수 있는가
(1-2문장: 어떤 유형의 프로젝트에 적합하고, 무엇을 제공하는가)

## 읽는 순서
1. 이 문서 (전체 파악)
2. project-blueprint.md (개발 순서 결정)
3. lessons-learned.md (실수 방지)
4. reusable-patterns/ (코드 재사용)

## 프로젝트 개요
- Phase: 완료/총 Phase
- 테스트: N개
- 커밋: N개
- 기간: 시작일 ~ 종료일

## 가장 중요한 실수 Top 5
| 순위 | 교훈 ID | 한 줄 요약 | 예방 규칙 |
|------|---------|-----------|----------|
→ 상세: [lessons-learned.md](lessons-learned.md)

## 바로 재사용할 수 있는 패턴 Top 5
| 순위 | 패턴 | 해결 문제 | 복붙 가능? |
|------|------|----------|-----------|
→ 상세: [reusable-patterns/](reusable-patterns/)

## 권장 개발 순서 1페이지 요약
(project-blueprint.md에서 Core Path + Expansion Path 요약)
→ 상세: [project-blueprint.md](project-blueprint.md)

## 후속 과제
(남은 TODO, 확장 가능성)
```

---

### 3. 정합성 검증 (Consistency Check)

- [ ] lessons-learned.md의 모든 항목이 lessons-learned.json에 존재
- [ ] lessons-learned.json의 모든 항목에 `prevention_rule` 존재
- [ ] high-impact 항목에 `early_signs`, `related_patterns` 존재
- [ ] blueprint의 `관련 교훈` ID가 lessons-learned에 실제 존재
- [ ] lessons-learned의 `관련 pattern` 파일이 reusable-patterns/에 실제 존재
- [ ] reusable-patterns/ 각 파일이 7-필드 헤더를 가짐
- [ ] reusable-patterns/ 각 파일이 실제 프로젝트 코드에서 추출됨
- [ ] wrapup-summary.md의 Top 5 실수/패턴이 실제 교훈/패턴과 일치
- [ ] wrapup-summary.md의 링크가 모두 유효
- [ ] 테스트 수, 기간, phase 수 등 수치가 문서 간 일관

---

## Output Format

```
생성 완료

project-wrapup/
├── wrapup-summary.md          (패키지 활용 가이드)
├── lessons-learned.md         (실수 방지 플레이북)
├── lessons-learned.json       (교훈 DB — 크로스 프로젝트 활용)
├── project-blueprint.md       (설계 가이드)
└── reusable-patterns/         (재사용 스니펫 라이브러리)
    ├── [pattern-1].py
    ├── [pattern-2].ts
    └── ...

요약:
- 교훈: N건 (기술 n, 설계 n, 프로세스 n) — high-impact n건
- 재사용 패턴: N개
- Blueprint Phase: N단계 (Core n + Expansion n)
- 교차 참조: blueprint→lesson N건, lesson→pattern N건
```

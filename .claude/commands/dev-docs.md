---
description: Phase dev-docs 생성 + project-overall 동기화
argument-hint: 계획할 내용 (예: "Phase 4 API", "Phase 5 Frontend")
---

# 개발 문서 생성 (Dev Docs Generator)

**Task:** $ARGUMENTS

## Instructions

### 1. 요청 분석 (Analyze Request)

- 범위(scope)와 영향도(impact) 파악
- 관련 컴포넌트 식별 (collector, research_engine, api, frontend)
- 기존 설계 문서와의 연관성 확인

### 2. 관련 문서 검토 (Review Existing Docs) — 반드시 모두 읽기

**프로젝트 전체 (필수):**
- `docs/masterplan-v0.md` — 마스터플랜 (아키텍처, API 명세, 프론트엔드, 마일스톤)
- `docs/session-compact.md` — 현재 진행 상태
- `dev/active/project-overall/project-overall-plan.md` — 전체 Phase 계획
- `dev/active/project-overall/project-overall-context.md` — 결정사항, 컨벤션
- `dev/active/project-overall/project-overall-tasks.md` — 전체 태스크 목록

**해당 Phase (존재 시):**
- `dev/active/[phase-name]/[phase-name]-plan.md`
- `dev/active/[phase-name]/[phase-name]-context.md`
- `dev/active/[phase-name]/[phase-name]-tasks.md`

### 3. Phase Dev-Docs 생성 (Generate Phase Files)

**위치:** `dev/active/[phase-name]/`

| 파일 | 용도 |
|------|------|
| `[phase-name]-plan.md` | 종합 계획 (Summary, Current State, Target State, Stages, Tasks, Risks, Dependencies) |
| `[phase-name]-context.md` | 핵심 파일, 결정사항, 데이터 인터페이스, 컨벤션 체크 |
| `[phase-name]-tasks.md` | 체크리스트 형식 진행 추적 (commit hash 포함) |

**파일 헤더:**
```markdown
# [Phase Name]
> Last Updated: YYYY-MM-DD
> Status: Planning | In Progress | Review | Complete
```

**plan.md 필수 섹션:**
```
1. Summary (개요) — 목적, 범위, 예상 결과물
2. Current State (현재 상태) — 이전 Phase에서 넘어온 것
3. Target State (목표 상태) — 완료 후 기대 상태
4. Implementation Stages — Stage A, B... 순차 단계
5. Task Breakdown — 태스크 테이블 (Size: S/M/L/XL, 의존성)
6. Risks & Mitigation
7. Dependencies — 내부(다른 모듈) + 외부(라이브러리)
```

**context.md 필수 섹션:**
```
1. 핵심 파일 — 이 Phase에서 읽어야 할 기존 코드 경로
2. 데이터 인터페이스 — 입력(어디서 읽는가) / 출력(어디에 쓰는가)
3. 주요 결정사항 — 아키텍처 선택, 트레이드오프
4. 컨벤션 체크리스트 — 해당 Phase에 적용되는 규칙
```

### 4. project-overall 동기화 (CRITICAL — 반드시 수행)

Phase dev-docs 생성 후, 아래 3개 파일을 **반드시** 동시 업데이트:

#### 4.1 `project-overall-plan.md`
- 해당 Phase 섹션 내용을 Phase dev-docs와 정합성 맞추기
- Current State 갱신 (이전 Phase 완료 반영)
- 데이터 흐름도가 새 Phase 범위를 포함하는지 확인

#### 4.2 `project-overall-context.md`
- 주요 결정사항 테이블에 새 결정 추가
- API 엔드포인트 / 프론트엔드 페이지 테이블이 Phase 내용과 일치하는지 확인
- 컨벤션 체크리스트 업데이트

#### 4.3 `project-overall-tasks.md`
- 해당 Phase 태스크 목록이 Phase tasks.md와 **동일**한지 확인
- Summary 섹션 (총 태스크 수, Size 분포) 갱신

### 5. 정합성 검증 (Consistency Check)

생성 완료 후 아래를 검증:
- [ ] Phase tasks.md 태스크 목록 == project-overall-tasks.md 해당 Phase 섹션
- [ ] Phase plan.md의 Stage 구조 == project-overall-plan.md 해당 Phase 설명
- [ ] masterplan-v0.md의 해당 섹션과 Phase plan.md 범위가 일치
- [ ] session-compact.md의 Remaining/TODO가 최신 상태

### 6. 컨벤션 체크 (Convention Checklist)

**데이터:** OHLCV 스키마, FDR primary, idempotent UPSERT
**API:** Router-Service-Repository, Pydantic, DI, CORS, Pagination
**인코딩:** utf-8-sig (read), utf-8 (write), PYTHONUTF8=1
**배포:** 환경변수 금지, .env gitignore, TLS

---

## Output Format

```
생성 완료

Phase dev-docs:
dev/active/[phase-name]/
├── [phase-name]-plan.md      (종합 계획)
├── [phase-name]-context.md   (컨텍스트)
└── [phase-name]-tasks.md     (태스크 추적)

project-overall 동기화:
dev/active/project-overall/
├── project-overall-plan.md    (Phase 섹션 업데이트)
├── project-overall-context.md (결정사항/테이블 업데이트)
└── project-overall-tasks.md   (태스크 목록 동기화)

요약:
- Stages: N개
- Tasks: N개 (S: n, M: n, L: n, XL: n)
- 정합성 검증: PASS / FAIL (상세)
```

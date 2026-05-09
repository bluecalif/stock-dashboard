---
description: Phase dev-docs 생성 + project-overall 동기화. 모든 검증 게이트는 "Show, don't claim" 정책에 따라 명령/Evidence/통과기준 3단 형식으로 작성하고 verification/ 누적 디렉터리를 표준 산출물에 포함시킨다.
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

| 파일/디렉터리 | 용도 |
|------|------|
| `[phase-name]-plan.md` | 종합 계획 (Summary, Current State, Target State, Stages, Tasks, Risks, Dependencies) |
| `[phase-name]-context.md` | 핵심 파일, 결정사항, 데이터 인터페이스, 컨벤션 체크 |
| `[phase-name]-tasks.md` | 체크리스트 형식 진행 추적 (commit hash 포함) |
| `debug-history.md` | 전체 Phase 디버깅 이력 (버그, 원인, 수정, 교훈) — Phase당 단일 파일 |
| `verification/` | step별 evidence 누적 디렉터리 (§3.5 참조) — README.md + step-N-<topic>.md + figures/ |

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

**debug-history.md 필수 섹션:**
```
# [Phase Name] Debug History
> Last Updated: YYYY-MM-DD

## Step X.Y: [Step Name]

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|

### X.Y-N: [Bug Title] (심층 디버깅 시)
- **증상**: 에러 메시지 또는 관찰된 동작
- **원인**: 근본 원인 분석
- **수정**: 변경 내용 + 파일 경로

## Modified Files Summary
(Phase 전체 변경 파일 트리)

## Lessons Learned
(반복되는 패턴, 환경 이슈, 방어적 코딩 교훈)
```

**context.md 필수 섹션:**
```
1. 핵심 파일 — 이 Phase에서 읽어야 할 기존 코드 경로
2. 데이터 인터페이스 — 입력(어디서 읽는가) / 출력(어디에 쓰는가)
3. 주요 결정사항 — 아키텍처 선택, 트레이드오프
4. 컨벤션 체크리스트 — 해당 Phase에 적용되는 규칙
5. §0 핵심 원칙 — "Show, don't claim" (§3.5 정책 forwarding 1단락)
```

### 3.5 검증 게이트 형식 표준 — "Show, don't claim" (필수)

> **원칙**: 검증 게이트의 체크박스는 evidence가 dev-docs 또는 `verification/step-N-<topic>.md`에 paste되고 사용자가 본 후에만 표시 가능. Claude의 "통과/PASS" 주장만으로는 mark complete 금지.

#### 게이트 작성 형식 (3단)

```markdown
- [ ] <검증 항목>
  - 명령: <실행 가능한 1줄 — CLI 명령, SQL, Python 스니펫>
  - Evidence: <어떤 형식의 출력을 어디에 paste — markdown 표 / 코드 블록 / PNG 임베드>
  - 통과 기준: <PASS/FAIL 가르는 구체 임계 — 숫자, 형식, 일치 여부>
```

#### `verification/` 서브디렉터리 구조

```
dev/active/[phase-name]/
└── verification/
    ├── README.md                  (정책 + 진행 현황 표)
    ├── step-1-<topic>.md           (명령 + raw output + 해석)
    ├── step-2-<topic>.md
    └── figures/
        └── step-N-<topic>.png      (PNG 시각 산출물)
```

각 evidence 파일은 게이트별로 다음 구조:

```markdown
## G<step>.<n> — <검증 항목>
**명령**: <실행한 1줄>
**Raw output**: <표 / 코드 블록 / PNG 임베드>
**검증 결과**: ✅ PASS / ❌ FAIL — <근거>
```

#### PNG 시각 산출물 의무 (수치/시계열/분포/UI step)

다음 유형은 PNG 차트 의무 (`verification/figures/`):
- **수치 알고리즘 검증** (평균 보존, 분포 일치, reproducibility 시각)
- **시계열 적합성** (padding 구간, 추세 비교, 시계열 라인)
- **분포 검증** (히스토그램, σ 분포, row count bar chart)
- **UI / E2E** (스크린샷 — 모바일/데스크탑, drawer 동작, redirect 확인)

#### 체크 권한 규칙

- ✅ **체크 가능**: evidence paste + 사용자 노출
- ❌ **체크 금지**: Claude만 명령 실행, raw output 비공개
- ❌ **체크 금지**: "정상", "통과", "smoke OK" 주장만, raw output 부재

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
- **§0 "Show, don't claim" 핵심 원칙 섹션** — 신규 Gen이면 최초 1회 작성 (§3.5 정책 본문 옮겨오기). 후속 Phase가 자동 inherit하도록.

#### 4.3 `project-overall-tasks.md`
- 해당 Phase 태스크 목록이 Phase tasks.md와 **동일**한지 확인
- Summary 섹션 (총 태스크 수, Size 분포) 갱신

### 5. 정합성 검증 (Consistency Check)

생성 완료 후 아래를 검증:
- [ ] Phase tasks.md 태스크 목록 == project-overall-tasks.md 해당 Phase 섹션
- [ ] Phase plan.md의 Stage 구조 == project-overall-plan.md 해당 Phase 설명
- [ ] masterplan-v0.md의 해당 섹션과 Phase plan.md 범위가 일치
- [ ] session-compact.md의 Remaining/TODO가 최신 상태
- [ ] **모든 검증 게이트가 §3.5 3단 형식 (명령/Evidence/통과 기준) 준수**
- [ ] **`verification/` 서브디렉터리 + `README.md` 작성됨** (Phase별 신규 시)
- [ ] **수치·시계열·분포·UI step에 PNG 의무 항목 명시됨** (해당 시)
- [ ] **DoD에 evidence 파일 + PNG 누적 항목 포함됨**

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
├── [phase-name]-context.md   (컨텍스트 + §0 Show-don't-claim forwarding)
├── [phase-name]-tasks.md     (태스크 추적, 게이트 = 3단 형식)
├── debug-history.md          (디버깅 이력)
└── verification/             (step별 evidence 누적)
    ├── README.md
    └── figures/              (PNG 시각 산출물 위치)

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

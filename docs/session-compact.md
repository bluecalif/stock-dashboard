# Session Compact

> Generated: 2026-05-09
> Source: Conversation compaction via /compact-and-go

## Goal

Bronze gen 종료 + Silver gen 시작 준비. session-compact.md 직전 세션의 Step 0 지시("dev-docs 정리 → silver project-overall 작성 → Phase 1 코딩 진입")를 실행하되, 사용자 추가 요청으로 silver gen 전용 skill까지 정비. 본 세션은 코딩 직전까지 완료. 다음 세션은 **`dev/active/silver-rev1-phase1/` Phase dev-docs 작성** 또는 **Phase 1 코딩(Alembic migration)** 진입.

## Completed

- [x] **Bronze gen archive**: `dev/active/` 19개 폴더(phase1~7 + phaseA~G + project-overall) → `dev/archive/bronze-gen/`로 이동. 71 파일 손실 0 검증, 미커밋 변경분(`phaseF-agentic/*.md` 3건)도 보존
- [x] `dev/active/` 비움 (silver gen 진입 준비)
- [x] **Silver project-overall 3종 신규 생성** (`Gen: silver` 헤더):
  - `project-overall-plan.md` — Stage A~E (Phase 1~5) 매핑, 마스터플랜 §8 그대로
  - `project-overall-context.md` — D-1~D-21 결정 21건 + 컨벤션 체크리스트 + 미해결 후속 결정
  - `project-overall-tasks.md` — Phase 1~5 = 29 태스크 (S:10 / M:12 / L:6 / XL:1)
- [x] **silver-simulation skill 신규 생성** (`.claude/skills/silver-simulation/SKILL.md`, ~330줄):
  - 21 D-lock 결정 표 (코딩 시 매번 확인용)
  - 8 모듈 구조 (replay/strategy_a/b/portfolio/padding/wbi/fx/mdd)
  - 핵심 패턴 (lock 사이클, GBM 시드 42, cyclic returns reverse-cumprod)
  - Anti-Patterns 12건 (자주 빠지는 함정)
  - 사용자 흐름 (Tab A/B/C → API → simulation, A-004 적용)
- [x] `skill-rules.json`에 silver-simulation 트리거 등록 (priority: high, 25+ 키워드 + 5 intentPatterns)
- [x] **frontend-dev에 silver-design.md references 분리** (progressive disclosure):
  - `.claude/skills/frontend-dev/references/silver-design.md` 신규 (~270줄): 다크 톤 토큰, KpiCard/EquityChart/Pill/Drawer 레시피, 모바일 768px, anti-patterns 9건
  - `frontend-dev/SKILL.md`에 "Silver Visual System" 1줄 포인터 + description 보강

## Current State

- 코드 변경 없음 (skill/dev-docs 정비만)
- `dev/active/` = `project-overall/`만 존재 (silver gen 시작 직전 상태)
- skill 5종: `backend-dev` / `frontend-dev` (silver-design 통합) / `langgraph-dev` / `silver-simulation` (신규) / `skill-developer`
- Bronze 운영 그대로, Phase 4 빅뱅 cut-over 전까지 영향 0

### Changed Files

**신규**:
- `dev/active/project-overall/project-overall-plan.md`
- `dev/active/project-overall/project-overall-context.md`
- `dev/active/project-overall/project-overall-tasks.md`
- `.claude/skills/silver-simulation/SKILL.md`
- `.claude/skills/frontend-dev/references/silver-design.md`
- `dev/archive/bronze-gen/` (19개 폴더 통째로 이동)

**수정**:
- `.claude/skills/skill-rules.json` (silver-simulation 트리거 추가)
- `.claude/skills/frontend-dev/SKILL.md` (description 보강 + Silver Visual System 섹션 + Related Docs 갱신)
- `docs/session-compact.md` (재생성)

**이동(삭제+복사)**:
- `dev/active/{phase1~7, phaseA~G, project-overall}` → `dev/archive/bronze-gen/`

## Remaining / TODO

다음 작업은 **`/dev-docs` 두 번째 호출**(silver-rev1-phase1 Phase dev-docs 작성) 또는 **Phase 1 코딩 진입**.

### Phase 1 — Data Infra (Bronze 영향 0, S:2/M:3/L:1)

- [ ] **P1-1 (M)** Alembic migration — `asset_master` 5컬럼(currency / annual_yield / history_start_date / allow_padding / display_name) + `fx_daily` 신규 테이블 (마스터플랜 §5.1 SQL)
- [ ] **P1-2 (S)** `backend/collector/fdr_client.py:14` SYMBOL_MAP 8종 추가 (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA)
- [ ] **P1-3 (M)** `backend/collector/fx_collector.py` 신규 — FDR `USD/KRW` 일봉
- [ ] **P1-4 (L)** 신규 자산 10년 backfill (staging) + asset_master 컬럼 채움
- [ ] **P1-5 (M)** padding 알고리즘 unit test (JEPI 5년 → 10년 cyclic returns)
- [ ] **P1-6 (S)** WBI synthetic 시드 42 fixture 저장

### Phase 2~5 — `dev/active/project-overall/project-overall-tasks.md` 참조

## Key Decisions

### 워크플로우 결정

- **Bronze archive 위치**: `dev/archive/bronze-gen/` (직전 session-compact 명시 컨벤션 따름, dev-docs skill 기본 `dev/archive/bronze/` 대신)
- **silver-simulation은 별도 skill**: backend-dev에 silver 섹션 추가하지 않고 도메인 단위로 분리. 21 D-lock 결정이 stack skill로 커버 안 되는 이유
- **frontend-dev는 references/silver-design.md로 progressive disclosure**: 별도 silver-design skill 안 만들고 frontend-dev 안에 분리 — silver-rev1 외 프로젝트에서 불필요한 스킬 회피
- **eval 절차 생략 (vibe 모드)**: skill 작성 후 evals/iteration 루프 안 돌림. silver-rev1 실작업이 더 강한 검증

### 시각 디자인 결정 (UX-design-ref.JPG 분석 결과)

- 다크 네이비 셸 + 미세 글로우 카드 톤 차용
- 4 KPI 카드 (라벨/큰숫자/스파크라인/푸터) → silver KPI 4종(D-18)에 1:1 매핑
- 녹색 면적 차트 + 피크 callout chip → EquityChart 첫 시리즈 녹색 고정
- Pill 셀렉터 → 기간 3/5/10년 + 적립금 5종 입력 패널
- **사이드바 nav는 차용 안 함** (D-12 상단 가로 nav, 톤·카드 패턴만 차용)
- 토큰화 필수 (헥스 하드코딩 금지) — `--bg-app/--accent-green` 등 CSS 변수

## Context

### 핵심 참조 파일 (다음 세션 즉시 열어야 함)

1. **`docs/silver-masterplan.md`** — 단일 source of truth (12 섹션, 871줄)
2. `dev/active/project-overall/project-overall-plan.md` — Phase 1~5 매핑, Stage A~E
3. `dev/active/project-overall/project-overall-context.md` — D-1~D-21 결정 표 (코딩 시 매번 확인)
4. `dev/active/project-overall/project-overall-tasks.md` — 29 태스크 체크리스트
5. `.claude/skills/silver-simulation/SKILL.md` — 시뮬레이션 코딩 시 자동 활성화
6. `.claude/skills/frontend-dev/references/silver-design.md` — 프론트 작업 시 함께 로드
7. `docs/UX-design-ref.JPG` — 다크 톤 시각 레퍼런스
8. `dev/archive/bronze-gen/` — Bronze gen 작업 history 보존 (참조용)

### 절대 잊으면 안 되는 제약 (D-lock 핵심)

- **D-7**: 강제 재매수 = "매도일 + 365일" (draft "12월 말" 폐기)
- **D-8**: `lock_until_year`는 **재매수 시점**에 갱신 (매도 시점 X)
- **D-9**: 적립 시작 후 12개월 grace (매도 트리거 무시)
- **D-6**: 60거래일 ratio는 **현지통화** 가격으로 계산 (USD 자산은 USD 가격)
- **D-2**: padding은 가격 직접 복제 X, **수익률 cyclic + reverse-cumprod**
- **D-5**: WBI (Warren Buffett Index) 시드 42 + KRW 자산 (reproducibility)
- **D-17**: 같은 날 적립과 트리거 겹치면 **적립 먼저**, strategy.step() 그 다음
- **D-18**: KPI 4종 이름 고정 (final_asset_krw / total_return / annualized_return / yearly_worst_mdd)

### 환경 / 운영

- Bronze 운영중 (Phase 4 빅뱅 cut-over 전까지 영향 0 유지)
- Agentic AI(Phase F) tool 정리는 Phase 4: strategy_classify/report 제거 + simulation_replay/strategy/portfolio 신규
- 사용자 1명 → 다운타임 영향 0, feature flag 무의미
- A-004 교훈: 프론트 페이지 ↔ Agentic tool이 동일 simulation 함수 호출 (단일 source)

### 미해결 후속 결정 (코딩 중 발생 시 사용자 확인)

- C-2 fractional 정밀도 자릿수 (Phase 2)
- C-4 신호 빈도 "3회/년" 폐기 여부 (Phase 3)
- Tab A 자산 정렬 캘린더 forward-fill (Phase 3)
- 카드형 vs step형 (Phase 3 시안 후)
- 모바일 nav (가로 스크롤 vs hamburger, Phase 3)

## Next Action

### Step 0 — Phase 1 dev-docs 작성 (코딩 진입 전 권장)

새 세션 시작 시 사용자가 `/dev-docs start phase1 silver-rev1-phase1` 같은 형식으로 호출하면:

1. `dev/active/silver-rev1-phase1/` 폴더 생성
2. 표준 3종 작성: `silver-rev1-phase1-plan.md` / `-context.md` / `-tasks.md`
3. `debug-history.md` 빈 헤더 생성
4. project-overall 3종 동기화 (Phase 1 섹션 정합성 확인)
5. 헤더에 `Gen: silver` 명시

### Step 1 — Phase 1 코딩 착수 (P1-1 Alembic migration)

dev-docs 정리 후 즉시 진입 가능. 첫 작업:

1. `docs/silver-masterplan.md` §5.1 SQL 확인
2. **Alembic migration 작성**:
   ```sql
   ALTER TABLE asset_master ADD COLUMN currency VARCHAR(8) NOT NULL DEFAULT 'KRW';
   ALTER TABLE asset_master ADD COLUMN annual_yield NUMERIC(6,4) NOT NULL DEFAULT 0;
   ALTER TABLE asset_master ADD COLUMN history_start_date DATE;
   ALTER TABLE asset_master ADD COLUMN allow_padding BOOLEAN DEFAULT FALSE;
   ALTER TABLE asset_master ADD COLUMN display_name VARCHAR(64);

   CREATE TABLE fx_daily (
       date DATE PRIMARY KEY,
       usd_krw_close NUMERIC(10,4) NOT NULL,
       created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```
   파일명 예: `alembic revision -m "silver_rev1_schema_changes"`
3. 로컬 Alembic upgrade 후 schema 확인
4. P1-2로 진행: `backend/collector/fdr_client.py:14` SYMBOL_MAP 8종 추가
5. 커밋: `[silver-rev1-phase1] Step 1.1: asset_master 5컬럼 + fx_daily migration`

작업 단위 commit convention: `[silver-rev1-phase1] Step X.Y: description`

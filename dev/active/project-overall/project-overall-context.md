# Project Overall Context — Silver Gen
> Gen: silver
> Last Updated: 2026-05-09
> Note: Phase 1 dev-docs 작성됨 (`dev/active/silver-rev1-phase1/`) — Phase 1 상세 컨텍스트는 해당 폴더 참조

## 0. 핵심 원칙 — "Show, don't claim" (Silver gen 전 phase 공통)

> **검증 게이트의 체크박스는 evidence가 본 dev-docs 또는 `verification/step-N.md`에 paste됐을 때만 표시 가능.**
> Claude의 "PASS / 통과" 주장만으로는 mark complete 금지. 사용자가 출력물을 직접 볼 수 있어야 한다.

### 0.1 적용 범위
모든 Phase (1~5) tasks.md의 검증 게이트, Stage 종료 조건, Phase Definition of Done에 일괄 적용.

### 0.2 게이트 작성 표준 (3단 형식, A: Evidence-required)

```markdown
- [ ] <검증 항목>
  - 명령: <실행 가능한 1줄 명령 또는 SQL>
  - Evidence: <어떤 형식의 출력을 어디에 paste할지 명시 — markdown 표 / SQL dump / pytest 출력 / PNG 경로>
  - 통과 기준: <PASS/FAIL을 가르는 구체적 임계 — 숫자, 형식, 일치 여부>
```

### 0.3 verification/ 서브디렉터리 (B: 누적 evidence)

각 Phase 폴더 안에 `verification/` 생성, step별 evidence를 markdown으로 누적.

```
dev/active/silver-rev1-phaseN/
└── verification/
    ├── step-1-<topic>.md      # 명령 + raw output + 해석 3단
    ├── step-2-<topic>.md
    └── ...
```

각 Phase tasks.md의 step 종료 항목에 **`verification/step-N-<topic>.md` 작성 완료**를 sub-step으로 의무화.

### 0.4 시각 산출물 (D: PNG 의무화)

수치/시계열/분포 검증이 포함된 step은 **PNG 차트** 의무. 위치: `verification/figures/<step>-<topic>.png` 또는 fixture 디렉터리.

대상 예시 (Phase별 적용 시점):
- Phase 1: padding 시계열, WBI 가격 시계열 + 일별 수익률 히스토그램, backfill 자산별 row count bar chart
- Phase 2: KPI cross-check (QQQ 10년 적립 결과 vs 외부 도구), strategy A lock 사이클 시각화, MDD 연도별 bar chart
- Phase 3: UI screenshot (모바일 768px / 데스크탑), drawer 동작 캡처
- Phase 4: cut-over 전후 라우트 redirect 캡처, smoke test API 응답 dump
- Phase 5: 사용자 피드백 차트, latency P95 분포

### 0.5 게이트 체크 권한 규칙 (E: Show, don't claim 명문화)

- ✅ **체크 가능**: evidence가 dev-docs 또는 `verification/`에 paste됐고, 사용자가 그 내용을 본 경우
- ❌ **체크 금지**: Claude가 명령을 실행했지만 출력을 사용자에게 노출하지 않은 경우
- ❌ **체크 금지**: "정상", "통과", "smoke OK" 같은 주장만 있고 raw output이 없는 경우
- ⚠️ **회색 영역**: 같은 세션에서 사용자가 직접 본 출력은 evidence로 인정. 그러나 step 종료 시 `verification/` 파일에 정리해 사후 회고 가능하게 보존.

---



## 1. 핵심 참조 파일 (코딩 진입 시 즉시 열어야 함)

### 1.1 기획·명세 (single source of truth)
| 파일 | 용도 |
|---|---|
| `docs/silver-masterplan.md` | **마스터플랜 12 섹션** — 모든 코딩 결정의 기준 |
| `docs/draft-rev1.md` | §1.1 lock 항목 (탭 A 자산, 적립금 프리셋, 이벤트 순서 등) |
| `docs/silver-rev1-analysis.md` | Part B 7대 허들 / Part C Gap Map (리스크 추적) |
| `docs/session-compact.md` | 직전 세션 인계 상태 |
| `docs/UX-design-ref.JPG` | 다크톤 디자인 레퍼런스 |

### 1.2 Bronze gen 코드 진입점 (Silver 작업의 출발점)
| 파일 | 용도 |
|---|---|
| `backend/collector/fdr_client.py:14` | SYMBOL_MAP — Phase 1에서 8종 추가 |
| `backend/db/models/asset_master.py` (or 동등) | Phase 1 컬럼 추가 대상 |
| `backend/research_engine/` | Phase 2 simulation/ 신규 추가 위치 |
| `backend/api/main.py` + `routers/` | Phase 2 라우터 등록 위치 |
| `backend/api/services/llm/agentic/` | Phase 4 tool registration 정리 대상 |
| `frontend/src/App.tsx` | Phase 3 라우트 재편 시작점 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | Phase 3 SignalDetailPage 베이스 |

### 1.3 Bronze gen 보존 자산 (재사용 가능)
| 위치 | 가치 |
|---|---|
| `dev/archive/bronze-gen/` | Phase 1~7, A~G 전체 dev-docs 아카이브 |
| `project-wrapup/lessons-learned.json` | 교훈 41건 (A-004 등 Silver 작업 시 참조) |
| `project-wrapup/reusable-patterns/` | 패턴 9개 (router-service-repo, idempotent-upsert, langraph-classifier 등) |
| `project-wrapup/project-blueprint.md` | 설계 순서도 |

## 2. 데이터 인터페이스 (Silver gen 신규 흐름)

```
[FDR] ──┬─ SYMBOL_MAP(15종) ──→ price_daily (기존 + 8종 신규)
        └─ "USD/KRW"        ──→ fx_daily (신규)

asset_master (5컬럼 추가) ─→ simulation 모듈 (currency/annual_yield/allow_padding 참조)

simulation/ ─┬─ replay.py     ──┐
             ├─ strategy_a.py   │
             ├─ strategy_b.py   ├──→ /v1/silver/simulate/{replay,strategy,portfolio}
             ├─ portfolio.py    │
             ├─ padding.py      │   (매 요청 재계산, rev1은 캐시 없음)
             ├─ wbi.py          │
             ├─ fx.py           │
             └─ mdd.py          ┘

fx_daily ──→ /v1/fx/usd-krw

Agentic LangGraph state machine (Bronze 유지)
  ├─ tools 제거: strategy_classify, strategy_report
  ├─ tools 신규: simulation_replay, simulation_strategy, simulation_portfolio
  └─ tools 유지: dashboard_summary, price_lookup, correlation_matrix
```

## 3. 주요 결정사항 (Silver gen 핵심 lock)

> 마스터플랜 §0 인터뷰 답변 21건 + §1.1 lock 6건 = 총 27 결정. 여기는 코딩 시 매번 확인할 항목만 발췌.

| # | 결정 | 출처 | 코딩 영향 |
|---|---|---|---|
| D-1 | JEPY → JEPI 통일 | Q1-1 | SYMBOL_MAP, asset_master.display_name |
| D-2 | history padding = **일별 수익률 cyclic 복제** (가격 점프 X) | Q1-2 | `padding.py` 알고리즘 + 차트 회색 영역 |
| D-3 | USD/KRW 신규 테이블 `fx_daily` | Q1-3 | Phase 1 migration + fx_collector |
| D-4 | 배당 = 공시 연 배당률 / 252 균등 분할 | Q1-4 | `replay.py` 보유분에 매일 (1+rate) 적용 |
| D-5 | WBI (Warren Buffett Index) = 거래일 등비 + GBM(σ=1%/일, drift 보정), 시드 42, **KRW 자산** | Q2-5/6 | `wbi.py` reproducibility 보장 |
| D-6 | 트리거 통화 = **현지통화 가격 기준** | Q3-9 | `strategy_a.py` 60거래일 ratio는 USD 가격으로 |
| D-7 | 전략 A: 강제 재매수 = **매도일 + 365일** (draft 12월 X) | Q4-11 | `strategy_a.py` `forced = date >= sell_date + 365d` |
| D-8 | 전략 A: lock 범위 = **매도해 ~ 재매수해 포함** | Q4-13 | `lock_until_year` state, 같은 해 매도 시그널 무시 |
| D-9 | 전략 A: grace period = **12개월** | Q4-14 | 적립 시작일 + 12개월 안에 매도 트리거 무시 |
| D-10 | MDD = **캘린더 연도** 기준 | Q5-15 | `mdd.py` Jan-Dec 슬라이스 |
| D-11 | UI = 상단 가로 nav + `+` 버튼 drawer + 모바일 필수 | Q6-16/18/20 | `TabNav`, `AssetPickerDrawer`, 768px breakpoint |
| D-12 | chat/AI = Bronze Phase F **그대로 유지** | Q6-19 | LangGraph state machine 그대로, tool만 정리 |
| D-13 | 신호 카드 = 개별 RSI/MACD/ATR + 상태 라벨 (종합 점수 X) | Q7-21 | `IndicatorCard.tsx` |
| D-14 | Bronze→Silver = **빅뱅 교체** (사용자 1명, 다운타임 0 영향) | Q8-24 | Phase 4 cut-over, feature flag/점진 전환 무의미 |
| D-15 | StrategyPage drop = **DB 테이블도 drop** | Q8-26 | `backtest_run/equity_curve/trade_log` DROP migration |
| D-16 | 이벤트 순서 lock: **정기 적립 후 조건 실행** | §1.1 | `replay.py` 적립 → `strategy_a.step()` 순서 |
| D-17 | KPI 4종 = 최종자산 / 총수익률 / 연환산 / 연도 MDD | §1.1 + §1.2 | `compute_kpi()` 시그니처 고정 |
| D-18 | Tab A universe = QQQ/SPY/KS200/SCHD/JEPI/WBI **6종** | §8.2 | AssetPickerDrawer 옵션 |
| D-19 | Tab B 자산 = QQQ/SPY/KS200 **3종만** | §9.2 | 전략 A/B universe 제한 |
| D-20 | Tab C preset = **4개 고정**, 사용자 비중 편집 불가 | §10.5 | preset 상수 + select UI |
| D-21 | 신호 자산 = QQQ/SPY/KS200/NVDA/GOOGL/TSLA/SEC/SKH **8종** | §12.3 | SignalDetailPage 자산 select |

## 4. 컨벤션 체크리스트

### 4.1 인코딩 (Windows + Korean)
- CSV read: `encoding='utf-8-sig'` (BOM)
- File write: `encoding='utf-8'` 명시
- Python stdout: `PYTHONUTF8=1`
- HTTP JSON: `.json()` 자동 UTF-8

### 4.2 커밋 / 브랜치
- 커밋: `[silver-rev1-phaseN] Step X.Y: description`
- 브랜치: `feature/silver-rev1` (Phase 4 master merge 직전 `v-bronze-final` tag)

### 4.3 Bash / PowerShell (CLAUDE.md 규칙)
- Git Bash에서 Windows 경로는 `/c/...` 형식
- PowerShell `$` 변수: Bash tool에서 .ps1 파일로 분리 작성 → 실행 → cleanup
- `&&` 체인 금지 (개별 병렬 호출로 분리)

### 4.4 LLM 모델
- reasoning (gpt-5-mini/nano): `max_completion_tokens` 사용 (`temperature/max_tokens` 미지원)
- non-reasoning (gpt-4.1-mini): Reporter 전용, `temperature=0` 가능

### 4.5 서버 안정성
- uvicorn --reload 불안정 시: `tasklist | grep python` → `taskkill //F //PID <pid>` 전부 종료 후 재시작
- 백그라운드 task에 요청 스코프 DB 세션 전달 금지 → 자체 `SessionLocal()` 생성

### 4.6 데이터 / DB
- 자산별 캘린더 차이: forward-fill 가정 (Phase 2 시각적 검증)
- fractional 정밀도: 12자리 가정 (D-22 후속 결정 필요)
- DEFAULT 값으로 backward-compatible 컬럼 추가 (Phase 1 Bronze 영향 0 보장)

### 4.7 컨벤션 ENFORCEMENT
- API: Router-Service-Repo 분리 (project-wrapup 패턴)
- OHLCV: schema 검증 (collector)
- Pydantic schemas for all I/O
- FastAPI DI for services

### 4.8 검증 게이트 형식 (Silver gen 표준 — §0 참조)
- 모든 게이트 = **명령 / Evidence 형식 / 통과 기준** 3단
- 각 step 종료 시 `verification/step-N-<topic>.md` 작성 의무
- 수치·시계열·분포 step = PNG 차트 의무 (`verification/figures/`)
- 체크 표시는 evidence가 paste되고 사용자가 본 경우에만 가능

## 5. 미해결 후속 결정 (마스터플랜 §11.3 발췌)

| 항목 | 결정 시점 |
|---|---|
| C-2 fractional 정밀도 자릿수 | Phase 2 코딩 중 사용자 확인 |
| C-4 신호 빈도 "3회/년" 폐기 여부 | Phase 3 시안 검토 |
| Tab A 자산 정렬 캘린더 (forward-fill 가정) | Phase 3 시각 검증 |
| 시뮬레이션 결과 캐시 | Phase 5 (P95 임계 시) |
| 실제 배당락 데이터 도입 | Phase 5 |
| 데이터 alerting 신규 자산 확장 | Phase 1 후반 |
| 카드형 vs step형 (§6.2 lock) | Phase 3 시안 후 |
| 모바일 nav 동작 (가로 스크롤 vs hamburger) | Phase 3 시안 후 |

## 5b. Phase 4 추가 결정사항 (prod 버그 수정)

| # | 결정 | 출처 | 코딩 영향 |
|---|---|---|---|
| D-P4-4 | WBI GBM drift 재스케일링 — 항상 20% CAGR 보장 | prod 버그 C | `wbi.py`: target_log 기반 drift_per_day 조정 |
| D-P4-5 | simulation_service `_load_price_and_fx` NaN 필터 의무화 | prod 버그 B | `r.close is not None` + `.dropna()` |
| D-P4-6 | DCA annualized < 자산 CAGR = 정상 (평균 투자 기간 ≈ period/2) | prod 버그 C 분석 | UI 라벨/설명에 "DCA 기준 연환산" 명시 권장 |

## 6. Bronze gen 핵심 교훈 적용 (project-wrapup/lessons-learned)

- **A-004 (대시보드 ↔ Agentic 데이터 소스 일치)**: Silver에서도 chat이 호출하는 simulation_* tool과 프론트가 호출하는 `/v1/silver/simulate/*`가 동일 함수를 거치도록 설계
- **PERF-1 (Reporter 모델 분리)**: Silver Phase 5에서 LLM 해설 카드 도입 시 reasoning vs non-reasoning 모델 분리 유지
- **운영 안정성**: 빅뱅 cut-over 직후 1주 monitoring (Phase 4)
- **재사용 패턴**: `langraph-classifier.py`, `router-service-repo.py`, `idempotent-upsert.py`, `cascade-fk-models.py` 모두 Silver 작업에서 그대로 적용 가능

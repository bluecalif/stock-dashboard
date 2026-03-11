# Project Overall Context
> Last Updated: 2026-03-11
> Status: MVP 완료 (Phase 0~7), Post-MVP Phase A 착수 예정

## 핵심 파일

| 파일 | 용도 |
|------|------|
| `docs/masterplan-v0.md` | MVP 설계 명세서 (아키텍처, DB 스키마, API 12개, 프론트엔드 6페이지) |
| `docs/post-mvp-implementation-sketch.md` | Post-MVP 제품 요구사항 (대화형 분석 워크스페이스) |
| `docs/session-compact.md` | 현재 진행 상태 |
| `.claude/plans/snuggly-growing-willow.md` | Post-MVP 전체 구현 계획 |
| `CLAUDE.md` | 프로젝트 규칙, 기술 스택, 컨벤션 |
| `.claude/skills/backend-dev/SKILL.md` | 백엔드 개발 가이드 (Auth 패턴 포함) |
| `.claude/skills/frontend-dev/SKILL.md` | 프론트엔드 개발 가이드 (Zustand, SSE, ProtectedRoute 포함) |
| `.claude/skills/langgraph-dev/SKILL.md` | LangGraph + Gemini 에이전트 가이드 |
| `dev/active/phaseA-auth/` | Phase A (Auth) dev-docs (plan/context/tasks/debug) |

## 주요 결정사항

### MVP 결정사항
| 일자 | 결정 | 근거 |
|------|------|------|
| 2026-02-10 | Kiwoom OpenAPI 폐기 | 32비트 Python 요구, DLL 잠금 이슈 |
| 2026-02-10 | FDR 단일 소스 (Week 1-4) | 전 자산 검증 통과, 통합 간편 |
| 2026-02-10 | Hantoo fallback 이연 (v0.9+) | 배포 직전 국내주식 이중화 |
| 2026-02-10 | Dashboard: React + Recharts + Vite + TS | 시각화 라이브러리 풍부, 타입 안전성 |
| 2026-02-10 | DB Migration: Alembic | SQLAlchemy 네이티브 통합 |
| 2026-02-10 | 알림: Discord Webhook | 무료, 설정 간편 |
| 2026-02-12 | 상관행렬: API on-the-fly 계산 | 별도 DB 테이블 불필요, 7자산 소규모 |
| 2026-02-12 | Phase 구조 리비전 | Phase 4(API), Phase 5(Frontend) 분리 |
| 2026-02-13 | Frontend: TailwindCSS 채택 | 유틸리티 CSS, 빠른 프로토타이핑 |
| 2026-02-13 | Frontend: React useState + useEffect | MVP 수준에서 별도 상태 라이브러리 불필요 |
| 2026-02-14 | missing_threshold 10%로 상향 | 한국주식 공휴일 캘린더 차이 |
| 2026-02-14 | NaN 방어: API 스키마 field_validator | DB NaN → JSON 직렬화 실패 방지 |
| 2026-02-15 | Phase 7: GitHub Actions cron | 무료, 기존 CI/CD 인프라 활용 |
| 2026-02-15 | Railway Public Networking | GitHub Actions → Railway DB 직접 접속 |
| 2026-02-15 | cron UTC 09:00 (KST 18:00) | 한국 장 마감 후 충분한 여유 |

### Post-MVP 결정사항 (2026-03-10 확정)
| 항목 | 결정 | 근거 |
|------|------|------|
| Auth | JWT 자체 구현 (python-jose + passlib) | 외부 서비스 의존 없이 제어 가능 |
| LLM 플랫폼 | **LangGraph** (langgraph + langchain-core + langchain-google-genai) | 명시적 그래프, SSE 이벤트 분리, 내장 checkpointer |
| LLM 모델 | **Gemini 3.1 Pro** (메인) + **Gemini 3.1 Flash Lite** (분류/온보딩) | 비용 효율 (OpenAI → Claude → Gemini 비교 후) |
| Chat 프로토콜 | SSE 스트리밍 (FastAPI StreamingResponse) | WebSocket 대비 구현 간편, HTTP 호환 |
| 상태 관리 | Zustand 추가 (기존 hooks 유지, 공유 상태만 store) | 공유 상태 관리 필요 (auth, chat, chart) |
| Embedding | Phase E 진입 시 결정 (Gemini embedding 또는 OpenAI) | 아직 벡터 검색 요구 불확실 |
| Vector DB | pgvector (Railway 지원 확인 필요) | 기존 Postgres 내 관리, 운영 단순 |
| 비용 제어 | 초기 제한 없음, 토큰 사용량 컬럼 미리 설계 | 사용량 추적 후 제한 설정 |
| 기존 API | auth 없이 하위 호환 유지 | 기존 공개 엔드포인트 접근성 유지 |
| 페이지 재편 | 홈/가격/상관/지표시그널/전략 (팩터+시그널 통합) | 사용자 관점 단순화 |

## 자산 목록

| asset_id | 이름 | 카테고리 | FDR 심볼 |
|----------|------|----------|----------|
| KS200 | KOSPI200 | index | KS200 |
| 005930 | 삼성전자 | stock | 005930 |
| 000660 | SK하이닉스 | stock | 000660 |
| SOXL | SOXL ETF | etf | SOXL |
| BTC | Bitcoin | crypto | BTC/KRW |
| GC=F | Gold | commodity | GC=F |
| SI=F | Silver | commodity | SI=F |

## DB 테이블

### MVP 테이블 (8개, 운영 중)
1. `asset_master` — 자산 마스터 (7개 시드)
2. `price_daily` — 일봉 PK: (asset_id, date, source) — 5,573+ rows
3. `factor_daily` — 팩터 PK: (asset_id, date, factor_name, version)
4. `signal_daily` — 전략 신호
5. `backtest_run` — 백테스트 실행 (run_id UUID PK)
6. `backtest_equity_curve` — 에쿼티 커브
7. `backtest_trade_log` — 트레이드 로그
8. `job_run` — 작업 실행 이력

### Post-MVP 신규 테이블 (9개, 계획)
9. `users` — 사용자 (Phase A)
10. `user_sessions` — 리프레시 토큰 세션 (Phase A)
11. `chat_sessions` — 채팅 세션 (Phase B)
12. `chat_messages` — 채팅 메시지 (Phase B)
13. `chart_presets` — 차트 프리셋 (Phase D)
14. `user_memories` — 사용자 메모리 (Phase E)
15. `retrieval_chunks` — 벡터 임베딩 (Phase E)
16. `analysis_snapshots` — 분석 스냅샷 (Phase E)
17. `onboarding_profiles` — 온보딩 프로필 (Phase F)

## API 엔드포인트

### MVP API (v1) — 12개 운영 중

#### 조회 API (5개)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/health` | 헬스체크 |
| GET | `/v1/assets` | 자산 목록 |
| GET | `/v1/prices/daily` | 가격 조회 |
| GET | `/v1/factors` | 팩터 조회 |
| GET | `/v1/signals` | 시그널 조회 |

#### 백테스트 API (5개)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/backtests/run` | 온디맨드 백테스트 |
| GET | `/v1/backtests` | 백테스트 목록 |
| GET | `/v1/backtests/{run_id}` | 백테스트 요약 |
| GET | `/v1/backtests/{run_id}/equity` | 에쿼티 커브 |
| GET | `/v1/backtests/{run_id}/trades` | 거래 이력 |

#### 집계 API (2개)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/dashboard/summary` | 대시보드 요약 |
| GET | `/v1/correlation` | 상관행렬 |

### Post-MVP API — 계획

#### Auth API (Phase A)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/auth/signup` | 회원가입 |
| POST | `/v1/auth/login` | 로그인 |
| POST | `/v1/auth/refresh` | 토큰 갱신 |
| GET | `/v1/auth/me` | 내 정보 |

#### Chat API (Phase B)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/chat/sessions` | 채팅 세션 생성 |
| GET | `/v1/chat/sessions/{session_id}` | 세션 조회 |
| POST | `/v1/chat/sessions/{session_id}/messages` | 메시지 전송 (SSE) |

#### Analysis API (Phase C)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/analysis/correlation/explain` | 상관도 설명 |
| POST | `/v1/analysis/indicators` | 지표 해석 |
| POST | `/v1/analysis/strategies/compare` | 전략 비교 |

#### Preferences / Memory / Onboarding API (Phase D~F)
| Method | Path | Phase |
|--------|------|-------|
| GET | `/v1/preferences/charts` | D |
| PUT | `/v1/preferences/charts/{preset_id}` | D |
| POST | `/v1/chart-actions/preview` | D |
| GET/POST/DELETE | `/v1/memory` | E |
| POST | `/v1/retrieval/query` | E |
| POST | `/v1/onboarding/start` | F |
| POST | `/v1/onboarding/answers` | F |
| GET | `/v1/onboarding/profile` | F |

## 프론트엔드 페이지

### MVP 페이지 (6개, 운영 중)
| # | 페이지 | 주요 API 소비 | 차트 종류 |
|---|--------|-------------|----------|
| 1 | 대시보드 홈 | `/dashboard/summary` | 요약 카드 + 미니 라인 |
| 2 | 가격/수익률 | `/prices/daily` | 라인/캔들 + 정규화 비교 |
| 3 | 상관 히트맵 | `/correlation` | 히트맵 (Recharts) |
| 4 | 팩터 현황 | `/factors` | RSI/MACD 서브차트 |
| 5 | 시그널 타임라인 | `/signals` + `/prices/daily` | 가격 + 매매 마커 |
| 6 | 전략 성과 | `/backtests/*` | 에쿼티 커브 + 메트릭스 |

### Post-MVP 페이지 변경 (계획)
- 팩터 + 시그널 → **지표 시그널** 통합 (Phase D)
- **채팅 패널**: 우측 슬라이드 (Phase B)
- **로그인/회원가입**: 인증 페이지 (Phase A)
- 최종 구조: 홈 / 가격 / 상관 / 지표시그널 / 전략 + 채팅 패널

## 컨벤션 체크리스트

### 데이터 관련 ✅
- [x] OHLCV 표준 스키마 준수
- [x] FDR primary source 사용
- [x] idempotent UPSERT
- [x] 지수 백오프 재시도
- [x] 정합성 검증

### API 관련 ✅
- [x] Router → Service → Repository 3계층
- [x] Pydantic 스키마 정의
- [x] 의존성 주입 패턴
- [x] CORS 설정
- [x] Pagination (limit/offset)

### 인코딩 관련 ✅
- [x] CSV/File read: `encoding='utf-8-sig'`
- [x] File write: `encoding='utf-8'` explicit
- [x] `PYTHONUTF8=1` 환경변수

### 배포/운영 관련
- [x] 환경변수 하드코딩 금지
- [x] `.env` 파일 gitignore
- [x] CORS 화이트리스트
- [x] GitHub Secrets 시크릿 관리
- [x] CI 파이프라인 (lint + test + build)
- [x] GitHub Actions cron 일일 자동 수집
- [ ] DB TLS 연결 강제
- [ ] DB 백업 + 복구 절차 검증

### Post-MVP 컨벤션 (신규)
- [ ] JWT 토큰 Bearer 헤더 전달
- [ ] get_current_user / get_current_user_optional DI 패턴
- [ ] 기존 공개 API optional auth 유지
- [ ] SSE 이벤트 포맷 (text_delta, tool_call, tool_result, ui_action, done)
- [ ] Zustand store 분리 (authStore, chatStore, chartStore)
- [ ] LangGraph Tool JSON schema 검증
- [ ] 사용자 데이터 user_id 기준 격리

## 배포 인프라

| 항목 | 선택 | 상태 |
|------|------|------|
| 프론트엔드 호스팅 | Vercel | ✅ 운영 중 |
| 백엔드 호스팅 | Railway | ✅ 운영 중 |
| DB 호스팅 | Railway PostgreSQL | ✅ 운영 중 |
| CI/CD | GitHub Actions | ✅ 운영 중 |
| 일일 수집 | GitHub Actions cron | ✅ 운영 중 |
| 알림 | Discord Webhook | ✅ 운영 중 |
| LLM API | Google Gemini | 계획 (Phase B) |
| Vector 확장 | pgvector | 계획 (Phase E) |

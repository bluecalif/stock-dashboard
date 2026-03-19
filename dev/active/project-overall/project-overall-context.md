# Project Overall Context
> Last Updated: 2026-03-19
> Status: MVP 완료 (Phase 0~7), Phase A~F 완료, Phase G~H 미시작

## 핵심 파일

| 파일 | 용도 |
|------|------|
| `docs/masterplan-v0.md` | MVP 설계 명세서 (아키텍처, DB 스키마, API 12개, 프론트엔드 6페이지) |
| `docs/post-mvp-implementation-sketch.md` | Post-MVP 제품 요구사항 (대화형 분석 워크스페이스) |
| `docs/session-compact.md` | 현재 진행 상태 |
| `.claude/plans/snuggly-growing-willow.md` | Post-MVP 전체 구현 계획 |
| `docs/post-mvp-phaseCD-detail.md` | Phase C~E 통합 상세 계획 (31 Steps) |
| `CLAUDE.md` | 프로젝트 규칙, 기술 스택, 컨벤션 |
| `.claude/skills/backend-dev/SKILL.md` | 백엔드 개발 가이드 (Auth 패턴 포함) |
| `.claude/skills/frontend-dev/SKILL.md` | 프론트엔드 개발 가이드 (Zustand, SSE, ProtectedRoute 포함) |
| `.claude/skills/langgraph-dev/SKILL.md` | LangGraph + Gemini 에이전트 가이드 |
| `dev/active/phaseA-auth/` | Phase A (Auth) dev-docs — ✅ 완료 |
| `dev/active/phaseB-chatbot/` | Phase B (Chatbot) dev-docs (plan/context/tasks/debug) |
| `dev/active/phaseC-correlation/` | Phase C (상관도 페이지) dev-docs |
| `dev/active/phaseD-indicators/` | Phase D (지표 페이지) dev-docs — ✅ 완료 |
| `dev/active/phaseD-revision/` | Phase D-rev (지표 피드백) dev-docs — 12/13 완료 |
| `dev/active/phaseE-strategy/` | Phase E (전략 페이지) dev-docs — ✅ 완료 |
| `dev/active/phaseF-agentic/` | Phase F (Agentic Flow) dev-docs — ✅ 완료 |

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
| Auth | JWT 자체 구현 (python-jose + bcrypt) | 외부 서비스 의존 없이 제어 가능, passlib 제거 (bcrypt 5.x 호환) |
| LLM 플랫폼 | **LangGraph** (langgraph + langchain-core + langchain-openai) | 명시적 그래프, SSE 이벤트 분리, 내장 checkpointer |
| LLM 모델 | **OpenAI GPT-5** (심층) + **GPT-5 Mini** (기본) | Gemini 쿼타 초과 (429)로 전환, 심층모드 토글 |
| Chat 프로토콜 | SSE 스트리밍 (FastAPI StreamingResponse) | WebSocket 대비 구현 간편, HTTP 호환 |
| 상태 관리 | Zustand 추가 (기존 hooks 유지, 공유 상태만 store) | 공유 상태 관리 필요 (auth, chat, chart) |
| Embedding | Phase F 진입 시 결정 (OpenAI embedding) | 아직 벡터 검색 요구 불확실 |
| Vector DB | pgvector (Railway 지원 확인 필요) | 기존 Postgres 내 관리, 운영 단순 |
| 비용 제어 | 초기 제한 없음, 토큰 사용량 컬럼 미리 설계 | 사용량 추적 후 제한 설정 |
| 기존 API | auth 없이 하위 호환 유지 | 기존 공개 엔드포인트 접근성 유지 |
| 페이지 재편 | 홈/가격/상관/지표시그널/전략 (팩터+시그널 통합) | 사용자 관점 단순화 |
| Phase C~E 통합 | 기존 C(분석)+D(그래프커스텀) → 페이지별 분리(C/D/E) | 각 페이지를 백엔드+프론트+챗봇까지 완결 후 다음 이동 |
| 하이브리드 분류기 | 정규표현식+키워드 (LLM intent 안 씀) | 레이턴시 최소화, 실패 시 LangGraph fallback |
| 스토리텔링 | 하드코딩 템플릿+f-string | 추상 점수 금지, 실제 금액/수익률만 사용 |
| on-the-fly 백테스트 | DB 저장 안 함 | DB에 없는 기간 조합도 즉시 비교 가능 |
| REST 분석 API | 성공률/전략비교용 1개 라우터 추가 | 페이지 렌더링용 REST 병행 (챗봇 중심 유지) |
| 지표별 시그널 | on-the-fly 생성 (DB 저장 없음) | factor_daily에서 파생 가능, 신규 테이블 불필요 |
| 전략→지표 전환 | 기존 strategy 기반 API 하위호환 유지 | Phase E 전략 페이지에서 사용 |
| 전략 재정의 (E) | 모멘텀=MACD, 역발상=RSI, 위험회피=ATR+vol | indicator_signal_service 시그널 기반 백테스트 |
| 1년단위 구간 평가 (E) | 연도별 전략 적합도 표시 | 수익률>0 AND win_rate>50% 기준 |
| Best/Worst annotation (E) | 그래프 내 효과 큰/실패 구간 visual 삽입 | ReferenceArea + 금액 라벨 |
| 위험회피 손실 회피 (E) | B&H 대비 절감된 손실 금액 표시 | ATR+vol 전략 전용 |
| 2-Step LLM Agentic (F) | Classifier(gpt-5-mini) + Reporter(deep_mode 선택) | 다단계 에이전트 대비 레이턴시/비용 최소화, LLM 최대 2회 |
| regex classifier 제거 (F) | LLM Structured Output으로 완전 대체 | 확장성 + 페이지 간 라우팅 가능 |
| 자동 네비게이션 (F) | 즉시 이동 (확인 없음) | Agentic AI UX 극대화 |
| 하드코딩 템플릿 제거 (F) | LLM Reporter로 대체 | 자연스러운 큐레이팅 분석 + 동적 follow-up |
| is_nudge 하위호환 (F) | 파라미터 유지, 내부 무시 | 프론트/백 배포 시점 불일치 방지 |
| confidence threshold (F) | 0.5 미만 시 LangGraph fallback | 분류 실패 안전망 |
| UIActionModel Literal (F) | action 필드를 Literal 타입으로 제한 | LLM hallucination 방지 |
| with_structured_output 폐기 (F) | JSON mode(`response_format=json_object`) + 수동 파싱 | 프로덕션에서 `with_structured_output` 지속 실패 |
| DataFetcher asset_ids 방어 (F) | 상관 tool에 2개 미만 자산 시 None 전달 (전체 자산) | LLM 출력 validation 필수 |

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
13. `chart_presets` — 차트 프리셋 (Phase F 이후)
14. `user_memories` — 사용자 메모리 (Phase G)
15. `retrieval_chunks` — 벡터 임베딩 (Phase G)
16. `analysis_snapshots` — 분석 스냅샷 (Phase G)
17. `onboarding_profiles` — 온보딩 프로필 (Phase H)

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

#### Analysis API (Phase D~E)
| Method | Path | 설명 | Phase |
|--------|------|------|-------|
| GET | `/v1/analysis/signal-accuracy` | 지표 매수/매도 성공률 | D |
| GET | `/v1/analysis/indicator-comparison` | 지표 예측력 비교 | D |
| POST | `/v1/analysis/strategy-backtest` | 전략 백테스트 (indicator 시그널 기반, on-the-fly) | E |

#### Memory / Onboarding API (Phase G~H)
| Method | Path | Phase |
|--------|------|-------|
| GET/POST/DELETE | `/v1/memory` | G |
| POST | `/v1/retrieval/query` | G |
| POST | `/v1/onboarding/start` | H |
| POST | `/v1/onboarding/answers` | H |
| GET | `/v1/onboarding/profile` | H |

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
- **로그인/회원가입**: 인증 페이지 (Phase A) ✅
- **채팅 패널**: 우측 슬라이드 (Phase B) ✅
- **상관도 페이지 확장**: 그룹핑 카드 + ScatterPlot + SpreadChart + 넛지 질문 + 관심 종목 (Phase C)
- **지표 시그널 통합 페이지**: 팩터+시그널 통합, 성공률 탭, 오버레이 차트, 설정 패널 (Phase D)
- **전략 페이지 고도화**: 전략 백테스트(모멘텀/역발상/위험회피), 연간 성과, Best/Worst annotation, 내러티브, 기간 설정 (Phase E)
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
- [x] JWT 토큰 Bearer 헤더 전달
- [x] get_current_user / get_current_user_optional DI 패턴
- [x] 기존 공개 API optional auth 유지
- [x] SSE 이벤트 포맷 (text_delta, tool_call, tool_result, done)
- [x] Zustand authStore 구현 완료
- [x] Zustand chatStore (Phase B 완료, deepMode 포함)
- [x] Zustand chartActionStore (Phase C) ✅
- [x] Zustand watchlistStore (Phase C) ✅
- [x] 하이브리드 분류기 (정규표현식+키워드) (Phase C) ✅
- [x] 분석 REST API (Phase D~E) ✅
- [x] LangGraph Tool 확장 (5→9개) (Phase C~E) ✅
- [x] Agentic Flow: 2-Step LLM JSON mode (Phase F) ✅
- [x] Agentic Flow: 자동 페이지 네비게이션 (Phase F) ✅
- [x] Agentic Flow: 동적 follow-up 질문 (Phase F) ✅
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
| LLM API | OpenAI GPT-5 / GPT-5 Mini | ✅ 운영 중 |
| Vector 확장 | pgvector | 계획 (Phase F) |

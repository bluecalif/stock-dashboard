# Phase G: User Context & Guided Experience — Debug History
> Last Updated: 2026-03-20

## Stage G-1: User Profile & Behavior Tracking

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| G1-1 | profile_repo | `jsonb_set` nested path 생성 불가 (중간 키 없으면 실패) | 상위 키를 `'{}'::jsonb`로 보장하는 2-step 접근 | `profile_repo.py` |
| G1-2 | profile_repo | `activity_data`가 `json` 타입인데 `jsonb_set` 결과 타입 불일치 | `::json` 캐스트 추가 | `profile_repo.py` |
| G1-3 | profile_repo | `try/except`에서 에러 무시 → 200 OK 반환, 데이터 미저장 | 에러 로깅 강화 | `profile_repo.py` |

### G1-1/G1-2: jsonb_set nested path + json 타입 캐스트

**증상**: `increment_activity()`, `record_page_visit()`에서 `page_visits.prices` 같은 nested 경로 저장 실패. API는 200 OK 반환하지만 DB 데이터 없음.

**원인**:
1. PostgreSQL `jsonb_set`은 중간 키(`page_visits`)가 없으면 `{page_visits, prices}` 경로 생성 불가
2. `activity_data` 컬럼이 `json` 타입이므로 `jsonb_set` 결과를 `::json`으로 캐스트해야 함

**수정**: 상위 키 존재 보장 쿼리 추가 + `::json` 캐스트

## Stage G-2: Conversation Memory

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| G2-1 | chat_service | `_run_summary()`가 요청 스코프 db 세션을 asyncio.ensure_future로 전달 → 세션 닫힘 후 실패 | 자체 `SessionLocal()` 세션 생성 + `try/finally` close | `chat_service.py` |

### G2-1: _run_summary 요청 스코프 DB 세션 누출

**증상**: `conversation_summaries` 테이블 0건. 24개 메시지 세션 존재에도 요약 미생성. `user_profiles.top_assets`/`top_categories` NULL.

**원인**: `_maybe_trigger_summary()`가 `asyncio.ensure_future(_run_summary(db, ...))` 호출. `db`는 FastAPI `get_db()` 의존성으로 요청 스코프. 스트리밍 응답 완료 후 `get_db()` finally 블록에서 `db.close()` → 백그라운드 태스크가 닫힌 세션 사용.

**수정**: `_run_summary()`에서 `db` 파라미터 제거, `SessionLocal()`로 자체 세션 생성, `try/finally`로 세션 close 보장.

## Stage G-3: Context-Aware Response & Guide

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| (버그 없음) | | | | |

## E2E 브라우저 테스트 버그

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| E2E-1 | chat.ts | SSE fetch가 axios 인터셉터 밖 → 401 시 토큰 갱신 안 됨 | `sendMessageSSE` 내 401 감지 + refresh + 재시도 로직 | `frontend/src/api/chat.ts` |
| E2E-2 | reporter.py | 복잡한 분석 질문에서 30초 타임아웃 부족 | request_timeout 30s → 45s, 에러 로그 강화 | `reporter.py` |
| E2E-3 | tools.py | LLM이 신호 성공률 null을 "산출 불가"로 오해 | `note` 필드 추가 + knowledge_prompts 가이드 | `tools.py`, `knowledge_prompts.py` |
| E2E-4 | tools.py | 그래프 API vs LLM API 신호 성공률 데이터 소스 불일치 | ⚠️ 미수정 — `analyze_indicators` 툴이 strategy-based 사용, 그래프는 indicator-based | `tools.py` |

| E2E-5 | chat_service | Agentic 플로우에서 이전 대화 히스토리 미전달 → "아까 그 종목" 참조 불가 | Classifier+Reporter에 최근 3턴 `chat_history` 전달 | `chat_service.py`, `classifier.py`, `reporter.py` |
| E2E-6 | chat_service | `unsupported` 질문 하드코딩 거부 → 일반 대화 불가 ("한국의 수도는") | unsupported → LangGraph fallback 라우팅 | `chat_service.py` |
| E2E-7 | prompts.py | LangGraph 시스템 프롬프트 "반드시 도구 호출" → 일반 질문도 도구 강제 | 일반 대화는 도구 없이 직접 답변 허용 | `prompts.py` |
| E2E-8 | 서버 관리 | uvicorn --reload가 변경 감지 못함 + 좀비 프로세스 잔류 → 코드 변경 미반영 | 전체 Python 프로세스 kill → 새 서버 시작 | (운영) |

### E2E-5: Agentic 플로우 대화 히스토리 미전달

**증상**: 사용자가 "방금 그 종목 RSI 알려줘" 등 이전 대화 참조 시 맥락 인식 불가.

**원인**: Agentic 플로우(Classifier → DataFetcher → Reporter)는 `[system, user_msg]` 2개 메시지만 LLM에 전달. LangGraph fallback은 MemorySaver checkpointer로 히스토리 유지하지만, Agentic이 주요 경로.

**수정**:
1. `chat_service.py`: 현재 user 메시지 제외한 최근 6개(3턴) 메시지를 `_history`로 추출
2. `classifier.py`: `_build_user_message()`에 `## 이전 대화` 섹션 추가 (내용 100자 요약)
3. `reporter.py`: `_build_user_message()`에 `## 이전 대화` 섹션 추가 (내용 200자 요약)

### E2E-6/E2E-7: unsupported 질문 라우팅 + LangGraph 프롬프트

**증상**: "한국의 수도는" → "이 질문은 저의 분석 범위를 벗어납니다" 거부 메시지. 3차례 서버 재시작 후에도 동일 증상 → 좀비 프로세스 원인.

**원인 (코드)**: `unsupported` 카테고리일 때 하드코딩 거부 메시지 반환 후 `return`. LangGraph 시스템 프롬프트도 "반드시 도구 호출" 강제.

**원인 (서버)**: uvicorn `--reload`가 Windows에서 간헐적 파일 변경 감지 실패. 이전 서버 프로세스(PID 22960, 10356)가 좀비로 잔류, 새 프로세스와 포트 충돌 없이 공존하면서 이전 코드 서빙.

**수정**:
1. `chat_service.py`: `unsupported` 카테고리 거부 블록 제거, `use_agentic` 조건에 `"unsupported"` 추가
2. `prompts.py`: "반드시 도구를 호출하여" → "자산/투자 관련 질문에는 반드시 도구를 호출하여", 일반 대화 직접 답변 허용
3. 서버 관리: `tasklist`로 전체 Python 프로세스 확인 → `taskkill //F //PID` 전부 종료 → 새 서버 시작

### E2E-4: 신호 성공률 데이터 소스 불일치 (미수정)

**증상**: 대시보드 그래프에는 RSI/MACD 성공률 표시되지만, 챗봇은 "산출 불가" 응답.

**원인**: `analyze_indicators` 툴(Phase D.5)이 `compute_signal_accuracy(strategy_id)` 사용. 그래프는 `compute_indicator_accuracy(indicator_id)` 사용 (Phase DR.2에서 추가). D.5 시점에 indicator-based 함수 미존재 → LLM 툴 미업데이트.

**수정 계획**: `analyze_indicators`에 `compute_indicator_accuracy("rsi_14"/"macd")` 호출 추가 → `indicator_accuracy` 키로 반환. plan 파일 참조.

## Post-Phase: Timeframe & Sorting 버그 (7건)

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| TF-1 | dashboard_service | `get_prices(limit=2)` → asc 정렬로 가장 오래된 2개 반환 → 대시보드 홈 가격이 3년 전 데이터 | `get_latest_prices(n=2)` 신규 함수 (desc 정렬) 사용 | `price_repo.py`, `dashboard_service.py` |
| TF-2 | tools.py | `get_prices(limit=1)` → asc 정렬로 가장 오래된 1개 반환 → ATR/Price 비율 계산에 과거 가격 사용 | `get_latest_price()` (이미 존재, desc 정렬) 사용 | `tools.py` |
| TF-3 | tools.py | `get_factors(limit=1)` → asc 정렬로 가장 오래된 팩터 반환 → RSI/MACD 현재 상태가 3년 전 | `get_latest_factor()` 신규 함수 (desc 정렬) 사용 | `factor_repo.py`, `tools.py` |
| TF-4 | tools.py | `get_prices(limit=days)` → date 필터 없이 limit만 → 오래된 N개 반환 | `start_date`/`end_date` 필터 추가 (`today - days ~ today`) | `tools.py` |
| TF-5 | tools.py | `get_factors(limit=days)` → 동일 문제 | `start_date`/`end_date` 필터 추가 | `tools.py` |
| TF-6 | tools.py | `get_signals(limit=days)` → 동일 문제 | `start_date`/`end_date` 필터 추가 | `tools.py` |
| TF-7 | SignalPage.tsx | `fetchSignals({limit:1})` → asc 정렬로 가장 오래된 시그널 → 매트릭스에 과거 시그널 표시 | 최근 30일 fetch → 마지막 요소(최신) 사용 | `SignalPage.tsx` |

### TF-1~7: Repository order_by(asc) + limit=N 조합 버그

**증상**: 대시보드 홈 가격이 3년 전 데이터 표시. 채팅 "삼성전자 RSI 현재 상태" → 2023년 데이터 기반 분석. 시그널 매트릭스도 과거 시그널 표시.

**근본 원인**: `price_repo.get_prices()`, `factor_repo.get_factors()`, `signal_repo.get_signals()` 모두 `order_by(date.asc())` 고정. `limit=N`만 사용하면 SQL이 **가장 오래된 N개**를 반환. 시계열 차트에는 asc 정렬이 맞지만, "최신 N개" 용도에는 desc 정렬이 필요.

**영향 범위**: 전수조사 결과 7개 호출 지점에서 버그 확인. date 필터를 함께 사용하는 호출(correlation_service, spread_service, indicator_signal_service)과 desc 정렬을 사용하는 호출(get_latest_price, get_latest_signal), `.all()` 호출(signal_accuracy_service)은 정상.

**수정 전략**:
1. **최신 단일/소수 값 조회** (TF-1,2,3): desc 정렬 전용 함수 추가 (`get_latest_prices`, `get_latest_factor`)
2. **시계열 조회** (TF-4,5,6): `start_date = today - timedelta(days)`, `end_date = today` 필터 추가, limit을 5000으로 완화
3. **프론트엔드** (TF-7): 최근 30일 fetch → 마지막 요소(asc 정렬의 끝 = 최신) 사용

**검증**: 858 tests 전체 통과. E2E API 테스트로 `data_date: 2026-03-20` (최신 거래일) 반환 확인.

## Modified Files Summary

```
backend/
├── api/
│   ├── repositories/
│   │   ├── profile_repo.py                 — jsonb nested path + json 캐스트 수정
│   │   ├── price_repo.py                   — get_latest_prices(n) 추가 (TF-1)
│   │   └── factor_repo.py                  — get_latest_factor() 추가 (TF-3)
│   ├── routers/analysis.py                 — strategy_id 경로에 start_date/end_date 전달
│   ├── services/
│   │   ├── dashboard_service.py            — get_latest_prices() 사용 (TF-1)
│   │   ├── chat/
│   │   │   ├── chat_service.py             — activity tracking, 요약 트리거, user_context 파이프
│   │   │   ├── summarizer.py               — gpt-4o-mini 요약 수정
│   │   │   └── user_context.py             — 신규: UserContext 빌더
│   │   └── llm/
│   │       ├── agentic/
│   │       │   ├── classifier.py           — user_context + chat_history 파라미터 추가
│   │       │   ├── reporter.py             — user_context + chat_history + timeout 45s
│   │       │   ├── schemas.py              — unsupported 카테고리
│   │       │   └── knowledge_prompts.py    — 동적 프롬프트 + 성공률 가이드 + days 기본값 365
│   │       ├── prompts.py                  — 일반 대화 도구 없이 답변 허용
│   │       └── tools.py                    — date 필터 추가 + get_latest 사용 (TF-2~6)
│   └── tests/unit/
│       ├── test_agentic_classifier.py      — user_context 테스트 추가
│       ├── test_agentic_reporter.py        — user_context 테스트 추가
│       └── test_api/
│           ├── test_chat_service.py        — activity + 요약 테스트 추가
│           ├── test_dashboard.py           — mock 대상 get_latest_prices로 변경 (TF-1)
│           ├── test_summarizer.py          — 수정
│           └── test_user_context.py        — 신규: UserContext 테스트
frontend/
├── src/
│   ├── api/chat.ts                         — SSE 401 token refresh
│   ├── pages/SignalPage.tsx                — 매트릭스 최신 시그널 로직 수정 (TF-7)
│   ├── components/
│   │   ├── layout/Layout.tsx               — PageGuide 통합
│   │   └── onboarding/PageGuide.tsx        — 신규: 첫 방문 안내
│   └── tailwind.config.js                  — PageGuide 애니메이션
```

## Lessons Learned

1. **PostgreSQL jsonb_set nested path**: 중간 키가 없으면 nested path 생성 불가. 상위 키 보장 → 하위 키 설정 2-step 필요.
2. **json vs jsonb 타입**: `json` 컬럼에 `jsonb_set` 결과 저장 시 `::json` 캐스트 필수.
3. **SSE와 axios 인터셉터**: `fetch` API는 axios 인터셉터 범위 밖. SSE 스트리밍에서 별도 401 처리 필요.
4. **LLM 툴 데이터 소스 일관성**: 그래프 API와 LLM 툴이 동일 데이터 소스를 사용해야 함. 새 분석 함수 추가 시 LLM 툴도 업데이트 필요.
5. **try/except 무시 패턴 위험**: DB 쓰기 에러를 조용히 삼키면 API 200 OK + 데이터 미저장 → 디버깅 매우 어려움.
6. **요청 스코프 DB 세션을 백그라운드 태스크에 전달 금지**: `asyncio.ensure_future()`로 넘긴 db 세션은 요청 종료 시 닫힘. 백그라운드 태스크는 자체 `SessionLocal()` 생성 필수.
7. **Windows uvicorn --reload 신뢰성**: 간헐적 파일 변경 감지 실패. 코드 변경 후 서버 응답이 예전과 동일하면 `tasklist`로 좀비 프로세스 확인 → 전부 `taskkill` 후 재시작.
8. **Agentic 단일 턴 LLM 호출의 한계**: system+user 2개 메시지만 보내면 대화 맥락 없음. 최근 N턴을 user_msg에 포함시켜 연속성 확보 (토큰 절약 위해 요약/truncate).
9. **order_by(asc) + limit=N 함정**: 시계열 데이터 repo가 asc 정렬 고정이면, `limit=N`은 "가장 오래된 N개"를 반환. "최신 N개"가 필요한 곳에서는 반드시 (1) desc 정렬 전용 함수 사용 또는 (2) date 필터로 범위 한정. 신규 조회 함수 추가 시 "이 limit은 어느 쪽 끝에서 자르는가?" 항상 확인.
10. **전수조사 패턴**: 동일 근본 원인의 버그는 1건 수정이 아닌 전체 호출 지점 전수조사 필수. grep으로 `limit=` 패턴 전체 검색 → 안전/위험 분류 → 위험한 곳만 수정.

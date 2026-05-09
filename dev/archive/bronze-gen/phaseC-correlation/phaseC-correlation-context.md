# Phase C: 상관도 페이지 — Context
> Last Updated: 2026-03-13
> Status: In Progress (7/12)

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `backend/api/services/correlation_service.py` | 상관행렬 on-the-fly 계산 — 재활용 |
| `backend/api/repositories/price_repo.py` | 가격 조회 — 스프레드 서비스에서 사용 |
| `backend/api/services/llm/tools.py` | 현재 5개 Tool — 2개 추가 |
| `backend/api/services/llm/graph.py` | StateGraph — 하이브리드 분류기 삽입 지점 |
| `backend/api/services/llm/prompts.py` | 시스템 프롬프트 — Tool 설명 추가 |
| `backend/api/services/chat/chat_service.py` | SSE 오케스트레이션 — page_context + ui_action |
| `frontend/src/hooks/useSSE.ts` | SSE 파싱 — onUIAction 콜백 추가 |
| `frontend/src/types/chat.ts` | SSEEvent 타입 — ui_action 추가 |
| `frontend/src/api/chat.ts` | sendMessageSSE — pageContext 파라미터 |
| `frontend/src/store/chatStore.ts` | 채팅 상태 — 참고용 |
| `frontend/src/pages/CorrelationPage.tsx` | 상관 히트맵 — 확장 대상 |
| `frontend/src/components/chat/ChatPanel.tsx` | 채팅 패널 — 넛지 질문 + 컨텍스트 전송 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
- `correlation_service.compute_correlation(db, asset_ids, start, end)` → 상관행렬 dict
- `price_repo.get_prices(db, asset_id, start, end)` → List[PriceDaily]

### 출력 (어디에 쓰는가)
- LangGraph Tool JSON 응답 → SSE text_delta
- SSE `ui_action` 이벤트 → Frontend chartActionStore
- 분석 결과는 DB 저장 없음 (on-the-fly)

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| 하이브리드 분류기 = 정규표현식+키워드 | LLM intent 불필요 → 레이턴시 최소화 |
| 분류 실패 → LLM fallback | 커버리지 보장 |
| Union-Find 그룹핑 | 7자산 소규모 → 단순 알고리즘 적합 |
| 스프레드 = 정규화 가격 비율 | log 수익률보다 직관적 |
| z-score 밴드 ±2σ | 통계적 표준 기준 |
| ui_action 선택적 처리 | 프론트 무시해도 텍스트만으로 동작 |
| 넛지 질문 페이지별 하드코딩 | LLM 생성 불필요, 일관성 |

## Changed Files (Step C.7)
- `backend/api/schemas/chat.py` — `PageContextRequest` 스키마 추가, `SendMessageRequest`에 `page_context` 필드
- `backend/api/routers/chat.py` — `page_context` → `chat_service.stream_chat()` 전달
- `backend/api/services/chat/chat_service.py` — 하이브리드 분류기 통합 (`classify_question` → `_fetch_hybrid_data` → 템플릿 응답 / LangGraph fallback), `ui_action` SSE 이벤트, `_chunk_text` 헬퍼
- `backend/api/services/llm/graph.py` — `_build_system_prompt()` (page_context 반영), `agent_node`에서 page_context 읽기
- `backend/tests/unit/test_hybrid_integration.py` — 신규 (16 tests: 하이브리드 경로, fallback, 라우터 page_context 전달)

## 4. 컨벤션 체크리스트

### 데이터 관련
- [ ] 상관행렬 on-the-fly 계산 (DB 저장 없음)
- [ ] 스프레드 on-the-fly 계산 (DB 저장 없음)
- [ ] NaN/None 안전 처리

### API/Backend 관련
- [ ] 분석 서비스: 순수 함수 위주 (DB 접근 최소화)
- [ ] Tool: JSON 직렬화 가능한 응답
- [ ] 하이브리드: `hybrid/` 디렉토리 모듈 분리
- [ ] SSE: ui_action 이벤트 포맷 규약

### Frontend 관련
- [ ] Zustand store: chartActionStore, watchlistStore
- [ ] Recharts: ScatterChart, LineChart 활용
- [ ] localStorage: 관심 종목 영속 저장
- [ ] TypeScript strict 준수

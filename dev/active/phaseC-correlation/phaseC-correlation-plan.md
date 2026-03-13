# Phase C: 상관도 페이지 완성
> Last Updated: 2026-03-13
> Status: Planning

## 1. Summary (개요)

**목적**: 상관도 페이지를 백엔드 분석 서비스 + 하이브리드 응답 기반 + 프론트 확장까지 완결
**범위**: 상관도 그룹핑/유사자산, 스프레드 분석, 해석 규칙, LangGraph Tool 2개, 하이브리드 응답 시스템, 프론트 차트/UI 확장, 관심 종목
**예상 결과물**: 신규 ~13 / 수정 ~9 / Migration 0

## 2. Current State (현재 상태)

- Phase B 완료: LangGraph + OpenAI GPT-5 챗봇 (5개 Tool: prices, factors, signals, correlation, backtest)
- 상관도 페이지: 히트맵만 표시 (기간/윈도우 조절)
- 챗봇: raw data 조회만 가능, 분석/해석 없음
- SSE 이벤트: text_delta, tool_call, tool_result, done (ui_action 미구현)

## 3. Target State (목표 상태)

- 상관도 분석: 그룹핑(Union-Find), 유사자산 추천, top pairs
- 스프레드 분석: 정규화 가격 비율 스프레드 + z-score 수렴/발산 감지
- 해석 규칙: 상관도(0.8~1.0=매우 강한…), z-score 해석
- LangGraph Tool: `analyze_correlation`, `get_spread` (5→7개)
- 하이브리드 응답: 정규표현식 분류기 → 템플릿 응답 (실패 시 LLM fallback)
- 프론트: ScatterPlot, SpreadChart, CorrelationGroupCard, NudgeQuestions, WatchlistToggle
- SSE: `ui_action` 이벤트 추가 → chartActionStore 연동

## 4. Implementation Stages

### Stage A: Backend 분석 서비스 (C.1~C.3)
1. **C.1** 상관도 분석 서비스 — `correlation_analysis.py`
   - `find_correlation_groups(matrix, asset_ids, threshold)` — Union-Find 알고리즘
   - `find_top_pairs(matrix, asset_ids, n)` — 상관도 높은 쌍
   - `recommend_similar(matrix, asset_ids, target_id, n)` — 유사자산 추천
   - 재활용: `correlation_service.compute_correlation()`
   - 테스트: `test_correlation_analysis.py`

2. **C.2** 스프레드 분석 서비스 — `spread_service.py`
   - `compute_spread(db, asset_a, asset_b, start, end)` → `SpreadResult`
   - SpreadResult: dates, spread_values, z_score, mean, std, convergence_events
   - 정규화 가격 비율 기반 스프레드 + z-score 수렴/발산 감지
   - 재활용: `price_repo.get_prices()`
   - 테스트: `test_spread_service.py`

3. **C.3** 해석 규칙 상수 — `interpretation_rules.py`
   - 상관도 해석: 0.8~1.0=매우 강한 양, 0.5~0.8=중간 양, ...
   - 스프레드 z-score 해석: |z|>2=극단, 1~2=주의, <1=정상
   - `interpret_correlation(value)`, `interpret_spread_zscore(zscore)`
   - 테스트: 경계값 해석 검증

### Stage B: LangGraph Tool 확장 (C.4~C.5)
4. **C.4** Tool — `analyze_correlation`
   - `analyze_correlation(asset_ids, days, threshold)` → 그룹핑+유사자산+해석 JSON
   - `tools.py` 수정, `prompts.py` Tool 설명 추가

5. **C.5** Tool — `get_spread`
   - `get_spread(asset_a, asset_b, days)` → 스프레드 시계열+z-score JSON
   - `tools.py` 수정

### Stage C: 하이브리드 응답 기반 (C.6~C.7)
6. **C.6** 하이브리드 응답 기반 구축
   - `hybrid/context.py` — `PageContext` 데이터클래스
   - `hybrid/classifier.py` — `classify_question(question, page_context) → Category|None`
   - `hybrid/templates.py` — 카테고리별 응답 템플릿 + `get_nudge_questions(page_id)`
   - `hybrid/actions.py` — `UIAction` 타입 (navigate/update_chart/set_filter)
   - 상관도용 카테고리: correlation_explain, similar_assets, spread_analysis
   - 테스트: `test_hybrid_classifier.py`

7. **C.7** 하이브리드를 LangGraph에 통합
   - `graph.py` 수정: agent_node에 분류기 삽입
   - `chat_service.py` 수정: `stream_chat()`에 page_context + SSE `ui_action`

### Stage D: Frontend 확장 (C.8~C.11)
8. **C.8** SSE 확장 + chartActionStore
   - `types/chat.ts` — SSEEvent에 `ui_action` 타입
   - `hooks/useSSE.ts` — `onUIAction` 콜백
   - `store/chartActionStore.ts` 신규 (Zustand)
   - `components/chat/ChatPanel.tsx` — 페이지 컨텍스트 전송
   - `api/chat.ts` — `sendMessageSSE`에 pageContext 추가

9. **C.9** 상관도 페이지 확장
   - `charts/ScatterPlotChart.tsx` 신규 (Recharts ScatterChart)
   - `correlation/CorrelationGroupCard.tsx` 신규
   - `pages/CorrelationPage.tsx` 수정 — 히트맵 아래 그룹핑 카드 + ScatterPlot

10. **C.10** SpreadChart + 넛지 질문
    - `charts/SpreadChart.tsx` 신규 (LineChart + z-score 밴드)
    - `chat/NudgeQuestions.tsx` 신규
    - `pages/CorrelationPage.tsx` 수정 — 선택 쌍의 SpreadChart
    - `components/chat/ChatPanel.tsx` 수정 — 넛지 질문 영역

11. **C.11** 관심 종목 설정
    - `store/watchlistStore.ts` 신규 (Zustand + localStorage)
    - `common/WatchlistToggle.tsx` 신규
    - `pages/CorrelationPage.tsx` 수정 — 관심 종목 필터

### Stage E: 통합 검증 (C.12)
12. **C.12** Phase C 통합 검증
    - Backend: `pytest` 전체 통과 + `ruff check` clean
    - Frontend: `tsc --noEmit` 0 errors + `vite build` 성공
    - 브라우저 E2E: 상관도 페이지 렌더링, 그룹핑 카드, ScatterPlot, SpreadChart, 넛지 질문, 관심 종목 토글 동작 확인
    - 챗봇: 상관도 관련 질문 → 하이브리드 응답 + Tool 호출 정상 동작
    - Railway/Vercel 배포 확인 (선택)

## 5. Task Breakdown

| # | Task | Size | 의존성 |
|---|------|------|--------|
| C.1 | 상관도 분석 서비스 | M | - |
| C.2 | 스프레드 분석 서비스 | M | - |
| C.3 | 해석 규칙 상수 | S | - |
| C.4 | Tool: analyze_correlation | M | C.1, C.3 |
| C.5 | Tool: get_spread | M | C.2, C.3 |
| C.6 | 하이브리드 응답 기반 | L | C.3 |
| C.7 | 하이브리드 LangGraph 통합 | L | C.6, C.4, C.5 |
| C.8 | SSE 확장 + chartActionStore | M | C.7 |
| C.9 | 상관도 페이지 확장 | M | C.8 |
| C.10 | SpreadChart + 넛지 질문 | M | C.8 |
| C.11 | 관심 종목 설정 | S | - |
| C.12 | Phase C 통합 검증 | M | C.1~C.11 전체 |

## 6. Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| Union-Find 7자산이므로 과잉 설계 | 단순 구현 + threshold 파라미터로 유연성 |
| 하이브리드 분류기 정규표현식 한계 | 실패 시 LangGraph LLM fallback 보장 |
| chartActionStore → 페이지 동기화 지연 | 프론트 무시해도 텍스트 응답만으로 동작 |

## 7. Dependencies

**내부**:
- `correlation_service.compute_correlation()` — 상관행렬 계산
- `price_repo.get_prices()` — 가격 조회
- `llm/graph.py`, `llm/tools.py` — LangGraph 기반

**외부 (신규 없음)**: 기존 패키지로 충분

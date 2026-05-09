# Phase F: Full Agentic Flow
> Last Updated: 2026-03-22
> Status: Complete (+ 성능 최적화 Post-Phase 완료)

## 1. Summary (개요)

**목적**: 현재 챗봇의 regex 분류기 + 하드코딩 템플릿 구조를 **2-Step LLM Structured Output** (Classifier + Reporter)으로 교체하고, **자동 페이지 네비게이션**을 구현하여 진정한 Agentic AI UX를 제공한다.

**범위**:
- LLM 기반 질문 분류기 (regex 대체)
- LLM 기반 큐레이팅 리포터 (템플릿 대체)
- 자동 페이지 네비게이션 (즉시 이동)
- Knowledge Expert 프롬프트 4종 (페이지별 전문 분석)
- 동적 follow-up 질문 생성
- 기존 LangGraph를 general fallback으로 유지

**예상 결과물**:
- `backend/api/services/llm/agentic/` 패키지 (5개 모듈)
- `chat_service.py` agentic flow 통합
- 프론트엔드 navigate 핸들러 + follow-up 질문 UI
- 레거시 hybrid classifier/template 정리

## 2. Current State (현재 상태)

### 챗봇 아키텍처 (Phase B~E 누적)
```
메시지 도착
  ├─ is_nudge=true → regex classifier → 9개 카테고리 → 하드코딩 f-string 템플릿 → SSE
  │                   (실패 시 페이지 기본 카테고리 적용)
  │
  └─ is_nudge=false → 바로 LangGraph fallback → agent+9개tool → SSE
```

**문제점**:
1. 넛지 질문만 구조화된 응답, 자유 질문은 비구조적
2. regex classifier 확장 어려움 (새 패턴마다 수동 추가)
3. 페이지 간 라우팅 없음 (prices에서 상관 질문해도 이동 안 함)
4. 템플릿 응답이 f-string 하드코딩이라 자연스러운 분석 불가
5. `is_nudge` 분기로 두 트랙이 완전 분리되어 일관성 부족

### 기존 자산
- **9개 LangChain Tool**: get_prices, get_factors, get_correlation, get_signals, list_backtests, analyze_correlation_tool, get_spread, analyze_indicators, backtest_strategy
- **UIAction 시스템**: navigate, highlight_pair, set_filter, update_chart (백엔드 정의 완료, SSE 전송 완료)
- **프론트엔드 SSE 파싱**: ui_action 이벤트 처리 (navigate만 핸들러 미구현)
- **chartActionStore**: 액션 큐 시스템 (Zustand)
- **LangGraph**: StateGraph (agent→tools→agent), MemorySaver checkpointer

### 테스트 현황
- Backend: 740 passed, ruff clean
- Frontend: tsc 0 errors, vite build 성공

## 3. Target State (목표 상태)

### 새 아키텍처
```
메시지 도착
  → Step 1: LLM Classifier (gpt-5-mini, Structured Output)
      → ClassificationResult {target_page, should_navigate, category, required_tools, asset_ids, params, confidence}
  → confidence < 0.5 OR category == "general":
      → 기존 LangGraph fallback (graph.py 변경 없음)
  → else:
      → should_navigate이면: "페이지를 이동합니다" + navigate() UI action
      → Step 2: DataFetcher — required_tools 프로그래밍적 호출 (기존 9개 tool 재사용)
      → Step 3: LLM Reporter (gpt-5/gpt-5-mini, Structured Output)
          → CuratedReport {summary, analysis, verdict, ui_actions, follow_up_questions}
      → SSE 스트리밍: text_delta + ui_actions + follow_up
```

### 핵심 변화
| 항목 | Before (Phase E) | After (Phase F) |
|------|-------------------|-----------------|
| 질문 분류 | regex 패턴 매칭 | LLM Structured Output |
| 응답 생성 | f-string 템플릿 | LLM 큐레이팅 리포트 |
| 페이지 이동 | 없음 | 자동 네비게이션 (즉시) |
| 후속 질문 | 정적 넛지 질문 | 동적 follow-up 생성 |
| is_nudge 분기 | 있음 (두 트랙) | 없음 (단일 agentic flow) |
| LLM 호출 횟수 | 0회(넛지) or N회(LangGraph) | 2회 고정 (Classifier+Reporter) |

## 4. Implementation Stages

### Stage A: 기반 정의 (F.1~F.2)
Pydantic 스키마 + Knowledge Expert 프롬프트 정의. 의존성 없이 독립 진행.

### Stage B: 핵심 모듈 구현 (F.3~F.5)
LLM Classifier, DataFetcher, LLM Reporter 3개 모듈. Stage A 완료 후 병렬 진행 가능.

### Stage C: 백엔드 통합 (F.6)
chat_service.py에 agentic flow 통합. Stage B 전체 완료 후 진행. 이 Phase의 핵심 리팩토링.

### Stage D: 프론트엔드 확장 (F.7~F.8)
follow-up 질문 UI + navigate 핸들러. Stage C 완료 후 병렬 진행 가능.

### Stage E: 정리 + 검증 (F.9~F.10)
레거시 코드 정리 + 전체 통합 검증.

## 5. Task Breakdown

| Task | 설명 | Size | 의존성 | Stage |
|------|------|------|--------|-------|
| F.1 | Pydantic 스키마 정의 (ClassificationResult, CuratedReport, UIActionModel) | S | 없음 | A |
| F.2 | Knowledge Expert Prompts (Classifier + 4개 페이지 전문가) | S | 없음 | A |
| F.3 | LLM Classifier (Structured Output, gpt-5-mini) | M | F.1, F.2 | B |
| F.4 | DataFetcher (tool 프로그래밍적 호출, 동적 매핑) | M | F.1 | B |
| F.5 | LLM Reporter (Structured Output, knowledge prompt) | M | F.1, F.2 | B |
| F.6 | chat_service.py 통합 (agentic flow 전환) | L | F.3, F.4, F.5 | C |
| F.7 | follow_up SSE 이벤트 + 프론트엔드 UI | S | F.6 | D |
| F.8 | 프론트엔드 navigate 핸들러 (즉시 이동) | S | F.6 | D |
| F.9 | 레거시 코드 정리 (regex classifier, templates) | S | F.6~F.8 | E |
| F.10 | 통합 검증 (pytest + tsc + vite + E2E) | M | F.1~F.9 | E |

**Total**: 10 tasks (S:5, M:4, L:1)

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM Classifier 분류 정확도 부족 | 잘못된 카테고리/페이지 | 중 | confidence threshold + LangGraph fallback |
| Reporter가 잘못된 UIAction 생성 | 무효 navigate/highlight | 중 | UIActionModel Literal 타입 제한 + Pydantic 검증 |
| Structured Output 파싱 실패 | 응답 불가 | 저 | try/except → LangGraph fallback |
| LLM 2회 호출 레이턴시 | UX 저하 | 중 | **해결됨**: Reporter를 gpt-4.1-mini(non-reasoning)로 분리 → E2E cold ~26s, warm ~15s |
| 기존 테스트 깨짐 | CI 실패 | 중 | hybrid 코드 즉시 삭제 안 함, 단계적 정리 |
| is_nudge 하위호환 | 프론트/백 배포 시점 불일치 | 저 | 파라미터 유지하되 내부에서 무시 |

## 7. Dependencies

### 내부 (기존 모듈 재사용)
- `api/services/llm/tools.py` — 9개 LangChain Tool (수정 없음)
- `api/services/llm/hybrid/actions.py` — UIAction dataclass (수정 없음)
- `api/services/llm/graph.py` — LangGraph StateGraph (수정 없음, fallback 용)
- `api/services/llm/prompts.py` — 기존 시스템 프롬프트 (참조용)
- `api/repositories/asset_repo.py` — 종목명 매핑 (DataFetcher에서 사용)

### 외부
- **OpenAI API**: Structured Output (`response_format` with JSON Schema)
- **langchain-openai**: `ChatOpenAI.with_structured_output()` — Pydantic 모델 직접 전달
- **Pydantic v2**: 스키마 정의 + JSON Schema 자동 생성

### 신규 패키지: 없음 (기존 의존성으로 충분)

## 8. Post-Phase: 성능 최적화 (2026-03-22)

### 8.1 Reporter 모델 분리
**근본 원인**: gpt-5-mini/nano가 reasoning 모델 → `temperature=0` 400 에러 → langchain 자동 재시도로 25s+
**해결**: Reporter 모델을 `gpt-4.1-mini` (non-reasoning)로 분리. `llm_report_model` 설정 추가.
**결과**: Reporter 34.8s → 5.8s (6배), E2E warm ~15s (목표 달성). 커밋 `ec2995b`.

### 8.2 Cache Warmup (Cold 최적화)
**문제**: DataFetcher cold 12s — 첫 요청 시 DB 쿼리 + 계산 비용.
**해결**: 서버 시작 시 백그라운드로 주요 tool 결과 프리페치 (`cache_warmup.py`).
- 7개 자산 × 4개 tool (`get_prices`, `get_factors`, `get_signals`, `analyze_indicators`) + `get_correlation` = 29개 호출
- FastAPI lifespan hook으로 비동기 실행 (서버 시작 블로킹 없음)
- 17초 소요, 29/29 성공
**결과**: Cold 12s → ~1.3s (캐시 히트), E2E cold ~26s → ~15s (warm과 동일 수준).
